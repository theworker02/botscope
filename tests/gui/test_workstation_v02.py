"""GUI v0.2 tests — virtualized model, session filters with query, snapshots."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from botscope.api.analyzer import Analyzer
from botscope.demo import ensure_demo_log
from botscope.gui.events_model import EventsTableModel
from botscope.gui.main_window import ObservatoryWindow
from botscope.gui.session_state import GuiSession
from botscope.gui.theme import STYLESHEET
from botscope.live import StreamingAggregator
from botscope.normalize.event import NormalizedEvent


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setStyleSheet(STYLESHEET)
    return app


def test_events_table_model_virtualized(qapp) -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    model = EventsTableModel()
    model.set_events(result.events)
    assert model.rowCount() == len(result.events)
    assert model.columnCount() == 6
    idx = model.index(0, 1)
    assert model.data(idx) is not None
    assert model.event_id_at(0)


def test_session_query_filter() -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    session = GuiSession(source_path=ensure_demo_log(), result=result, is_demo=True)
    session.query = 'classification eq "AI CRAWLER"'
    filtered = session.filtered_events()
    assert filtered
    assert all((e.classification or "") == "AI CRAWLER" for e in filtered)


def test_observatory_apply_snapshot(qapp) -> None:
    win = ObservatoryWindow()
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    agg = StreamingAggregator(max_hz=50.0, is_demo=True)
    agg.ingest(result.events[:20])
    snap = agg.snapshot()
    win.observatory.apply_snapshot(snap)
    assert snap.total_events >= 1
    assert "events" in win.observatory.tile_events.value_label.text().lower() or win.observatory.tile_events.value_label.text() != "—"
    # Tabs include Compare / Live / History
    titles = [win.tabs.tabText(i) for i in range(win.tabs.count())]
    assert "Compare" in titles
    assert "Live" in titles
    assert "History" in titles
    win.close()


def test_workspace_roundtrip_on_session() -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    session = GuiSession(result=result, is_demo=True, denominator="bytes", query="status eq 200")
    ws = session.to_workspace()
    other = GuiSession(result=result)
    other.apply_workspace(ws)
    assert other.denominator == "bytes"
    assert other.query == "status eq 200"
