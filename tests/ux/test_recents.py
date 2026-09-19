"""Recent files + local settings UX."""

from __future__ import annotations

from pathlib import Path

from botscope.ux import (
    AppSettings,
    RecentFiles,
    classify_path,
    load_settings,
    save_settings,
)


def test_classify_path(tmp_path: Path) -> None:
    assert classify_path(tmp_path / "a.log") == "log"
    assert classify_path(tmp_path / "cap.pcap") == "pcap"
    assert classify_path(tmp_path / "cap.pcapng") == "pcap"
    session = tmp_path / "run.bscope"
    session.mkdir()
    (session / "events.jsonl").write_text("", encoding="utf-8")
    assert classify_path(session) == "session"
    assert classify_path(tmp_path / "notes.bin") == "other"


def test_recent_files_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    store = RecentFiles().load()
    log = tmp_path / "access.log"
    log.write_text("x", encoding="utf-8")
    store.remember(log, kind="log", label="access")
    again = RecentFiles().load()
    assert len(again.entries) == 1
    assert again.entries[0].kind == "log"
    assert again.existing()[0].path.endswith("access.log")


def test_settings_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    settings = AppSettings(
        theme="high_contrast",
        hash_ips=True,
        show_welcome=False,
        default_denominator="bytes",
    )
    save_settings(settings)
    loaded = load_settings()
    assert loaded.theme == "high_contrast"
    assert loaded.hash_ips is True
    assert loaded.show_welcome is False
    assert loaded.default_denominator == "bytes"
