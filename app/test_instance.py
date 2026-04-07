from fastapi import FastAPI
from fastapi.exceptions import HTTPException

app = FastAPI()

is_disabled = False

@app.get('/ping')
async def ping():
    if is_disabled:
        raise HTTPException(status_code=500)
    return {"pong": "pong"}


@app.get('/switch')
async def switch():
    global is_disabled
    is_disabled = not is_disabled
    return {
        'message': 'switched'
    }
