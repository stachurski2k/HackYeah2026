from pydantic import BaseModel, Field

from api.db.models import PermissionCode

from .common import ORMModel


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class GroupRead(ORMModel):
    id: int
    name: str


class PermissionRead(ORMModel):
    id: int
    code: PermissionCode


class PolicyCreate(BaseModel):
    group: str
    permission: PermissionCode
