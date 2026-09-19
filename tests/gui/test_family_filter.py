"""Family filter click-through semantics for GuiSession."""

from __future__ import annotations

from datetime import datetime, timezone

from botscope.api.analyzer import AnalysisResult
from botscope.classify.taxonomy import BotCategory
from botscope.gui.session_state import GuiSession
from botscope.normalize.event import NormalizedEvent
from botscope.statistics.aggregate import aggregate_events


def _make_session() -> GuiSession:
    events = [
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            classification=BotCategory.VERIFIED_SEARCH_CRAWLER.value,
            path="/a",
        ),
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            classification=BotCategory.HUMAN_LIKELY.value,
            path="/b",
        ),
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            classification=BotCategory.UNKNOWN.value,
            path="/c",
        ),
    ]
    stats = aggregate_events(events, is_demo=True)
    session = GuiSession()
    session.result = AnalysisResult(events=events, stats=stats, is_demo=True)
    session.is_demo = True
    return session


def test_family_filter_automated() -> None:
    session = _make_session()
    session.filter_category = "automated"
    assert len(session.filtered_events()) == 1
    assert session.filtered_events()[0].classification == BotCategory.VERIFIED_SEARCH_CRAWLER.value


def test_family_filter_unknown() -> None:
    session = _make_session()
    session.filter_category = "unknown"
    assert len(session.filtered_events()) == 1
