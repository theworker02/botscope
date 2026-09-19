"""Streaming aggregator — bound snapshots for Observatory GUI refresh.

Workers feed events continuously; the GUI receives compact snapshots a
few times per second, not one signal per event.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES, BotCategory
from botscope.normalize.event import NormalizedEvent
from botscope.timeline.bucket import BucketResolution, TimelineBucket, floor_timestamp


@dataclass
class ObservatorySnapshot:
    """Compact bound state published to the GUI (not raw event streams)."""

    generated_at: str
    total_events: int
    total_bytes: int
    by_category: dict[str, int]
    automated_share: float | None
    human_share: float | None
    unknown_share: float | None
    timeline: list[tuple[str, int, int, int]]
    events_per_second: float
    is_live: bool = True
    is_demo: bool = False
    source_label: str | None = None
    note: str = (
        "Shares are CLASSIFIED aggregates over this authorized live source only."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_events": self.total_events,
            "total_bytes": self.total_bytes,
            "by_category": dict(self.by_category),
            "automated_share": self.automated_share,
            "human_share": self.human_share,
            "unknown_share": self.unknown_share,
            "timeline": list(self.timeline),
            "events_per_second": round(self.events_per_second, 4),
            "is_live": self.is_live,
            "is_demo": self.is_demo,
            "source_label": self.source_label,
            "note": self.note,
        }


class StreamingAggregator:
    """Accumulate events into counters + timeline buckets; emit rate-limited snapshots."""

    def __init__(
        self,
        *,
        max_hz: float = 5.0,
        resolution: BucketResolution = BucketResolution.MINUTE,
        max_timeline_buckets: int = 120,
        source_label: str | None = None,
        is_demo: bool = False,
    ) -> None:
        if max_hz <= 0:
            raise ValueError("max_hz must be positive")
        self.max_hz = max_hz
        self.min_interval = 1.0 / max_hz
        self.resolution = resolution
        self.max_timeline_buckets = max_timeline_buckets
        self.source_label = source_label
        self.is_demo = is_demo

        self._total_events = 0
        self._total_bytes = 0
        self._by_category: Counter[str] = Counter()
        self._buckets: dict[str, TimelineBucket] = {}
        self._started_at = time.monotonic()
        self._last_emit = 0.0
        self._window_events = 0
        self._window_started = time.monotonic()

    def ingest(self, events: Iterable[NormalizedEvent]) -> None:
        for event in events:
            self.ingest_one(event)

    def ingest_one(self, event: NormalizedEvent) -> None:
        cat = event.classification or BotCategory.UNKNOWN.value
        self._total_events += 1
        self._total_bytes += int(event.bytes_out or 0)
        self._by_category[cat] += 1
        self._window_events += 1
        ts = event.timestamp or datetime.now(timezone.utc)
        key_dt = floor_timestamp(ts, self.resolution)
        key = key_dt.astimezone(timezone.utc).isoformat()
        if key not in self._buckets:
            self._buckets[key] = TimelineBucket(start=key_dt)
        self._buckets[key].ingest(event)
        if len(self._buckets) > self.max_timeline_buckets:
            # Drop oldest keys to keep snapshot bounded.
            for old in sorted(self._buckets)[: len(self._buckets) - self.max_timeline_buckets]:
                del self._buckets[old]

    def should_emit(self, *, force: bool = False) -> bool:
        if force:
            return True
        now = time.monotonic()
        return (now - self._last_emit) >= self.min_interval

    def _shares(self) -> tuple[float | None, float | None, float | None]:
        n = self._total_events
        if n == 0:
            return None, None, None
        auto_cats = {c.value for c in AUTOMATION_CATEGORIES}
        auto = sum(v for k, v in self._by_category.items() if k in auto_cats)
        human = self._by_category.get(BotCategory.HUMAN_LIKELY.value, 0)
        unknown = self._by_category.get(BotCategory.UNKNOWN.value, 0)
        return auto / n, human / n, unknown / n

    def _eps(self) -> float:
        now = time.monotonic()
        elapsed = now - self._window_started
        if elapsed <= 0:
            return 0.0
        # Rolling-ish: use total span from start for a stable measured rate.
        total_elapsed = now - self._started_at
        if total_elapsed <= 0:
            return 0.0
        return self._total_events / total_elapsed

    def snapshot(self, *, is_live: bool = True, force_mark_emit: bool = True) -> ObservatorySnapshot:
        auto, human, unknown = self._shares()
        timeline = [
            self._buckets[k].to_tuple() for k in sorted(self._buckets)
        ]
        if force_mark_emit:
            self._last_emit = time.monotonic()
        return ObservatorySnapshot(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_events=self._total_events,
            total_bytes=self._total_bytes,
            by_category=dict(self._by_category),
            automated_share=auto,
            human_share=human,
            unknown_share=unknown,
            timeline=timeline,
            events_per_second=self._eps(),
            is_live=is_live,
            is_demo=self.is_demo,
            source_label=self.source_label,
        )

    def maybe_snapshot(self, *, is_live: bool = True) -> ObservatorySnapshot | None:
        if not self.should_emit():
            return None
        return self.snapshot(is_live=is_live)

    def reset_rate_window(self) -> None:
        self._window_events = 0
        self._window_started = time.monotonic()
