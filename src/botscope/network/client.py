"""BotScope Network — opt-in aggregate contribution (OFF by default)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from platformdirs import user_config_dir


@dataclass
class NetworkConfig:
    enabled: bool = False  # MUST default OFF
    endpoint: str | None = None
    sensor_id: str = field(default_factory=lambda: str(uuid4()))
    contribute_raw: bool = False  # never enable by default
    aggregate_only: bool = True


class NetworkClient:
    """Local configuration for optional network participation.

    v0.1 does not deploy a global service. This module only manages opt-in
    settings and prepares privacy-preserving aggregate payloads.
    """

    def __init__(self, config: NetworkConfig | None = None) -> None:
        self.config = config or load_network_config()

    @property
    def contribution_enabled(self) -> bool:
        return bool(self.config.enabled)

    def status(self) -> dict[str, Any]:
        return {
            "contribution": "ON" if self.config.enabled else "OFF",
            "default": "OFF",
            "aggregate_only": self.config.aggregate_only,
            "contribute_raw": self.config.contribute_raw,
            "sensor_id": self.config.sensor_id,
            "endpoint": self.config.endpoint,
            "note": (
                "BotScope Network contribution is opt-in and OFF by default. "
                "No traffic is uploaded unless explicitly enabled by the user."
            ),
        }

    def build_aggregate_payload(self, aggregates: dict[str, Any]) -> dict[str, Any]:
        if self.config.contribute_raw:
            raise RuntimeError("Raw contribution is refused by default policy in v0.1")
        return {
            "schema_version": "0.1.0",
            "sensor_id": self.config.sensor_id,
            "aggregates": {
                k: v
                for k, v in aggregates.items()
                if k
                in {
                    "total_events",
                    "total_bytes",
                    "by_category",
                    "confidence_histogram",
                    "automation_fraction_requests",
                }
            },
            "privacy": "aggregate-only",
        }


def config_path() -> Path:
    root = Path(user_config_dir("botscope", "botscope"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "network.json"


def load_network_config() -> NetworkConfig:
    path = config_path()
    if not path.exists():
        cfg = NetworkConfig()
        save_network_config(cfg)
        return cfg
    data = json.loads(path.read_text(encoding="utf-8"))
    return NetworkConfig(
        enabled=bool(data.get("enabled", False)),
        endpoint=data.get("endpoint"),
        sensor_id=data.get("sensor_id") or str(uuid4()),
        contribute_raw=False,  # force false in v0.1 loader
        aggregate_only=True,
    )


def save_network_config(config: NetworkConfig) -> None:
    path = config_path()
    path.write_text(
        json.dumps(
            {
                "enabled": config.enabled,
                "endpoint": config.endpoint,
                "sensor_id": config.sensor_id,
                "contribute_raw": False,
                "aggregate_only": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
