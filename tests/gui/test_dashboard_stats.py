"""Phase 5 dashboard statistics tests (no Qt)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from botscope.classify.taxonomy import BotCategory
from botscope.gui.dashboard_stats import (
    build_traffic_pulse,
    composition_from_stats,
    confidence_distribution,
    explain_composition,
    metric_provenance,
    top_automated_actors,
)
from botscope.normalize.event import NormalizedEvent
from botscope.statistics.aggregate import aggregate_events


def _ev(
    *,
    cat: str,
    conf: float = 0.9,
    ua: str = "Mozilla/5.0",
    ts: datetime | None = None,
    bytes_out: int = 100,
) -> NormalizedEvent:
    return NormalizedEvent(
        timestamp=ts or datetime.now(timezone.utc),
        src_address="1.2.3.4",
        user_agent=ua,
        path="/",
        status=200,
        bytes_out=bytes_out,
        classification=cat,
        confidence=conf,
    )


def test_composition_requests_denominator() -> None:
    events = [
        _ev(cat=BotCategory.VERIFIED_SEARCH_CRAWLER.value),
        _ev(cat=BotCategory.VERIFIED_SEARCH_CRAWLER.value),
        _ev(cat=BotCategory.HUMAN_LIKELY.value),
        _ev(cat=BotCategory.UNKNOWN.value),
    ]
    stats = aggregate_events(events, is_demo=True)
    comp = composition_from_stats(stats, denominator="requests")
    assert comp.total == 4
    assert abs(comp.automated - 0.5) < 1e-9
    assert abs(comp.human_likely - 0.25) < 1e-9
    assert abs(comp.unknown - 0.25) < 1e-9


def test_composition_bytes_denominator() -> None:
    events = [
        _ev(cat=BotCategory.VERIFIED_SEARCH_CRAWLER.value, bytes_out=700),
        _ev(cat=BotCategory.HUMAN_LIKELY.value, bytes_out=300),
    ]
    stats = aggregate_events(events, is_demo=True)
    comp = composition_from_stats(stats, denominator="bytes")
    assert comp.total == 1000
    assert abs(comp.automated - 0.7) < 1e-9
    assert abs(comp.human_likely - 0.3) < 1e-9


def test_percentage_point_pulse() -> None:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events = []
    for i in range(6):
        cat = (
            BotCategory.HUMAN_LIKELY.value
            if i < 3
            else BotCategory.VERIFIED_SEARCH_CRAWLER.value
        )
        events.append(_ev(cat=cat, ts=base + timedelta(hours=i)))
    pulse = build_traffic_pulse(events, denominator="requests")
    assert pulse.auto_pp_delta is not None
    assert pulse.auto_pp_delta > 0  # second half more automated
    joined = " ".join(pulse.summary_lines)
    assert "pp" in joined


def test_confidence_buckets() -> None:
    events = [
        _ev(cat=BotCategory.UNKNOWN.value, conf=0.95),
        _ev(cat=BotCategory.UNKNOWN.value, conf=0.75),
        _ev(cat=BotCategory.UNKNOWN.value, conf=0.2),
    ]
    buckets = dict(confidence_distribution(events))
    assert buckets["Very high"] == 1
    assert buckets["High"] == 1
    assert buckets["Low"] == 0
    assert buckets["Unresolved"] == 1


def test_explain_and_provenance() -> None:
    events = [
        _ev(
            cat=BotCategory.VERIFIED_SEARCH_CRAWLER.value,
            ua="Mozilla/5.0 (compatible; Googlebot/2.1)",
        )
    ]
    stats = aggregate_events(events, is_demo=True)
    comp = composition_from_stats(stats)
    actors = top_automated_actors(events)
    text = explain_composition(comp, actors)
    assert "Automated traffic represents" in text
    prov = metric_provenance(
        metric="Automated request share",
        numerator=comp.automated_count,
        denominator=comp.total,
        denominator_label="eligible requests",
        sources=["demo"],
        filters=[],
        time_range="all",
        ruleset_version="test",
        is_demo=True,
    )
    assert prov["numerator"] == 1
    assert prov["is_demo"] is True
