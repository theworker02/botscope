"""Timeline bucketing algorithms for Observatory charts and live snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES, BotCategory
from botscope.normalize.event import NormalizedEvent


class BucketResolution(str, Enum):
    SECOND = "1s"
    MINUTE = "1m"
    FIVE_MINUTE = "5m"
    HOUR = "1h"
    DAY = "1d"

    @property
    def delta(self) -> timedelta:
        return {
            BucketResolution.SECOND: timedelta(seconds=1),
            BucketResolution.MINUTE: timedelta(minutes=1),
            BucketResolution.FIVE_MINUTE: timedelta(minutes=5),
            BucketResolution.HOUR: timedelta(hours=1),
            BucketResolution.DAY: timedelta(days=1),
        }[self]


@dataclass
class TimelineBucket:
    start: datetime
    total: int = 0
    automated: int = 0
    human: int = 0
    unknown: int = 0
    bytes_out: int = 0
    by_category: dict[str, int] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return self.start.astimezone(timezone.utc).isoformat()

    def ingest(self, event: NormalizedEvent) -> None:
        cat = event.classification or BotCategory.UNKNOWN.value
        self.total += 1
        self.by_category[cat] = self.by_category.get(cat, 0) + 1
        self.bytes_out += int(event.bytes_out or 0)
        if cat == BotCategory.HUMAN_LIKELY.value:
            self.human += 1
        elif cat == BotCategory.UNKNOWN.value:
            self.unknown += 1
        elif cat in {c.value for c in AUTOMATION_CATEGORIES}:
            self.automated += 1
        else:
            self.unknown += 1

    def to_tuple(self) -> tuple[str, int, int, int]:
        """Legacy Observatory chart format: (iso, total, automated, human)."""
        return (self.key, self.total, self.automated, self.human)

    def to_dict(self) -> dict:
        return {
            "start": self.key,
            "total": self.total,
            "automated": self.automated,
            "human": self.human,
            "unknown": self.unknown,
            "bytes_out": self.bytes_out,
            "by_category": dict(self.by_category),
        }


@dataclass
class TimelineSeries:
    resolution: BucketResolution
    buckets: list[TimelineBucket] = field(default_factory=list)

    def to_chart_series(self) -> list[tuple[str, int, int, int]]:
        return [b.to_tuple() for b in self.buckets]

    def to_dict(self) -> dict:
        return {
            "resolution": self.resolution.value,
            "bucket_count": len(self.buckets),
            "buckets": [b.to_dict() for b in self.buckets],
        }


def floor_timestamp(ts: datetime, resolution: BucketResolution) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts = ts.astimezone(timezone.utc)
    if resolution is BucketResolution.SECOND:
        return ts.replace(microsecond=0)
    if resolution is BucketResolution.MINUTE:
        return ts.replace(second=0, microsecond=0)
    if resolution is BucketResolution.FIVE_MINUTE:
        minute = (ts.minute // 5) * 5
        return ts.replace(minute=minute, second=0, microsecond=0)
    if resolution is BucketResolution.HOUR:
        return ts.replace(minute=0, second=0, microsecond=0)
    if resolution is BucketResolution.DAY:
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    return ts.replace(microsecond=0)


def auto_resolution(
    events: Iterable[NormalizedEvent],
    *,
    target_buckets: int = 48,
) -> BucketResolution:
    """Pick a resolution so roughly ``target_buckets`` cover the span."""
    stamps: list[datetime] = []
    for event in events:
        if event.timestamp:
            ts = event.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            stamps.append(ts)
    if len(stamps) < 2:
        return BucketResolution.MINUTE
    span = max(stamps) - min(stamps)
    seconds = max(span.total_seconds(), 1.0)
    per = seconds / max(target_buckets, 1)
    if per <= 1:
        return BucketResolution.SECOND
    if per <= 60:
        return BucketResolution.MINUTE
    if per <= 300:
        return BucketResolution.FIVE_MINUTE
    if per <= 3600:
        return BucketResolution.HOUR
    return BucketResolution.DAY


def bucket_events(
    events: Iterable[NormalizedEvent],
    *,
    resolution: BucketResolution | None = None,
    target_buckets: int = 48,
) -> TimelineSeries:
    """Aggregate events into ordered timeline buckets."""
    materialised = list(events)
    res = resolution or auto_resolution(materialised, target_buckets=target_buckets)
    accum: dict[datetime, TimelineBucket] = {}
    for event in materialised:
        if not event.timestamp:
            continue
        key = floor_timestamp(event.timestamp, res)
        if key not in accum:
            accum[key] = TimelineBucket(start=key)
        accum[key].ingest(event)
    ordered = [accum[k] for k in sorted(accum)]
    return TimelineSeries(resolution=res, buckets=ordered)


def merge_bucket_dicts(
    left: dict[str, TimelineBucket],
    right: Iterable[TimelineBucket],
) -> dict[str, TimelineBucket]:
    """Incremental merge helper for streaming aggregators."""
    out = dict(left)
    for bucket in right:
        existing = out.get(bucket.key)
        if existing is None:
            out[bucket.key] = bucket
            continue
        existing.total += bucket.total
        existing.automated += bucket.automated
        existing.human += bucket.human
        existing.unknown += bucket.unknown
        existing.bytes_out += bucket.bytes_out
        for cat, n in bucket.by_category.items():
            existing.by_category[cat] = existing.by_category.get(cat, 0) + n
    return out
