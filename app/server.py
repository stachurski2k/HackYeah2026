import uvicorn

from api.config import config


def run() -> None:
    uvicorn.run(
        "api:api",
        host=config.get("app.ip", "127.0.0.1"),
        port=config.get("app.port", 8000),
        reload=config.get("app.reload", False),
    )


if __name__ == "__main__":
    run()
