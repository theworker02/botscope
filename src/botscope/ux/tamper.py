"""Anti-tamper tripwire for BotScope secret store (GUI gate).

Detects vault forgery, ciphertext corruption, unauthorized rewrite, and
post-migration plaintext secret injection. On trip: persist a 110s lockout
under the UX dir, show a firm message, and refuse GUI launch.

Legitimate Settings UI / save_settings paths update the integrity seal and
must not trip this detector. CLI analysis commands are not gated.

Developer: set BOTSCOPE_CLEAR_LOCKOUT=1 to clear an active lockout.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from botscope.ux.secure_store import (
    SECRET_FIELDS,
    decrypt_blob,
    encrypt_blob,
    lockdown_path,
    vault_path,
)

LOCKOUT_SECONDS = 110
CHEAT_MESSAGE = "You have been detected cheating. Shutting down."
LOCKOUT_MESSAGE = (
    "BotScope is locked after a security trip. Try again in {seconds}s."
)

TripReason = Literal[
    "vault_corrupt",
    "vault_decrypt_failed",
    "seal_mismatch",
    "seal_corrupt",
    "suspicious_metadata",
    "plaintext_injection",
    "external_rewrite",
]


@dataclass(frozen=True)
class TamperVerdict:
    tripped: bool
    reason: TripReason | None = None
    detail: str = ""


@dataclass(frozen=True)
class LockoutState:
    active: bool
    until_epoch: float = 0.0
    remaining_seconds: int = 0


# In-process fingerprint of the last trusted vault (path + sha256).
_trusted_vault_path: str | None = None
_trusted_vault_fp: str | None = None


def lockout_path(ux_dir: Path) -> Path:
    return Path(ux_dir) / "security.lockout"


def seal_path(ux_dir: Path) -> Path:
    return Path(ux_dir) / "secrets.seal"


def clear_lockout_if_requested(ux_dir: Path) -> bool:
    """If BOTSCOPE_CLEAR_LOCKOUT is set, remove lockout file. Returns True if cleared."""
    flag = (os.environ.get("BOTSCOPE_CLEAR_LOCKOUT") or "").strip().lower()
    if flag not in {"1", "true", "yes"}:
        return False
    path = lockout_path(ux_dir)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            return False
    return True


def read_lockout(ux_dir: Path) -> LockoutState:
    path = lockout_path(ux_dir)
    if not path.exists():
        return LockoutState(active=False)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        until = float(raw.get("until_epoch") or 0.0)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return LockoutState(active=False)
    now = time.time()
    if now >= until:
        try:
            path.unlink()
        except OSError:
            pass
        return LockoutState(active=False)
    return LockoutState(
        active=True,
        until_epoch=until,
        remaining_seconds=max(1, int(until - now + 0.999)),
    )


def write_lockout(ux_dir: Path, *, seconds: int = LOCKOUT_SECONDS) -> float:
    ux_dir = Path(ux_dir)
    ux_dir.mkdir(parents=True, exist_ok=True)
    until = time.time() + seconds
    path = lockout_path(ux_dir)
    path.write_text(
        json.dumps(
            {
                "v": 1,
                "until_epoch": until,
                "seconds": seconds,
                "message": CHEAT_MESSAGE,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    lockdown_path(path)
    lockdown_path(ux_dir)
    return until


def vault_fingerprint(vault_bytes: bytes) -> str:
    return hashlib.sha256(vault_bytes).hexdigest()


def remember_trusted_vault(ux_dir: Path) -> None:
    """Record current vault bytes as trusted for runtime rewrite detection."""
    global _trusted_vault_path, _trusted_vault_fp
    path = vault_path(ux_dir)
    if not path.exists():
        _trusted_vault_path = None
        _trusted_vault_fp = None
        return
    try:
        _trusted_vault_path = str(path.resolve())
        _trusted_vault_fp = vault_fingerprint(path.read_bytes())
    except OSError:
        _trusted_vault_path = None
        _trusted_vault_fp = None


def mark_trusted_vault_bytes(data: bytes, ux_dir: Path | None = None) -> None:
    global _trusted_vault_path, _trusted_vault_fp
    _trusted_vault_fp = vault_fingerprint(data)
    if ux_dir is not None:
        _trusted_vault_path = str(vault_path(ux_dir).resolve())


def clear_trusted_vault() -> None:
    global _trusted_vault_path, _trusted_vault_fp
    _trusted_vault_path = None
    _trusted_vault_fp = None


def write_integrity_seal(ux_dir: Path, vault_bytes: bytes, envelope: dict[str, Any]) -> None:
    """Write DPAPI/0600-sealed integrity record for the vault ciphertext."""
    ux_dir = Path(ux_dir)
    payload = {
        "v": 1,
        "vault_sha256": vault_fingerprint(vault_bytes),
        "alg": envelope.get("alg"),
        "envelope_v": envelope.get("v"),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sealed = encrypt_blob(raw)
    path = seal_path(ux_dir)
    path.write_bytes(json.dumps(sealed, indent=2).encode("utf-8"))
    lockdown_path(path)
    mark_trusted_vault_bytes(vault_bytes, ux_dir)


def _load_seal(ux_dir: Path) -> tuple[dict[str, Any] | None, Literal["missing", "ok", "bad"]]:
    path = seal_path(ux_dir)
    if not path.exists():
        return None, "missing"
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(envelope, dict):
            return None, "bad"
        raw = decrypt_blob(envelope)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict) or "vault_sha256" not in data:
            return None, "bad"
        return data, "ok"
    except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
        return None, "bad"


def _inspect_vault_envelope(raw_text: str) -> tuple[dict[str, Any] | None, TripReason | None]:
    try:
        envelope = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, "vault_corrupt"
    if not isinstance(envelope, dict):
        return None, "vault_corrupt"
    allowed = {"v", "alg", "ciphertext_b64"}
    if set(envelope.keys()) - allowed:
        return None, "suspicious_metadata"
    if envelope.get("v") != 1:
        return None, "suspicious_metadata"
    if envelope.get("alg") not in {"dpapi", "plain_0600"}:
        return None, "suspicious_metadata"
    if not isinstance(envelope.get("ciphertext_b64"), str) or not envelope["ciphertext_b64"]:
        return None, "suspicious_metadata"
    return envelope, None


def _plaintext_injection(ux_dir: Path, vault_secrets: dict[str, Any]) -> bool:
    settings = Path(ux_dir) / "settings.json"
    if not settings.exists() or not vault_secrets:
        return False
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(data, dict):
        return False
    for key in SECRET_FIELDS:
        if key not in data:
            continue
        embedded = data.get(key)
        if embedded is None or embedded == "":
            continue
        vault_val = vault_secrets.get(key)
        if vault_val is None:
            continue
        # After migration, leftover identical plaintext is stale — not an exploit.
        if embedded != vault_val:
            return True
    return False


def inspect_secret_store(ux_dir: Path) -> TamperVerdict:
    """Inspect vault/seal/settings for tamper signals. Does not write lockout."""
    ux_dir = Path(ux_dir)
    vpath = vault_path(ux_dir)

    if not vpath.exists():
        # No vault — nothing sealed yet; plaintext migration is allowed elsewhere.
        return TamperVerdict(tripped=False)

    try:
        vault_bytes = vpath.read_bytes()
        raw_text = vault_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return TamperVerdict(tripped=True, reason="vault_corrupt", detail="unreadable vault")

    envelope, meta_reason = _inspect_vault_envelope(raw_text)
    if meta_reason:
        return TamperVerdict(tripped=True, reason=meta_reason, detail="vault envelope")

    seal, seal_status = _load_seal(ux_dir)
    try:
        assert envelope is not None
        plain = decrypt_blob(envelope)
        secrets = json.loads(plain.decode("utf-8"))
        if not isinstance(secrets, dict):
            return TamperVerdict(tripped=True, reason="vault_corrupt", detail="secrets not object")
    except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
        if seal_status == "ok":
            return TamperVerdict(
                tripped=True,
                reason="vault_decrypt_failed",
                detail="decrypt failed after prior valid seal",
            )
        # No prior seal: treat as unusable vault without trip (bootstrap edge).
        return TamperVerdict(tripped=False)

    if seal_status == "bad":
        return TamperVerdict(tripped=True, reason="seal_corrupt", detail="integrity seal broken")

    if seal_status == "ok":
        assert seal is not None
        expected = seal.get("vault_sha256")
        actual = vault_fingerprint(vault_bytes)
        if expected != actual:
            return TamperVerdict(tripped=True, reason="seal_mismatch", detail="vault hash mismatch")
        if seal.get("alg") and seal.get("alg") != envelope.get("alg"):
            return TamperVerdict(
                tripped=True, reason="suspicious_metadata", detail="seal alg mismatch"
            )

    if _plaintext_injection(ux_dir, secrets):
        return TamperVerdict(
            tripped=True,
            reason="plaintext_injection",
            detail="settings.json secret conflicts with vault",
        )

    # Runtime: unauthorized rewrite since last trusted remember (same vault path).
    global _trusted_vault_path, _trusted_vault_fp
    try:
        resolved = str(vpath.resolve())
    except OSError:
        resolved = str(vpath)
    if (
        _trusted_vault_fp is not None
        and _trusted_vault_path is not None
        and resolved == _trusted_vault_path
        and vault_fingerprint(vault_bytes) != _trusted_vault_fp
    ):
        return TamperVerdict(
            tripped=True, reason="external_rewrite", detail="vault changed outside app"
        )

    return TamperVerdict(tripped=False)


def bootstrap_seal_if_needed(ux_dir: Path) -> None:
    """After a clean inspect, ensure an integrity seal exists for a valid vault."""
    ux_dir = Path(ux_dir)
    vpath = vault_path(ux_dir)
    if not vpath.exists():
        remember_trusted_vault(ux_dir)
        return
    if seal_path(ux_dir).exists():
        remember_trusted_vault(ux_dir)
        return
    try:
        vault_bytes = vpath.read_bytes()
        envelope, reason = _inspect_vault_envelope(vault_bytes.decode("utf-8"))
        if reason or envelope is None:
            return
        decrypt_blob(envelope)  # must decrypt
        write_integrity_seal(ux_dir, vault_bytes, envelope)
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return


def check_runtime_vault_rewrite(ux_dir: Path) -> TamperVerdict:
    """Trip if vault bytes changed since the last trusted load/save in this process."""
    global _trusted_vault_path, _trusted_vault_fp
    if _trusted_vault_fp is None or _trusted_vault_path is None:
        return TamperVerdict(tripped=False)
    path = vault_path(ux_dir)
    try:
        resolved = str(path.resolve())
    except OSError:
        resolved = str(path)
    # Different UX directory (e.g. tests) — not an in-process rewrite of this vault.
    if resolved != _trusted_vault_path:
        return TamperVerdict(tripped=False)
    if not path.exists():
        return TamperVerdict(
            tripped=True, reason="external_rewrite", detail="vault removed externally"
        )
    try:
        current = vault_fingerprint(path.read_bytes())
    except OSError:
        return TamperVerdict(tripped=True, reason="vault_corrupt", detail="vault unreadable")
    if current != _trusted_vault_fp:
        return TamperVerdict(
            tripped=True, reason="external_rewrite", detail="vault changed outside app"
        )
    return TamperVerdict(tripped=False)


def _show_message(text: str) -> None:
    print(text, file=sys.stderr)
    # Avoid blocking modal dialogs under pytest / offscreen CI.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    if (os.environ.get("QT_QPA_PLATFORM") or "").strip().lower() == "offscreen":
        return
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance()
        created = False
        if app is None:
            app = QApplication(sys.argv if hasattr(sys, "argv") else [])
            created = True
        box = QMessageBox()
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("BotScope Security")
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()
        if created:
            app.quit()
    except Exception:
        pass


def enforce_gui_security_gate(ux_dir: Path | None = None) -> None:
    """Gate GUI launch: honor lockout, inspect store, trip+exit on tamper.

    Call before constructing the main window. Does not gate CLI subcommands.
    """
    if ux_dir is None:
        from botscope.ux.recents import _ux_dir

        ux_dir = _ux_dir()
    ux_dir = Path(ux_dir)

    clear_lockout_if_requested(ux_dir)

    lock = read_lockout(ux_dir)
    if lock.active:
        msg = LOCKOUT_MESSAGE.format(seconds=lock.remaining_seconds)
        _show_message(msg)
        raise SystemExit(msg)

    verdict = inspect_secret_store(ux_dir)
    if verdict.tripped:
        write_lockout(ux_dir)
        _show_message(CHEAT_MESSAGE)
        raise SystemExit(CHEAT_MESSAGE)

    bootstrap_seal_if_needed(ux_dir)
    remember_trusted_vault(ux_dir)


def trip_and_exit(ux_dir: Path, *, reason: TripReason | None = None) -> None:
    """Record lockout and terminate (used when runtime rewrite is detected)."""
    del reason  # retained for call-site clarity / future logging
    write_lockout(ux_dir)
    _show_message(CHEAT_MESSAGE)
    raise SystemExit(CHEAT_MESSAGE)
