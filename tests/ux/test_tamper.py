"""Anti-tamper tripwire tests (no live secrets printed)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from botscope.ux import AppSettings, load_settings, save_settings
from botscope.ux.secure_store import encrypt_blob, save_secrets, vault_path
from botscope.ux.tamper import (
    CHEAT_MESSAGE,
    LOCKOUT_SECONDS,
    bootstrap_seal_if_needed,
    clear_lockout_if_requested,
    clear_trusted_vault,
    enforce_gui_security_gate,
    inspect_secret_store,
    lockout_path,
    read_lockout,
    remember_trusted_vault,
    seal_path,
    write_lockout,
)


@pytest.fixture(autouse=True)
def _reset_trusted_fp():
    clear_trusted_vault()
    yield
    clear_trusted_vault()


def test_legitimate_save_does_not_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_settings(AppSettings(cloudflare_radar_token="cfut_legit_token_aaaa"))
    assert seal_path(tmp_path).exists()
    verdict = inspect_secret_store(tmp_path)
    assert not verdict.tripped
    loaded = load_settings()
    assert loaded.cloudflare_radar_token == "cfut_legit_token_aaaa"
    # Second legitimate save still clean
    save_settings(AppSettings(cloudflare_radar_token="cfut_legit_token_bbbb", theme="instrument"))
    assert not inspect_secret_store(tmp_path).tripped
    assert "cloudflare_radar_token" not in json.loads(
        (tmp_path / "settings.json").read_text(encoding="utf-8")
    )


def test_vault_corruption_trips_after_seal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_seal_me"})
    assert seal_path(tmp_path).exists()
    vault_path(tmp_path).write_text("{not-json", encoding="utf-8")
    verdict = inspect_secret_store(tmp_path)
    assert verdict.tripped
    assert verdict.reason == "vault_corrupt"


def test_seal_mismatch_trips(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_original"})
    # Forge vault bytes while leaving old seal (unauthorized rewrite)
    forged = encrypt_blob(json.dumps({"cloudflare_radar_token": "cfut_forged"}).encode())
    vault_path(tmp_path).write_bytes(json.dumps(forged, indent=2).encode("utf-8"))
    verdict = inspect_secret_store(tmp_path)
    assert verdict.tripped
    assert verdict.reason == "seal_mismatch"


def test_plaintext_injection_trips(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_settings(AppSettings(cloudflare_radar_token="cfut_vault_value"))
    # Inject different plaintext into settings while vault exists
    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    settings["cloudflare_radar_token"] = "cfut_injected_other"
    (tmp_path / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    verdict = inspect_secret_store(tmp_path)
    assert verdict.tripped
    assert verdict.reason == "plaintext_injection"


def test_matching_plaintext_leftover_does_not_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_settings(AppSettings(cloudflare_radar_token="cfut_same"))
    settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    settings["cloudflare_radar_token"] = "cfut_same"
    (tmp_path / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    assert not inspect_secret_store(tmp_path).tripped
    # load migrates leftover out
    loaded = load_settings()
    assert loaded.cloudflare_radar_token == "cfut_same"
    raw = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert "cloudflare_radar_token" not in raw


def test_suspicious_metadata_trips(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_meta"})
    envelope = json.loads(vault_path(tmp_path).read_text(encoding="utf-8"))
    envelope["extra_probe"] = "exploit"
    vault_path(tmp_path).write_text(json.dumps(envelope), encoding="utf-8")
    verdict = inspect_secret_store(tmp_path)
    assert verdict.tripped
    assert verdict.reason == "suspicious_metadata"


def test_external_rewrite_trips_runtime_check(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_rt"})
    remember_trusted_vault(tmp_path)
    # Unauthorized rewrite of vault bytes while process holds prior fingerprint
    forged = encrypt_blob(json.dumps({"cloudflare_radar_token": "cfut_ext"}).encode())
    vault_path(tmp_path).write_bytes(json.dumps(forged, indent=2).encode("utf-8"))
    from botscope.ux.tamper import check_runtime_vault_rewrite

    verdict = check_runtime_vault_rewrite(tmp_path)
    assert verdict.tripped
    assert verdict.reason == "external_rewrite"
    # Subsequent legitimate-looking save must refuse and lock out
    with pytest.raises(SystemExit):
        save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_after"})
    assert lockout_path(tmp_path).exists()


def test_decrypt_failure_after_valid_seal_trips(tmp_path: Path, monkeypatch) -> None:
    import base64

    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_ok"})
    envelope = json.loads(vault_path(tmp_path).read_text(encoding="utf-8"))
    envelope["ciphertext_b64"] = base64.b64encode(b"tampered-not-valid-cipher").decode("ascii")
    vault_path(tmp_path).write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    verdict = inspect_secret_store(tmp_path)
    assert verdict.tripped
    assert verdict.reason in {"vault_decrypt_failed", "seal_mismatch"}


def test_lockout_blocks_gui_gate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    write_lockout(tmp_path, seconds=LOCKOUT_SECONDS)
    assert read_lockout(tmp_path).active
    with pytest.raises(SystemExit):
        enforce_gui_security_gate(tmp_path)
    # Clear via env
    monkeypatch.setenv("BOTSCOPE_CLEAR_LOCKOUT", "1")
    assert clear_lockout_if_requested(tmp_path)
    assert not read_lockout(tmp_path).active
    # Clean store should pass gate
    enforce_gui_security_gate(tmp_path)


def test_trip_writes_lockout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    save_secrets(tmp_path, {"cloudflare_radar_token": "cfut_trip"})
    vault_path(tmp_path).write_text("CORRUPT", encoding="utf-8")
    with pytest.raises(SystemExit) as ei:
        enforce_gui_security_gate(tmp_path)
    assert CHEAT_MESSAGE in str(ei.value)
    assert lockout_path(tmp_path).exists()
    state = read_lockout(tmp_path)
    assert state.active
    assert 1 <= state.remaining_seconds <= LOCKOUT_SECONDS


def test_bootstrap_seal_for_existing_vault(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    # Write vault without seal (upgrade path)
    from botscope.ux.secure_store import encrypt_blob as enc

    raw = json.dumps({"cloudflare_radar_token": "cfut_upgrade"}).encode()
    sealed = enc(raw)
    vault_path(tmp_path).write_bytes(json.dumps(sealed, indent=2).encode())
    assert not seal_path(tmp_path).exists()
    assert not inspect_secret_store(tmp_path).tripped
    bootstrap_seal_if_needed(tmp_path)
    assert seal_path(tmp_path).exists()
    assert not inspect_secret_store(tmp_path).tripped


def test_lockout_expires(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BOTSCOPE_UX_DIR", str(tmp_path))
    path = lockout_path(tmp_path)
    path.write_text(
        json.dumps({"v": 1, "until_epoch": time.time() - 1, "seconds": 110}),
        encoding="utf-8",
    )
    assert not read_lockout(tmp_path).active
