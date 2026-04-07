from sqlmodel import SQLModel, Field


class Service(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    url: str
    is_alive: bool = Field(default=False)
    is_working: bool = Field(default=False)
    user_id: int = Field(default=None, foreign_key="user.id")
