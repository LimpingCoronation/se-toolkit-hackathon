from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import DEV_MODE, logger, redis_manager, connection_manager
from core.utils import verify_token
from routers.users import router as user_router
from routers.monitor import router as monitor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is launched")
    # startup
    await redis_manager.subscribe('main')
    asyncio.create_task(redis_manager.listener())

    logger.info("Server started")
    yield
    # shutdown


app = FastAPI(lifespan=lifespan)
app.include_router(user_router)
app.include_router(monitor_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.websocket('/monitor')
async def websocket_handler(websocket: WebSocket):
    token = websocket.headers.get('sec-websocket-protocol')
    if not token:
        raise HTTPException(403, "Token isn't specified")
    
    token = token.split(' ')[-1]
    data = verify_token(token)
    if not data:
        raise HTTPException(403, "Token is wrong")
    
    await websocket.accept(subprotocol=token)
    connection_manager.connect(data['id'], websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        print("Disconnected")


@app.get("/root")
def root():
    return {"message": f"DEV_MODE is {DEV_MODE}"}
