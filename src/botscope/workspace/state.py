"""Analysis Workspace schema and serializers.

A workspace captures *how* an analyst is looking at a session — not the
events themselves. Events live in SessionStore; this module stores view
state so reopen restores filters, charts, and column layout.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE_SCHEMA_VERSION = 1
WORKSPACE_FILENAME = "workspace.json"


class WorkspaceError(ValueError):
    """Invalid or incompatible workspace document."""


@dataclass
class TimeRange:
    """Optional inclusive observation window (ISO-8601 UTC strings)."""

    start: str | None = None
    end: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> TimeRange:
        if not data:
            return cls()
        return cls(start=data.get("start"), end=data.get("end"))


@dataclass
class ChartOverlay:
    """Named chart overlay preference (category highlight, series toggle)."""

    chart_id: str
    enabled: bool = True
    categories: list[str] = field(default_factory=list)
    color_hint: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "enabled": self.enabled,
            "categories": list(self.categories),
            "color_hint": self.color_hint,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChartOverlay:
        return cls(
            chart_id=str(data.get("chart_id") or "unknown"),
            enabled=bool(data.get("enabled", True)),
            categories=list(data.get("categories") or []),
            color_hint=data.get("color_hint"),
            note=data.get("note"),
        )


@dataclass
class ColumnPref:
    """Events-table column visibility and order preference."""

    key: str
    visible: bool = True
    width: int | None = None
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ColumnPref:
        return cls(
            key=str(data["key"]),
            visible=bool(data.get("visible", True)),
            width=data.get("width"),
            order=int(data.get("order", 0)),
        )


@dataclass
class AnalysisWorkspace:
    """Full Analysis Workspace document (schema v1)."""

    schema_version: int = WORKSPACE_SCHEMA_VERSION
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    denominator: str = "requests"
    query: str = ""
    filter_category: str | None = None
    filter_text: str = ""
    selected_event_id: str | None = None
    time_range: TimeRange = field(default_factory=TimeRange)
    chart_overlays: list[ChartOverlay] = field(default_factory=list)
    columns: list[ColumnPref] = field(default_factory=list)
    annotation_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "updated_at": self.updated_at,
            "denominator": self.denominator,
            "query": self.query,
            "filter_category": self.filter_category,
            "filter_text": self.filter_text,
            "selected_event_id": self.selected_event_id,
            "time_range": self.time_range.to_dict(),
            "chart_overlays": [c.to_dict() for c in self.chart_overlays],
            "columns": [c.to_dict() for c in self.columns],
            "annotation_ids": list(self.annotation_ids),
            "notes": list(self.notes),
            "extras": dict(self.extras),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisWorkspace:
        if not isinstance(data, dict):
            raise WorkspaceError("Workspace document must be a JSON object")
        version = int(data.get("schema_version") or 0)
        if version > WORKSPACE_SCHEMA_VERSION:
            raise WorkspaceError(
                f"Unsupported workspace schema_version={version} "
                f"(max supported={WORKSPACE_SCHEMA_VERSION})"
            )
        overlays = [ChartOverlay.from_dict(x) for x in (data.get("chart_overlays") or [])]
        columns = [ColumnPref.from_dict(x) for x in (data.get("columns") or [])]
        return cls(
            schema_version=version or WORKSPACE_SCHEMA_VERSION,
            updated_at=str(data.get("updated_at") or datetime.now(timezone.utc).isoformat()),
            denominator=str(data.get("denominator") or "requests"),
            query=str(data.get("query") or ""),
            filter_category=data.get("filter_category"),
            filter_text=str(data.get("filter_text") or ""),
            selected_event_id=data.get("selected_event_id"),
            time_range=TimeRange.from_dict(data.get("time_range")),
            chart_overlays=overlays,
            columns=columns,
            annotation_ids=list(data.get("annotation_ids") or []),
            notes=list(data.get("notes") or []),
            extras=dict(data.get("extras") or {}),
        )

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def save_workspace(path: str | Path, workspace: AnalysisWorkspace) -> Path:
    """Write ``workspace.json`` under a ``.bscope`` root (or any directory)."""
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    target = root / WORKSPACE_FILENAME if root.is_dir() else root
    if root.is_dir():
        target = root / WORKSPACE_FILENAME
    workspace.touch()
    target.write_text(json.dumps(workspace.to_dict(), indent=2), encoding="utf-8")
    return target


def load_workspace(path: str | Path) -> AnalysisWorkspace:
    """Load workspace from a ``.bscope`` directory or a workspace.json path."""
    path = Path(path)
    if path.is_dir():
        path = path / WORKSPACE_FILENAME
    if not path.exists():
        return AnalysisWorkspace()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkspaceError(f"Corrupt workspace file: {exc}") from exc
    return AnalysisWorkspace.from_dict(data)
