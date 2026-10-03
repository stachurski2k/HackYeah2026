import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app.config import config
from app.db import get_db, models

router = APIRouter(tags=["database"])


def commit(db: Session, detail: str = "Record already exists") -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def group_by_name(db: Session, name: str) -> models.Group:
    group = db.scalar(select(models.Group).where(models.Group.name == name))
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group '{name}' not found")
    return group


def permission_by_code(db: Session, code: models.PermissionCode) -> models.Permission:
    permission = db.scalar(select(models.Permission).where(models.Permission.code == code.value))
    if permission is None:  # protects against a manually damaged reference table
        raise HTTPException(status_code=500, detail="Permission dictionary is incomplete")
    return permission


def user_view(db: Session, user: models.User) -> schemas.UserRead:
    token = db.get(models.AccessToken, user.token_id)
    groups = db.scalars(
        select(models.Group.name)
        .join(models.UserGroup, models.UserGroup.group_id == models.Group.id)
        .where(models.UserGroup.user_id == user.id)
    ).all()
    return schemas.UserRead(id=user.id, name=user.name, token=token.token, groups=list(groups))  # type: ignore[union-attr]


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/tokens", response_model=schemas.TokenRead, status_code=status.HTTP_201_CREATED)
async def generate_token(db: Session = Depends(get_db)) -> models.AccessToken:
    token = models.AccessToken(token=secrets.token_urlsafe(config["security"]["token_bytes"]))
    db.add(token)
    commit(db)
    db.refresh(token)
    return token


@router.post("/users", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.UserRead:
    if data.token:
        access_token = db.scalar(
            select(models.AccessToken).where(models.AccessToken.token == data.token)
        )
        if access_token is None:
            raise HTTPException(status_code=404, detail="Token not found")
        if db.scalar(select(models.User).where(models.User.token_id == access_token.id)):
            raise HTTPException(status_code=409, detail="Token is already assigned")
    else:
        access_token = models.AccessToken(
            token=secrets.token_urlsafe(config["security"]["token_bytes"])
        )
        db.add(access_token)
        db.flush()

    groups = [group_by_name(db, name) for name in set(data.groups)]
    user = models.User(name=data.name, token_id=access_token.id)
    db.add(user)
    db.flush()
    db.add_all(models.UserGroup(user_id=user.id, group_id=group.id) for group in groups)
    commit(db)
    return user_view(db, user)


@router.get("/users", response_model=list[schemas.UserRead])
async def list_users(db: Session = Depends(get_db)) -> list[schemas.UserRead]:
    return [user_view(db, user) for user in db.scalars(select(models.User)).all()]


@router.patch("/users/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int, data: schemas.UserUpdate, db: Session = Depends(get_db)
) -> schemas.UserRead:
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = data.name
    if data.groups is not None:
        groups = [group_by_name(db, name) for name in set(data.groups)]
        db.execute(delete(models.UserGroup).where(models.UserGroup.user_id == user.id))
        db.add_all(models.UserGroup(user_id=user.id, group_id=group.id) for group in groups)
    commit(db)
    return user_view(db, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)) -> Response:
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return Response(status_code=204)


@router.get("/groups", response_model=list[schemas.GroupRead])
async def list_groups(db: Session = Depends(get_db)) -> list[models.Group]:
    return list(db.scalars(select(models.Group)).all())


@router.post("/groups", response_model=schemas.GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(data: schemas.GroupCreate, db: Session = Depends(get_db)) -> models.Group:
    group = models.Group(name=data.name)
    db.add(group)
    commit(db, "Group already exists")
    db.refresh(group)
    return group


@router.get("/permissions", response_model=list[schemas.PermissionRead])
async def list_permissions(db: Session = Depends(get_db)) -> list[models.Permission]:
    return list(db.scalars(select(models.Permission)).all())


@router.post("/models", response_model=schemas.ModelRead, status_code=status.HTTP_201_CREATED)
async def register_model(
    data: schemas.ModelCreate, db: Session = Depends(get_db)
) -> models.RegisteredModel:
    item = models.RegisteredModel(name=data.name, api_url=str(data.api_url))
    db.add(item)
    commit(db, "Model already exists")
    db.refresh(item)
    return item


@router.get("/models", response_model=list[schemas.ModelRead])
async def list_models(db: Session = Depends(get_db)) -> list[models.RegisteredModel]:
    return list(db.scalars(select(models.RegisteredModel)).all())


@router.patch("/models/{model_id}", response_model=schemas.ModelRead)
async def update_model(
    model_id: int, data: schemas.ModelUpdate, db: Session = Depends(get_db)
) -> models.RegisteredModel:
    item = db.get(models.RegisteredModel, model_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Model not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, str(value) if key == "api_url" else value)
    commit(db, "Model name already exists")
    return item


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: int, db: Session = Depends(get_db)) -> Response:
    item = db.get(models.RegisteredModel, model_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.put("/models/{model_id}/policies", status_code=status.HTTP_204_NO_CONTENT)
async def set_model_policy(
    model_id: int, data: schemas.PolicyCreate, db: Session = Depends(get_db)
) -> Response:
    if db.get(models.RegisteredModel, model_id) is None:
        raise HTTPException(status_code=404, detail="Model not found")
    group = group_by_name(db, data.group)
    permission = permission_by_code(db, data.permission)
    policy = db.scalar(
        select(models.ModelGroup).where(
            models.ModelGroup.model_id == model_id, models.ModelGroup.group_id == group.id
        )
    )
    if policy:
        policy.permission_id = permission.id
    else:
        db.add(models.ModelGroup(model_id=model_id, group_id=group.id, permission_id=permission.id))
    db.commit()
    return Response(status_code=204)


@router.post("/actions", response_model=schemas.ActionRead, status_code=status.HTTP_201_CREATED)
async def create_action(data: schemas.ActionCreate, db: Session = Depends(get_db)) -> models.Action:
    item = models.Action(**data.model_dump())
    db.add(item)
    commit(db, "Action already exists")
    db.refresh(item)
    return item


@router.get("/actions", response_model=list[schemas.ActionRead])
async def list_actions(db: Session = Depends(get_db)) -> list[models.Action]:
    return list(db.scalars(select(models.Action)).all())


@router.patch("/actions/{action_id}", response_model=schemas.ActionRead)
async def update_action(
    action_id: int, data: schemas.ActionUpdate, db: Session = Depends(get_db)
) -> models.Action:
    item = db.get(models.Action, action_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Action not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    return item


@router.delete("/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(action_id: int, db: Session = Depends(get_db)) -> Response:
    item = db.get(models.Action, action_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Action not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.put("/actions/{action_id}/policies", status_code=status.HTTP_204_NO_CONTENT)
async def set_action_policy(
    action_id: int, data: schemas.PolicyCreate, db: Session = Depends(get_db)
) -> Response:
    if db.get(models.Action, action_id) is None:
        raise HTTPException(status_code=404, detail="Action not found")
    group = group_by_name(db, data.group)
    permission = permission_by_code(db, data.permission)
    policy = db.scalar(
        select(models.ActionGroupPermission).where(
            models.ActionGroupPermission.action_id == action_id,
            models.ActionGroupPermission.group_id == group.id,
        )
    )
    if policy:
        policy.permission_id = permission.id
    else:
        db.add(
            models.ActionGroupPermission(
                action_id=action_id, group_id=group.id, permission_id=permission.id
            )
        )
    db.commit()
    return Response(status_code=204)


@router.put("/budgets/{user_id}", response_model=schemas.BudgetRead)
async def set_budget(
    user_id: int, data: schemas.BudgetCreate, db: Session = Depends(get_db)
) -> models.BudgetLimit:
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    item = db.scalar(select(models.BudgetLimit).where(models.BudgetLimit.user_id == user_id))
    if item:
        item.budget = data.budget
    else:
        item = models.BudgetLimit(user_id=user_id, budget=data.budget)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post(
    "/validation-tools",
    response_model=schemas.ValidationToolRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_validation_tool(
    data: schemas.ValidationToolCreate, db: Session = Depends(get_db)
) -> models.ValidationTool:
    item = models.ValidationTool(name=data.name)
    db.add(item)
    commit(db, "Validation tool already exists")
    db.refresh(item)
    return item


@router.get("/validation-tools", response_model=list[schemas.ValidationToolRead])
async def list_validation_tools(db: Session = Depends(get_db)) -> list[models.ValidationTool]:
    return list(db.scalars(select(models.ValidationTool)).all())
