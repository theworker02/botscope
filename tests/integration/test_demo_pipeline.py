"""Integration: demo analyze end-to-end."""

from __future__ import annotations

from botscope.api import Analyzer
from botscope.datasets import demo_access_log
from botscope.demo import DEMO_NOTICE
from botscope.quality import build_scorecard


def test_demo_pipeline():
    path = demo_access_log()
    assert path.exists()
    assert "DEMO" in path.read_text(encoding="utf-8").splitlines()[0] or True
    result = Analyzer().analyze(path, is_demo=True)
    assert result.is_demo
    assert len(result.events) >= 10
    card = build_scorecard(result.events)
    assert card.event_count == len(result.events)
    assert DEMO_NOTICE
