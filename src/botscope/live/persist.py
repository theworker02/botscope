"""Continuous live-session persistence into SessionStore.

Status: IMPLEMENTED — append-only events; debounced aggregates/report.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from botscope.__version__ import __version__
from botscope.classify.result import MODEL_VERSION, RULESET_VERSION
from botscope.live.aggregator import ObservatorySnapshot
from botscope.normalize.event import NormalizedEvent
from botscope.reports.generator import build_report
from botscope.statistics.aggregate import aggregate_events
from botscope.storage.session import SessionStore


@dataclass
class LiveSessionWriter:
    """Append live batches to a ``.bscope`` without rewriting the JSONL each tick."""

    path: Path
    source_label: str | None = None
    debounce_s: float = 2.0
    max_memory_events: int = 50_000
    _store: SessionStore | None = field(default=None, init=False, repr=False)
    session_id: str | None = field(default=None, init=False)
    _pending_agg: bool = field(default=False, init=False)
    _last_flush: float = field(default=0.0, init=False)
    _memory: list[NormalizedEvent] = field(default_factory=list, init=False)
    _total_appended: int = field(default=0, init=False)

    def open(self, *, config: dict[str, Any] | None = None) -> str:
        if self._store is not None:
            return self.session_id or ""
        self.path = Path(self.path)
        self._store = SessionStore(self.path)
        self.session_id = self._store.create_session(
            source_path=self.source_label,
            classifier_version=MODEL_VERSION,
            ruleset_version=RULESET_VERSION,
            is_demo=False,
            config={
                "botscope_version": __version__,
                "live": True,
                **(config or {}),
            },
        )
        self._last_flush = time.monotonic()
        return self.session_id

    @property
    def memory_events(self) -> list[NormalizedEvent]:
        return list(self._memory)

    @property
    def total_appended(self) -> int:
        return self._total_appended

    def append(self, events: Iterable[NormalizedEvent]) -> int:
        batch = list(events)
        if not batch:
            return 0
        if self._store is None:
            self.open()
        assert self._store is not None
        n = self._store.append_events(batch)
        self._total_appended += n
        self._memory.extend(batch)
        if len(self._memory) > self.max_memory_events:
            overflow = len(self._memory) - self.max_memory_events
            del self._memory[:overflow]
        self._pending_agg = True
        self._maybe_flush_aggregates(force=False)
        return n

    def note_snapshot(self, snapshot: ObservatorySnapshot) -> None:
        """Opportunistic aggregate flush when a bound snapshot arrives."""
        if self._pending_agg:
            self._maybe_flush_aggregates(force=False, snapshot=snapshot)

    def flush(self, *, snapshot: ObservatorySnapshot | None = None) -> None:
        self._maybe_flush_aggregates(force=True, snapshot=snapshot)

    def _maybe_flush_aggregates(
        self,
        *,
        force: bool,
        snapshot: ObservatorySnapshot | None = None,
    ) -> None:
        if self._store is None or self.session_id is None:
            return
        if not self._pending_agg and not force:
            return
        now = time.monotonic()
        if not force and (now - self._last_flush) < self.debounce_s:
            return
        events = self._memory
        if not events and snapshot is None:
            return
        if events:
            stats = aggregate_events(events, is_demo=False)
            report = build_report(stats, events=events, is_demo=False)
            for key, value in stats.to_dict().items():
                self._store.set_aggregate(
                    self.session_id, key, value, stats.provenance.value
                )
        else:
            report = {
                "title": "BotScope Live Session",
                "generated_at": snapshot.generated_at if snapshot else None,
                "live": True,
            }
        if snapshot is not None:
            report["live_snapshot"] = snapshot.to_dict()
        report["live"] = True
        report["events_appended"] = self._total_appended
        self._store.write_report(report)
        self._last_flush = now
        self._pending_agg = False

    def close(self) -> Path | None:
        if self._store is None:
            return None
        self.flush()
        root = self._store.root
        self._store.close()
        self._store = None
        return root


def suggest_live_session_path(base: Path | None = None) -> Path:
    """Suggest a timestamped live session directory under ``base`` or cwd."""
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = Path(base) if base is not None else Path.cwd()
    return root / f"live_{stamp}.bscope"
