from datetime import datetime

from pydantic import BaseModel, Field

from .common import ORMModel


class TokenRead(ORMModel):
    id: int
    token: str
    created_at: datetime


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    token: str | None = None
    groups: list[str] = Field(default_factory=lambda: ["user"])


class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    groups: list[str] | None = None


class UserRead(BaseModel):
    id: int
    name: str
    token: str
    groups: list[str]
