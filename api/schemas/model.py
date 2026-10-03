from pydantic import BaseModel, Field, HttpUrl

from .common import ORMModel


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    api_url: HttpUrl


class ModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    api_url: HttpUrl | None = None


class ModelRead(ORMModel):
    id: int
    name: str
    api_url: str
