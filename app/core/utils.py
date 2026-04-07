import hashlib
from datetime import datetime, timedelta

import jwt

from .config import settings


def get_token(id: int, username: str):
    now = datetime.now()
    expire_time = now + timedelta(days=1)

    return jwt.encode({
        "id": id,
        "username": username,
        "cr": now.timestamp(),
        "exp": expire_time.timestamp()
    }, key=settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str):
    try:
        return jwt.decode(token, key=settings.SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        print(e)
        return None


def hash_password(password: str):
    h = hashlib.sha256()
    h.update(password.encode())
    return h.hexdigest()


def verify_password(password: str, hash: str):
    h = hash_password(password)
    return h == hash
