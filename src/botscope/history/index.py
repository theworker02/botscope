"""Recent-session history index (local JSON file)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def default_history_path() -> Path:
    """Platform-appropriate path for the recent-sessions index."""
    override = os.environ.get("BOTSCOPE_HISTORY_PATH")
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "BotScope" / "recent_sessions.json"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "botscope" / "recent_sessions.json"
    return Path.home() / ".local" / "share" / "botscope" / "recent_sessions.json"


@dataclass
class HistoryEntry:
    path: str
    opened_at: str
    label: str | None = None
    event_count: int | None = None
    is_demo: bool = False
    classifier_version: str | None = None
    source_path: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "opened_at": self.opened_at,
            "label": self.label,
            "event_count": self.event_count,
            "is_demo": self.is_demo,
            "classifier_version": self.classifier_version,
            "source_path": self.source_path,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        return cls(
            path=str(data["path"]),
            opened_at=str(data.get("opened_at") or ""),
            label=data.get("label"),
            event_count=data.get("event_count"),
            is_demo=bool(data.get("is_demo", False)),
            classifier_version=data.get("classifier_version"),
            source_path=data.get("source_path"),
            notes=data.get("notes"),
        )


@dataclass
class SessionHistory:
    """MRU list of ``.bscope`` session directories."""

    path: Path = field(default_factory=default_history_path)
    max_entries: int = 40
    entries: list[HistoryEntry] = field(default_factory=list)

    def load(self) -> SessionHistory:
        if not self.path.exists():
            self.entries = []
            return self
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.entries = []
            return self
        raw = data.get("entries") if isinstance(data, dict) else data
        self.entries = [HistoryEntry.from_dict(x) for x in (raw or []) if isinstance(x, dict)]
        return self

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entries": [e.to_dict() for e in self.entries[: self.max_entries]],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self.path

    def remember(
        self,
        session_path: str | Path,
        *,
        label: str | None = None,
        event_count: int | None = None,
        is_demo: bool = False,
        classifier_version: str | None = None,
        source_path: str | None = None,
        notes: str | None = None,
    ) -> HistoryEntry:
        resolved = str(Path(session_path).resolve())
        now = datetime.now(timezone.utc).isoformat()
        entry = HistoryEntry(
            path=resolved,
            opened_at=now,
            label=label or Path(resolved).name,
            event_count=event_count,
            is_demo=is_demo,
            classifier_version=classifier_version,
            source_path=source_path,
            notes=notes,
        )
        self.entries = [e for e in self.entries if e.path != resolved]
        self.entries.insert(0, entry)
        self.entries = self.entries[: self.max_entries]
        self.save()
        return entry

    def recent(self, limit: int = 20) -> list[HistoryEntry]:
        return list(self.entries[:limit])

    def existing_only(self) -> Iterator[HistoryEntry]:
        for entry in self.entries:
            if Path(entry.path).exists():
                yield entry

    def prune_missing(self) -> int:
        before = len(self.entries)
        self.entries = [e for e in self.entries if Path(e.path).exists()]
        removed = before - len(self.entries)
        if removed:
            self.save()
        return removed
