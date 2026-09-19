"""Geo aggregate tests."""

from __future__ import annotations

from datetime import datetime, timezone

from botscope.geo import GEO_CAVEAT, aggregate_geo
from botscope.normalize.event import NormalizedEvent, SourceType


def test_aggregate_geo_counts_and_caveat() -> None:
    events = [
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.WEB_LOG,
            extras={"country": "us"},
        ),
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.WEB_LOG,
            extras={"country_code": "DE"},
        ),
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.WEB_LOG,
        ),
    ]
    agg = aggregate_geo(events)
    assert agg.tagged_events == 2
    assert agg.untagged_events == 1
    assert agg.by_country["US"] == 1
    assert agg.by_country["DE"] == 1
    assert "not the physical location" in GEO_CAVEAT.lower() or "not" in agg.caveat.lower()
