from fastapi.routing import APIRouter
from fastapi import Depends, Request
from sqlalchemy import select
from fastapi.exceptions import HTTPException

from core.database.setup_db import session_getter
from models.user import User
from schemas.users import UserCreate
from core.utils import hash_password, verify_password, get_token, verify_token

router = APIRouter(prefix="/users")


async def get_user(request: Request, session = Depends(session_getter)):
    token = request.headers.get("authorization")
    if not token:
        raise HTTPException(status_code=403, detail="not_authorized")
    
    token = token.split(' ')
    if len(token) != 2:
        raise HTTPException(status_code=403, detail="wrong_token")
    
    token = verify_token(token[-1])
    if token is not None:
        id = token["id"]
        user = (await session.execute(select(User).where(User.id == id))).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=403, detail="user_doesnt_exist")
        return user
    
    raise HTTPException(status_code=403, detail="wrong_token")


@router.post("/sign-up/")
async def sign_up(body: UserCreate, session = Depends(session_getter)):
    password = hash_password(body.password)
    user = User(username=body.username, hash_password=password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/sign-in/")
async def sign_in(body: UserCreate, session = Depends(session_getter)):
    stmt = select(User).where(User.username == body.username)
    user: User = (await session.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=403, detail="wrong_username_or_password")
    
    if verify_password(body.password, user.hash_password):
        token = get_token(user.id, user.username)
        return {"token": token}
    else:
        raise HTTPException(status_code=403, detail="wrong_username_or_password")


@router.get("/profile/")
async def profile(user: User = Depends(get_user)):
    return {
        "id": user.id,
        "username": user.username
    }
