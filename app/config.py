from pathlib import Path
from tomllib import load
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"

with CONFIG_PATH.open("rb") as config_file:
    config: dict[str, Any] = load(config_file)
