from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    url: str = Field(min_length=10)

