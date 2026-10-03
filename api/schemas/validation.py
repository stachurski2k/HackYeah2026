from pydantic import BaseModel, Field

from .common import ORMModel


class ValidationToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ValidationToolRead(ORMModel):
    id: int
    name: str
