from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.config import config
from app.db import Base, engine
from app.db.seed import seed_reference_data
from app.endpoints import chat_router, database_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_reference_data(db)
    yield


def register_endpoints(application: FastAPI) -> None:
    application.include_router(chat_router)
    application.include_router(database_router)


api = FastAPI(
    title=config["api"]["title"],
    version=config["api"]["version"],
    lifespan=lifespan,
)
register_endpoints(api)
