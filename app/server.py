import uvicorn

from app.config import config


def run() -> None:
    uvicorn.run(
        "app.api:api",
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=config["api"]["reload"],
    )


if __name__ == "__main__":
    run()
