from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .db.models import PermissionCode


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class GroupRead(ORMModel):
    id: int
    name: str


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


class PermissionRead(ORMModel):
    id: int
    code: PermissionCode


class PolicyCreate(BaseModel):
    group: str
    permission: PermissionCode


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


class BudgetCreate(BaseModel):
    budget: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class BudgetRead(ORMModel):
    id: int
    user_id: int
    budget: Decimal


class ValidationToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ValidationToolRead(ORMModel):
    id: int
    name: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    authenticated: bool
    user_id: int | None
    next_stage: str
