"""Session save/load + SessionStore additive API tests."""

from __future__ import annotations

from pathlib import Path

from botscope.api.analyzer import Analyzer
from botscope.demo import ensure_demo_log
from botscope.gui.session_io import load_analysis_session, save_analysis_session
from botscope.storage import SessionStore
from botscope.workspace import AnalysisWorkspace


def test_save_and_load_bscope(tmp_path: Path) -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    target = tmp_path / "roundtrip.bscope"
    ws = AnalysisWorkspace(denominator="bytes", query='status eq 200')
    saved = save_analysis_session(
        target,
        result.events,
        source_path=ensure_demo_log(),
        is_demo=True,
        workspace=ws,
        remember=False,
    )
    assert saved.path.exists()
    assert (saved.path / "events.jsonl").exists()
    assert (saved.path / "workspace.json").exists()
    assert saved.meta is not None
    assert saved.meta.is_demo is True
    assert saved.meta.classifier_version

    loaded = load_analysis_session(target, remember=False)
    assert len(loaded.result.events) == len(result.events)
    assert loaded.workspace.denominator == "bytes"
    assert loaded.result.is_demo is True


def test_session_store_summary_and_list(tmp_path: Path) -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True, output=tmp_path / "out.bscope")
    store = SessionStore(result.session_path)
    try:
        summary = store.summary()
        assert summary["event_count"] == len(result.events)
        assert summary["is_demo"] is True
        sessions = store.list_sessions()
        assert len(sessions) >= 1
        doc = {"denominator": "requests"}
        store.save_workspace_document(doc)
        assert store.load_workspace_document()["denominator"] == "requests"
    finally:
        store.close()
