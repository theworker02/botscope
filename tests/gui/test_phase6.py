"""Phase 6 anomaly + compare window + breakdown tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from botscope.classify.taxonomy import BotCategory
from botscope.gui.anomaly import compare_windows, detect_anomalies
from botscope.gui.breakdown import available_dimensions, breakdown
from botscope.normalize.event import NormalizedEvent


def _ev(cat: str, hour: int, ua: str = "Mozilla/5.0") -> NormalizedEvent:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return NormalizedEvent(
        timestamp=base + timedelta(hours=hour),
        classification=cat,
        user_agent=ua,
        path=f"/h{hour}",
        status=200,
        bytes_out=100,
        host="example.test",
    )


def test_detect_volume_anomaly() -> None:
    events = []
    # Steady baseline then a spike hour
    for h in range(10):
        n = 50 if h != 7 else 400
        for _ in range(n):
            events.append(_ev(BotCategory.HUMAN_LIKELY.value, h))
    findings = detect_anomalies(events, z_threshold=2.0)
    assert any(f.metric == "traffic_volume" for f in findings)


def test_compare_windows_pp_vs_relative() -> None:
    events = []
    for h in range(6):
        cat = BotCategory.HUMAN_LIKELY.value if h < 3 else BotCategory.VERIFIED_SEARCH_CRAWLER.value
        for _ in range(10):
            events.append(_ev(cat, h, ua="Mozilla/5.0 (compatible; Googlebot/2.1)"))
    timed = sorted(events, key=lambda e: e.timestamp)
    mid = len(timed) // 2
    a, b = timed[:mid], timed[mid:]
    result = compare_windows(
        events,
        start_a=a[0].timestamp,
        end_a=a[-1].timestamp,
        start_b=b[0].timestamp,
        end_b=b[-1].timestamp,
    )
    auto = next(r for r in result["rows"] if r["metric"] == "Automated")
    assert auto["percentage_point_change"] > 0
    assert "pp" in auto["display"]
    assert "percentage-point" in result["note"].lower() or "pp" in result["note"].lower()


def test_breakdown_dimensions() -> None:
    events = [
        _ev(BotCategory.VERIFIED_SEARCH_CRAWLER.value, 0, "Googlebot/2.1"),
        _ev(BotCategory.HUMAN_LIKELY.value, 1),
    ]
    dims = available_dimensions(events)
    assert "classification" in dims
    rows = breakdown(events, dimension="classification")
    assert sum(r.count for r in rows) == 2
    auto_rows = breakdown(events, dimension="classification", family="automated")
    assert sum(r.count for r in auto_rows) == 1
