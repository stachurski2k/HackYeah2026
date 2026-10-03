from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import config

from . import models


def seed_reference_data(db: Session) -> None:
    for name in config.get("defaults.groups", ["admin", "office", "user"]):
        if not db.scalar(select(models.Group).where(models.Group.name == name)):
            db.add(models.Group(name=name))
    for permission in models.PermissionCode:
        if not db.scalar(
            select(models.Permission).where(models.Permission.code == permission.value)
        ):
            db.add(models.Permission(code=permission.value))
    db.commit()
