"""GUI unit tests — offscreen Qt, no interactive window required."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from botscope.api.analyzer import Analyzer
from botscope.demo import ensure_demo_log
from botscope.gui.main_window import ObservatoryWindow
from botscope.gui.session_state import GuiSession
from botscope.gui.theme import STYLESHEET
from botscope.gui.widgets import TimelineChart, fmt_pct


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setStyleSheet(STYLESHEET)
    return app


def test_fmt_pct() -> None:
    assert fmt_pct(None) == "—"
    assert fmt_pct(0.374) == "37.4%"


def test_timeline_accepts_series(qapp) -> None:
    chart = TimelineChart()
    chart.set_series([("2026-09-18T10:00", 10, 4, 5)])
    assert len(chart._series) == 1


def test_session_filter() -> None:
    path = ensure_demo_log()
    result = Analyzer().analyze(path, is_demo=True)
    session = GuiSession(source_path=path, result=result, is_demo=True)
    session.filter_category = "AI CRAWLER"
    filtered = session.filtered_events()
    assert all((e.classification or "") == "AI CRAWLER" for e in filtered)


def test_observatory_window_loads_demo(qapp) -> None:
    win = ObservatoryWindow()
    path = ensure_demo_log()
    result = Analyzer().analyze(path, is_demo=True)
    win.session.source_path = path
    win.session.is_demo = True
    win.session.result = result
    win._refresh_all()
    assert win.session.loaded
    assert win.session.is_demo
    assert not win.observatory.demo_banner.isHidden()
    win.close()
