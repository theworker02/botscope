"""Session history index tests."""

from __future__ import annotations

from pathlib import Path

from botscope.history import SessionHistory


def test_history_remember_and_recent(tmp_path: Path, monkeypatch) -> None:
    hist_path = tmp_path / "recent.json"
    monkeypatch.setenv("BOTSCOPE_HISTORY_PATH", str(hist_path))
    session = tmp_path / "demo.bscope"
    session.mkdir()
    h = SessionHistory(path=hist_path, max_entries=5)
    h.remember(session, label="demo", event_count=10, is_demo=True)
    h.remember(session, label="demo2", event_count=12, is_demo=True)
    recent = h.load().recent()
    assert len(recent) == 1  # same path deduped to MRU
    assert recent[0].event_count == 12
    assert recent[0].is_demo is True
