"""Theme + motion unit tests (offscreen Qt)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel

from botscope.gui.motion import fade_in, pulse_opacity, reduce_motion, set_reduce_motion
from botscope.gui.theme import chart_colors, set_chart_theme, stylesheet_for


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_stylesheet_for_themes() -> None:
    instrument = stylesheet_for("instrument")
    contrast = stylesheet_for("high_contrast")
    assert "primaryButton" in instrument
    assert "ghostButton" in instrument
    assert "#ffff00" in contrast
    assert "primaryButton" in contrast


def test_chart_theme_switch() -> None:
    set_chart_theme("instrument")
    assert chart_colors()["auto"] == "#2f6f6b"
    set_chart_theme("high_contrast")
    assert chart_colors()["paper"] == "#000000"
    set_chart_theme("instrument")


def test_reduce_motion_skips_animations(qapp) -> None:
    set_reduce_motion(True)
    assert reduce_motion() is True
    label = QLabel("x")
    assert fade_in(label) is None
    assert pulse_opacity(label) is None
    set_reduce_motion(False)
    assert fade_in(label) is not None


def test_stylesheet_covers_new_chrome() -> None:
    sheet = stylesheet_for("instrument")
    for token in ("navChrome", "brandWordmark", "pageHeader", "zeroConfigBanner", "emptyState"):
        assert token in sheet
    contrast = stylesheet_for("high_contrast")
    assert "brandWordmark" in contrast
    assert "#ffff00" in contrast
