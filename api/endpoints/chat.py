from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db import get_db, models
from api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    _: ChatRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> ChatResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    raw_token = authorization.removeprefix("Bearer ").strip()
    token = db.scalar(select(models.AccessToken).where(models.AccessToken.token == raw_token))
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.scalar(select(models.User).where(models.User.token_id == token.id))
    return ChatResponse(
        authenticated=True,
        user_id=user.id if user else None,
        next_stage="authorization",
    )
