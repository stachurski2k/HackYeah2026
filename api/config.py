from pathlib import Path
from tomllib import load
from typing import Any, TypeVar, cast

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"
T = TypeVar("T")

with CONFIG_PATH.open("rb") as config_file:
    config_data: dict[str, Any] = load(config_file)


class Config:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def get(self, key: str, default: T) -> T:
        value: Any = self._data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return cast(T, value)


config = Config(config_data)
