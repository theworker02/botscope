"""Agent 2 + core smoke tests for provenance."""

from __future__ import annotations

from botscope.demo import iter_demo_events
from botscope.normalize.event import ProvenanceLevel
from botscope.provenance import claim_safe_totals, inspect_event, summarize_corpus


def test_inspect_event_and_summary():
    events = list(iter_demo_events())
    assert events
    report = inspect_event(events[0])
    assert report.event_id
    assert report.fields
    summary = summarize_corpus(events)
    assert summary.total_events == len(events)
    claims = claim_safe_totals(events)
    assert claims["observed_event_count"] == len(events)
    assert claims["provenance"]["counts"] == ProvenanceLevel.OBSERVED.value
