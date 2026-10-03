from decimal import Decimal

from pydantic import BaseModel, Field

from .common import ORMModel


class BudgetCreate(BaseModel):
    budget: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class BudgetRead(ORMModel):
    id: int
    user_id: int
    budget: Decimal
