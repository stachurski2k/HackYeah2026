import asyncio
from collections.abc import AsyncGenerator

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api import api
from api.config import config
from api.db import Base, get_db
from api.db.seed import seed_reference_data

test_engine = create_engine(
    "sqlite:///./test_proxy.db",
    connect_args={"check_same_thread": False},
)


async def get_test_db() -> AsyncGenerator[Session, None]:
    with Session(test_engine, expire_on_commit=False) as db:
        yield db


api.dependency_overrides[get_db] = get_test_db


def reset_database() -> None:
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    with Session(test_engine) as db:
        seed_reference_data(db)


def test_config_is_loaded() -> None:
    assert config.get("app.title", "") == "AI Proxy API"
    assert config.get("missing.value", "default") == "default"


def test_token_user_and_chat_flow() -> None:
    async def scenario() -> None:
        reset_database()
        transport = httpx.ASGITransport(app=api)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            token_response = await client.post("/tokens")
            assert token_response.status_code == 201
            token = token_response.json()["token"]

            user_response = await client.post(
                "/users", json={"name": "Ala", "token": token, "groups": ["user", "office"]}
            )
            assert user_response.status_code == 201
            assert set(user_response.json()["groups"]) == {"user", "office"}

            assert (await client.post("/chat", json={"message": "hello"})).status_code == 401
            chat_response = await client.post(
                "/chat",
                json={"message": "hello"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert chat_response.status_code == 200
            assert chat_response.json()["authenticated"] is True
            assert chat_response.json()["user_id"] == user_response.json()["id"]

    asyncio.run(scenario())


def test_configuration_resources() -> None:
    async def scenario() -> None:
        reset_database()
        transport = httpx.ASGITransport(app=api)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            model_response = await client.post(
                "/models", json={"name": "llama", "api_url": "http://localhost:11434/api/chat"}
            )
            assert model_response.status_code == 201
            policy_response = await client.put(
                f"/models/{model_response.json()['id']}/policies",
                json={"group": "user", "permission": "ALLOW"},
            )
            assert policy_response.status_code == 204

            action_response = await client.post(
                "/actions",
                json={
                    "name": "mask-pii",
                    "prompt": "Mask personal data",
                    "action_name": "mask_pii",
                },
            )
            assert action_response.status_code == 201
            tool_response = await client.post(
                "/validation-tools", json={"name": "prompt-injection-check"}
            )
            assert tool_response.status_code == 201

    asyncio.run(scenario())
