"""Streaming aggregator + log-tail tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from botscope.live import LogTailConfig, StreamingAggregator, tail_new_lines
from botscope.normalize.event import NormalizedEvent, SourceType


def _evt(cat: str = "AI CRAWLER") -> NormalizedEvent:
    return NormalizedEvent(
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.WEB_LOG,
        classification=cat,
        confidence=0.7,
        bytes_out=100,
    )


def test_streaming_aggregator_snapshot_rates() -> None:
    agg = StreamingAggregator(max_hz=100.0, source_label="test")
    agg.ingest([_evt(), _evt("HUMAN-LIKELY"), _evt("UNKNOWN")])
    snap = agg.snapshot()
    assert snap.total_events == 3
    assert snap.total_bytes == 300
    assert snap.automated_share is not None
    assert snap.by_category["AI CRAWLER"] == 1
    assert snap.events_per_second >= 0
    assert snap.is_live is True
    # Rate limit: immediate second emit without waiting should be suppressed
    agg2 = StreamingAggregator(max_hz=1.0)
    agg2.ingest_one(_evt())
    first = agg2.maybe_snapshot()
    assert first is not None
    second = agg2.maybe_snapshot()
    assert second is None


def test_tail_new_lines(tmp_path: Path) -> None:
    log = tmp_path / "access.log"
    log.write_text("line-a\n", encoding="utf-8")
    config = LogTailConfig(path=log, poll_interval_s=0.05, start_at_end=True)
    # Append after opening would be ideal; start_at_end means we only see new lines.
    # Write more then read with stop_after.
    log.write_text("line-a\nline-b\n", encoding="utf-8")
    # Re-open from start for deterministic unit test:
    config_start = LogTailConfig(path=log, poll_interval_s=0.01, start_at_end=False)
    lines = list(tail_new_lines(config_start, stop_after=0.2))
    assert "line-a" in lines
    assert "line-b" in lines
