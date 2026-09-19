"""Preset persistence tests."""

from __future__ import annotations

from botscope.gui.presets import (
    BUILTIN_PRESETS,
    AnalysisPreset,
    load_presets,
    save_presets,
)


def test_builtin_presets_exist(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    # Force path under tmp via monkeypatch of presets_path parent
    from botscope.gui import presets as presets_mod

    monkeypatch.setattr(presets_mod, "presets_path", lambda: tmp_path / "presets.json")
    loaded = load_presets()
    assert len(loaded) >= len(BUILTIN_PRESETS)
    custom = AnalysisPreset("My view", denominator="bytes", filters={"family": "automated"})
    save_presets([custom])
    again = load_presets()
    assert again[0].name == "My view"
    assert again[0].denominator == "bytes"


def test_malformed_presets_fallback(tmp_path, monkeypatch) -> None:
    from botscope.gui import presets as presets_mod

    path = tmp_path / "presets.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(presets_mod, "presets_path", lambda: path)
    loaded = load_presets()
    assert len(loaded) == len(BUILTIN_PRESETS)
