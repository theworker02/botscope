"""Quality scorecard tests."""

from __future__ import annotations

from botscope.api import Analyzer
from botscope.demo import ensure_demo_log
from botscope.quality import build_scorecard


def test_scorecard_has_multiple_dimensions_no_overall_pct():
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    card = build_scorecard(result.events)
    data = card.to_dict()
    assert "overall" not in data
    assert "overall_percent" not in data
    assert len(data["dimensions"]) >= 5
    names = {d["name"] for d in data["dimensions"]}
    assert "completeness" in names
    assert "evidence_coverage" in names
    assert "No single overall" in data["policy"]
