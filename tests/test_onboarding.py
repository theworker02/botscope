"""Tests for first-run onboarding helpers."""

from __future__ import annotations

from pathlib import Path

from botscope.demo import DEMO_NOTICE
from botscope.onboarding import (
    HELLO_NEXT_STEPS,
    access_checklist,
    format_access_checklist,
    format_fraction,
    format_hello_summary,
    quickstart_guide,
    run_hello_analysis,
    top_categories,
)


def test_format_fraction():
    assert format_fraction(None) == "n/a"
    assert format_fraction(0.5) == "50.0%"
    assert format_fraction(0.1234, digits=2) == "12.34%"


def test_top_categories_ordering_and_limit():
    by_cat = {"B": 2, "A": 5, "C": 5, "D": 1}
    tops = top_categories(by_cat, limit=3)
    assert tops == [("A", 5), ("C", 5), ("B", 2)]
    assert top_categories({}, limit=5) == []
    assert top_categories(by_cat, limit=0) == []


def test_access_checklist_covers_key_paths():
    items = access_checklist()
    ids = {item["id"] for item in items}
    assert {
        "install_core",
        "install_gui",
        "hello",
        "zero_config",
        "data_locations",
        "open_gui",
        "disable_network",
        "doctor",
    }.issubset(ids)
    assert "pip install 'botscope[gui]'" in (
        next(i["detail"] for i in items if i["id"] == "install_gui")
    )
    text = format_access_checklist()
    assert "botscope hello" in text
    assert "OFF by default" in text
    assert "pip install botscope" in text
    # Rich escapes must still render extras literally when printed
    assert "botscope\\[gui]" in text or "botscope[gui]" in text


def test_quickstart_guide_richer_surface():
    text = quickstart_guide()
    for needle in (
        "botscope hello",
        "pip install",
        "botscope demo",
        "botscope analyze",
        "botscope gui",
        "botscope doctor",
        "Global Observatory",
        "Privacy defaults",
        "botscope access",
    ):
        assert needle in text


def test_run_hello_analysis_offline(tmp_path: Path):
    session = tmp_path / "hello.bscope"
    summary = run_hello_analysis(keep_session=session)
    assert summary["is_demo"] is True
    assert summary["offline"] is True
    assert summary["notice"] == DEMO_NOTICE
    assert summary["events"] > 0
    assert isinstance(summary["automation_fraction"], float)
    assert summary["top_categories"]
    assert summary["session_path"] is not None
    assert Path(summary["session_path"]).exists()
    assert summary["next_steps"] == list(HELLO_NEXT_STEPS)

    text = format_hello_summary(summary)
    assert "BotScope hello" in text
    assert "Events analyzed" in text
    assert "Next steps" in text


def test_run_hello_analysis_without_session():
    summary = run_hello_analysis(keep_session=None)
    assert summary["events"] > 0
    assert summary["session_path"] is None
