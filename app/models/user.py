from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


def get_utc_now():
    return datetime.now()


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hash_password: str
    created_at: datetime = Field(default_factory=get_utc_now)

