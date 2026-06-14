from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 10086


@dataclass
class ModelConfig:
    index: int = 0


@dataclass
class TouchReaction:
    text: list[str] = field(default_factory=list)
    expression: str = ""
    motion: str = ""


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    expressions: dict[str, int] = field(default_factory=dict)
    motions: dict[str, str] = field(default_factory=dict)
    effects: dict[int, int] = field(default_factory=dict)
    touch_reactions: dict[str, TouchReaction] = field(default_factory=dict)


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    p = Path(path)
    if not p.exists():
        return AppConfig()

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    touch_reactions = {}
    for area, cfg in data.get("touch_reactions", {}).items():
        touch_reactions[area] = TouchReaction(
            text=cfg.get("text", []),
            expression=cfg.get("expression", ""),
            motion=cfg.get("motion", ""),
        )

    return AppConfig(
        server=ServerConfig(**data.get("server", {})),
        model=ModelConfig(**data.get("model", {})),
        expressions=data.get("expressions", {}),
        motions=data.get("motions", {}),
        effects=data.get("effects", {}),
        touch_reactions=touch_reactions,
    )
