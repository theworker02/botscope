"""Local analysis presets — no account required."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from botscope.ux.recents import _ux_dir


@dataclass
class AnalysisPreset:
    name: str
    filters: dict[str, Any] = field(default_factory=dict)
    denominator: str = "requests"
    time_range_key: str = "all"
    breakdown_dimension: str | None = None
    chart_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisPreset:
        return cls(
            name=str(data.get("name") or "Untitled"),
            filters=dict(data.get("filters") or {}),
            denominator=str(data.get("denominator") or "requests"),
            time_range_key=str(data.get("time_range_key") or "all"),
            breakdown_dimension=data.get("breakdown_dimension"),
            chart_config=dict(data.get("chart_config") or {}),
        )


BUILTIN_PRESETS: list[AnalysisPreset] = [
    AnalysisPreset("Overview"),
    AnalysisPreset("Automation Investigation", filters={"family": "automated"}),
    AnalysisPreset("Unknown Traffic", filters={"family": "unknown"}),
    AnalysisPreset("High Confidence Only", filters={"confidence_min": 0.7}),
    AnalysisPreset("Bot Attribution", filters={"family": "automated"}),
    AnalysisPreset("Bandwidth Impact", denominator="bytes"),
]


def presets_path() -> Path:
    return _ux_dir() / "presets.json"


def load_presets() -> list[AnalysisPreset]:
    path = presets_path()
    if not path.exists():
        return list(BUILTIN_PRESETS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return list(BUILTIN_PRESETS)
        return [AnalysisPreset.from_dict(x) for x in raw if isinstance(x, dict)]
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return list(BUILTIN_PRESETS)


def save_presets(presets: list[AnalysisPreset]) -> None:
    path = presets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([p.to_dict() for p in presets], indent=2),
        encoding="utf-8",
    )
