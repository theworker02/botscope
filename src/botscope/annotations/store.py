"""Researcher annotations — separate from classifier evidence.

Status: IMPLEMENTED

Uses the annotations table already present in Agent 1 SessionStore schema,
plus an optional JSONL sidecar for portable note export.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


@dataclass
class Annotation:
    id: str
    session_id: str
    created_at: str
    body: str
    event_id: str | None = None
    tags: list[str] | None = None
    author: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "body": self.body,
            "event_id": self.event_id,
            "tags": list(self.tags or []),
            "author": self.author,
            "kind": "researcher_annotation",
            "note": "Annotations are researcher commentary, not classifier evidence.",
        }


class AnnotationStore:
    """Manage researcher annotations for a .bscope session directory."""

    def __init__(self, session_path: str | Path) -> None:
        self.root = Path(session_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "meta.sqlite"
        self.sidecar = self.root / "annotations.jsonl"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                body TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
            """
        )
        # Extended columns via sidecar JSON; keep SQLite minimal for A1 compatibility.
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def add(
        self,
        session_id: str,
        body: str,
        *,
        event_id: str | None = None,
        tags: Iterable[str] | None = None,
        author: str | None = None,
    ) -> Annotation:
        now = datetime.now(timezone.utc).isoformat()
        # Persist body into Agent 1 table for basic visibility.
        self._conn.execute(
            "INSERT INTO annotations (session_id, created_at, body) VALUES (?, ?, ?)",
            (session_id, now, body),
        )
        self._conn.commit()
        ann = Annotation(
            id=str(uuid4()),
            session_id=session_id,
            created_at=now,
            body=body,
            event_id=event_id,
            tags=list(tags or []),
            author=author,
        )
        with self.sidecar.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(ann.to_dict()) + "\n")
        return ann

    def list_annotations(self, session_id: str | None = None) -> list[Annotation]:
        if not self.sidecar.exists():
            return []
        out: list[Annotation] = []
        with self.sidecar.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if session_id and data.get("session_id") != session_id:
                    continue
                out.append(
                    Annotation(
                        id=data["id"],
                        session_id=data["session_id"],
                        created_at=data["created_at"],
                        body=data["body"],
                        event_id=data.get("event_id"),
                        tags=data.get("tags") or [],
                        author=data.get("author"),
                    )
                )
        return out
