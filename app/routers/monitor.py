import json

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select, delete

from core.config import redis_manager
from core.database.setup_db import session_getter
from routers.users import get_user
from schemas.services import ServiceCreate
from models.user import User
from models.service import Service

router = APIRouter(prefix="/services")


@router.post("/add", response_model=Service)
async def add_server(
    body: ServiceCreate,
    user: User = Depends(get_user),
    session = Depends(session_getter)
):
    service = Service(url=body.url, user_id=user.id)
    session.add(service)
    await session.commit()
    await session.refresh(service)

    return service


@router.post("/monitor/{id}", response_model=Service)
async def start_monitoring(
    id: int,
    user: User = Depends(get_user),
    session = Depends(session_getter)
):
    stmt = select(Service).where(Service.id == id)
    service: Service = (await session.execute(stmt)).scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=400, detail="no_such_service")
    
    if not service.is_working:
        service.is_working = True
        await session.commit()
        await session.refresh(service)

        data = json.dumps({
            "type": "start_translation",
            "service_id": service.id,
            "user_id": user.id,
            "url": service.url
        })

        await redis_manager.send_message("main", data)


    return service


@router.post("/stop_monitor/{id}")
async def start_monitoring(
    id: int,
    user: User = Depends(get_user),
    session = Depends(session_getter)
):
    stmt = select(Service).where(Service.id == id)
    service: Service = (await session.execute(stmt)).scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=400, detail="no_such_service")

    service.is_working = False
    await session.commit()
    await session.refresh(service)

    data = json.dumps({
        "type": "stop_translation",
        "user_id": user.id,
        "service_id": service.id
    })

    await redis_manager.send_message("main", data)

    return service


@router.get("/list/", response_model=list[Service])
async def list_services(
    user: User = Depends(get_user),
    session = Depends(session_getter)
):
    stmt = select(Service).where(Service.user_id == user.id)
    services = (await session.execute(stmt)).scalars()
    return services


@router.delete("/remove/{id}")
async def remove_service(
    id: int,
    session = Depends(session_getter)
):
    await session.execute(delete(Service).where(Service.id == id))
    await session.commit()

    return {
        "message": "removed"
    }
