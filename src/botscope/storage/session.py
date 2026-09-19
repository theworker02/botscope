"""Local analytical storage — SQLite metadata + JSONL/Parquet-friendly events."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from uuid import uuid4

from botscope.__version__ import __version__
from botscope.normalize.event import NormalizedEvent


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    botscope_version TEXT NOT NULL,
    classifier_version TEXT,
    ruleset_version TEXT,
    signature_version TEXT,
    native_backend TEXT,
    source_path TEXT,
    source_hash TEXT,
    is_demo INTEGER NOT NULL DEFAULT 0,
    config_json TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS aggregates (
    session_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    provenance TEXT NOT NULL,
    PRIMARY KEY (session_id, key),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
"""


@dataclass
class SessionMeta:
    id: str
    created_at: datetime
    botscope_version: str
    classifier_version: str | None
    ruleset_version: str | None
    signature_version: str | None
    native_backend: str | None
    source_path: str | None
    source_hash: str | None
    is_demo: bool
    config: dict[str, Any]


class SessionStore:
    """Portable analysis session (.bscope directory or zip-like folder layout).

    Layout:
      analysis.bscope/
        meta.sqlite
        events.jsonl
        report.json
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if self.path.suffix.lower() == ".bscope":
            self.root = self.path
        else:
            self.root = self.path
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "meta.sqlite"
        self.events_path = self.root / "events.jsonl"
        self.report_path = self.root / "report.json"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def create_session(
        self,
        *,
        source_path: str | None = None,
        source_hash: str | None = None,
        classifier_version: str | None = None,
        ruleset_version: str | None = None,
        signature_version: str | None = None,
        native_backend: str | None = None,
        is_demo: bool = False,
        config: dict[str, Any] | None = None,
    ) -> str:
        session_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO sessions (
                id, created_at, botscope_version, classifier_version, ruleset_version,
                signature_version, native_backend, source_path, source_hash, is_demo, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                now,
                __version__,
                classifier_version,
                ruleset_version,
                signature_version,
                native_backend,
                source_path,
                source_hash,
                1 if is_demo else 0,
                json.dumps(config or {}),
            ),
        )
        self._conn.commit()
        return session_id

    def append_events(self, events: Iterable[NormalizedEvent]) -> int:
        count = 0
        with self.events_path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(event.model_dump_json() + "\n")
                count += 1
        return count

    def iter_events(self) -> Iterator[NormalizedEvent]:
        if not self.events_path.exists():
            return iter(())
        def _gen() -> Iterator[NormalizedEvent]:
            with self.events_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        yield NormalizedEvent.model_validate_json(line)
        return _gen()

    def set_aggregate(self, session_id: str, key: str, value: Any, provenance: str) -> None:
        self._conn.execute(
            """
            INSERT INTO aggregates (session_id, key, value_json, provenance)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id, key) DO UPDATE SET
                value_json=excluded.value_json,
                provenance=excluded.provenance
            """,
            (session_id, key, json.dumps(value), provenance),
        )
        self._conn.commit()

    def get_aggregates(self, session_id: str) -> dict[str, Any]:
        rows = self._conn.execute(
            "SELECT key, value_json, provenance FROM aggregates WHERE session_id = ?",
            (session_id,),
        ).fetchall()
        return {
            key: {"value": json.loads(value_json), "provenance": provenance}
            for key, value_json, provenance in rows
        }

    def latest_session_id(self) -> str | None:
        row = self._conn.execute(
            "SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    def get_session(self, session_id: str) -> SessionMeta | None:
        row = self._conn.execute(
            """
            SELECT id, created_at, botscope_version, classifier_version, ruleset_version,
                   signature_version, native_backend, source_path, source_hash, is_demo, config_json
            FROM sessions WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return SessionMeta(
            id=row[0],
            created_at=datetime.fromisoformat(row[1]),
            botscope_version=row[2],
            classifier_version=row[3],
            ruleset_version=row[4],
            signature_version=row[5],
            native_backend=row[6],
            source_path=row[7],
            source_hash=row[8],
            is_demo=bool(row[9]),
            config=json.loads(row[10] or "{}"),
        )

    def write_report(self, report: dict[str, Any]) -> Path:
        self.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return self.report_path

    def list_sessions(self) -> list[SessionMeta]:
        """Return all session metadata rows ordered by created_at descending."""
        rows = self._conn.execute(
            """
            SELECT id, created_at, botscope_version, classifier_version, ruleset_version,
                   signature_version, native_backend, source_path, source_hash, is_demo, config_json
            FROM sessions ORDER BY created_at DESC
            """
        ).fetchall()
        return [
            SessionMeta(
                id=row[0],
                created_at=datetime.fromisoformat(row[1]),
                botscope_version=row[2],
                classifier_version=row[3],
                ruleset_version=row[4],
                signature_version=row[5],
                native_backend=row[6],
                source_path=row[7],
                source_hash=row[8],
                is_demo=bool(row[9]),
                config=json.loads(row[10] or "{}"),
            )
            for row in rows
        ]

    def update_session_notes(self, session_id: str, notes: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET notes = ? WHERE id = ?",
            (notes, session_id),
        )
        self._conn.commit()

    def merge_session_config(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        """Merge keys into sessions.config_json (additive; preserves Agent 1 fields)."""
        meta = self.get_session(session_id)
        if meta is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        merged = dict(meta.config)
        merged.update(patch)
        self._conn.execute(
            "UPDATE sessions SET config_json = ? WHERE id = ?",
            (json.dumps(merged), session_id),
        )
        self._conn.commit()
        return merged

    def replace_events(self, events: Iterable[NormalizedEvent]) -> int:
        """Overwrite events.jsonl with the provided iterable (full rewrite)."""
        count = 0
        with self.events_path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(event.model_dump_json() + "\n")
                count += 1
        return count

    def workspace_path(self) -> Path:
        return self.root / "workspace.json"

    def save_workspace_document(self, document: dict[str, Any]) -> Path:
        path = self.workspace_path()
        path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        return path

    def load_workspace_document(self) -> dict[str, Any]:
        path = self.workspace_path()
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def summary(self) -> dict[str, Any]:
        """Compact summary for history browsers / CLI open."""
        sid = self.latest_session_id()
        meta = self.get_session(sid) if sid else None
        # Count events without fully materializing when possible.
        event_count = 0
        if self.events_path.exists():
            with self.events_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        event_count += 1
        return {
            "path": str(self.root),
            "session_id": sid,
            "event_count": event_count,
            "is_demo": meta.is_demo if meta else False,
            "classifier_version": meta.classifier_version if meta else None,
            "ruleset_version": meta.ruleset_version if meta else None,
            "signature_version": meta.signature_version if meta else None,
            "source_path": meta.source_path if meta else None,
            "source_hash": meta.source_hash if meta else None,
            "botscope_version": meta.botscope_version if meta else None,
            "created_at": meta.created_at.isoformat() if meta else None,
        }
