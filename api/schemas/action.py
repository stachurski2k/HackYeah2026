from pydantic import BaseModel, Field

from .common import ORMModel


class ActionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1)
    action_name: str = Field(min_length=1, max_length=100)


class ActionUpdate(BaseModel):
    prompt: str | None = Field(default=None, min_length=1)
    action_name: str | None = Field(default=None, min_length=1, max_length=100)


class ActionRead(ORMModel):
    id: int
    name: str
    prompt: str
    action_name: str
