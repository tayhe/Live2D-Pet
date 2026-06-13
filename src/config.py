from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class ExAPIConfig:
    host: str = "127.0.0.1"
    port: int = 10086

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}/api"


@dataclass
class ModelConfig:
    index: int = 0


@dataclass
class AppConfig:
    exapi: ExAPIConfig = field(default_factory=ExAPIConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    expressions: dict[str, int] = field(default_factory=dict)
    motions: dict[str, str] = field(default_factory=dict)
    effects: dict[str, int] = field(default_factory=dict)


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    p = Path(path)
    if not p.exists():
        return AppConfig()

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return AppConfig(
        exapi=ExAPIConfig(**data.get("exapi", {})),
        model=ModelConfig(**data.get("model", {})),
        expressions=data.get("expressions", {}),
        motions=data.get("motions", {}),
        effects=data.get("effects", {}),
    )
