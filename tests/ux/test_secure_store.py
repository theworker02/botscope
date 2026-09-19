"""Hardened settings / secret vault tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

from botscope.ux import AppSettings, load_settings, save_settings
from botscope.ux.secure_store import load_secrets, vault_path


def test_token_sharded_out_of_settings_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    settings = AppSettings(
        theme="instrument",
        cloudflare_radar_token="cfut_test_secret_token_value_xxxxx",
    )
    save_settings(settings)

    settings_file = tmp_path / "settings.json"
    raw = json.loads(settings_file.read_text(encoding="utf-8"))
    assert "cloudflare_radar_token" not in raw
    assert vault_path(tmp_path).exists()

    loaded = load_settings()
    assert loaded.cloudflare_radar_token == "cfut_test_secret_token_value_xxxxx"
    assert loaded.theme == "instrument"


def test_migrate_plaintext_token_into_vault(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    # Simulate legacy plaintext settings
    (tmp_path / "settings.json").write_text(
        json.dumps(
            {
                "theme": "instrument",
                "cloudflare_radar_token": "cfut_legacy_plaintext",
            }
        ),
        encoding="utf-8",
    )
    loaded = load_settings()
    assert loaded.cloudflare_radar_token == "cfut_legacy_plaintext"
    # After load, plaintext should be migrated out
    raw = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert "cloudflare_radar_token" not in raw
    assert load_secrets(tmp_path).get("cloudflare_radar_token") == "cfut_legacy_plaintext"


def test_clearing_token_removes_vault_entry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_settings(AppSettings(cloudflare_radar_token="cfut_temp"))
    save_settings(AppSettings(cloudflare_radar_token=None))
    loaded = load_settings()
    assert not loaded.cloudflare_radar_token
    secrets = load_secrets(tmp_path)
    assert "cloudflare_radar_token" not in secrets


def test_posix_mode_when_not_windows(tmp_path: Path, monkeypatch) -> None:
    if os.name == "nt":
        # On Windows we rely on icacls; still ensure vault round-trips
        monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
        save_settings(AppSettings(cloudflare_radar_token="cfut_win"))
        assert load_settings().cloudflare_radar_token == "cfut_win"
        return
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_settings(AppSettings(cloudflare_radar_token="cfut_posix"))
    mode = (tmp_path / "settings.json").stat().st_mode & 0o777
    assert mode == 0o600
    vault_mode = vault_path(tmp_path).stat().st_mode & 0o777
    assert vault_mode == 0o600
