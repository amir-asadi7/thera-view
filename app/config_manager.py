from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict


CONFIG_FILE = Path(__file__).resolve().parent / "config.json"


@dataclass
class AppConfig:
    device_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    output_dir: str = "recordings"

    @property
    def resolution(self) -> tuple[int, int]:
        return self.width, self.height

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "AppConfig":
        return cls(**data)


def load_config() -> AppConfig:
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as fp:
            try:
                data = json.load(fp)
                return AppConfig.from_json(data)
            except json.JSONDecodeError:
                pass
    config = AppConfig()
    save_config(config)
    return config


def save_config(config: AppConfig) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as fp:
        json.dump(config.to_json(), fp, indent=2)
