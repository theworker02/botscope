"""Timeline bucketing tests."""

from __future__ import annotations

from datetime import datetime, timezone

from botscope.normalize.event import NormalizedEvent, SourceType
from botscope.timeline import BucketResolution, auto_resolution, bucket_events


def _evt(ts: str, cat: str) -> NormalizedEvent:
    return NormalizedEvent(
        timestamp=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        source_type=SourceType.WEB_LOG,
        classification=cat,
        confidence=0.5,
    )


def test_bucket_events_minute() -> None:
    events = [
        _evt("2026-09-18T10:00:01", "AI CRAWLER"),
        _evt("2026-09-18T10:00:45", "HUMAN-LIKELY"),
        _evt("2026-09-18T10:01:10", "UNKNOWN"),
    ]
    series = bucket_events(events, resolution=BucketResolution.MINUTE)
    assert series.resolution is BucketResolution.MINUTE
    assert len(series.buckets) == 2
    assert series.buckets[0].total == 2
    chart = series.to_chart_series()
    assert chart[0][1] == 2


def test_auto_resolution_short_span() -> None:
    events = [_evt("2026-09-18T10:00:00", "UNKNOWN"), _evt("2026-09-18T10:00:30", "UNKNOWN")]
    assert auto_resolution(events, target_buckets=48) in {
        BucketResolution.SECOND,
        BucketResolution.MINUTE,
    }
