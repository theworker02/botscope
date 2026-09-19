"""Hardened local secret storage — ACL lockdown + DPAPI (Windows) / 0600 (POSIX).

Sensitive values (e.g. Cloudflare Radar token) are sharded out of settings.json
into an encrypted vault file under the user BotScope config directory.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
from pathlib import Path
from typing import Any

SECRET_FIELDS = frozenset({"cloudflare_radar_token"})


def vault_path(ux_dir: Path) -> Path:
    return ux_dir / "secrets.vault"


def lockdown_path(path: Path) -> None:
    """Restrict a file or directory to the current user only."""
    path = Path(path)
    if not path.exists():
        return
    if os.name == "nt":
        _lockdown_windows(path)
    else:
        mode = 0o700 if path.is_dir() else 0o600
        try:
            os.chmod(path, mode)
        except OSError:
            pass


def _lockdown_windows(path: Path) -> None:
    """Remove inherited ACLs; grant full control only to the current user."""
    try:
        who = subprocess.run(
            ["whoami"],
            check=False,
            capture_output=True,
            text=True,
        )
        user = (who.stdout or "").strip()
        if not user:
            user = os.environ.get("USERNAME") or ""
        if not user:
            return
        # Ensure current user can access BEFORE stripping inheritance
        subprocess.run(
            ["icacls", str(path), "/grant", f"{user}:(F)"],
            check=False,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["icacls", str(path), "/inheritance:r"],
            check=False,
            capture_output=True,
            text=True,
        )
        # Replace ACLs with current-user full control only
        subprocess.run(
            ["icacls", str(path), "/grant:r", f"{user}:(F)"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        pass


def _dpapi_protect(raw: bytes) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    blob_in = DATA_BLOB(len(raw), ctypes.create_string_buffer(raw, len(raw)))
    blob_out = DATA_BLOB()
    if not crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        "BotScope",
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise OSError("CryptProtectData failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        kernel32.LocalFree(blob_out.pbData)


def _dpapi_unprotect(protected: bytes) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    buf = ctypes.create_string_buffer(protected, len(protected))
    blob_in = DATA_BLOB(len(protected), buf)
    blob_out = DATA_BLOB()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise OSError("CryptUnprotectData failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        kernel32.LocalFree(blob_out.pbData)


def encrypt_blob(raw: bytes) -> dict[str, str]:
    """Return a JSON-serializable sealed payload."""
    if os.name == "nt":
        sealed = _dpapi_protect(raw)
        return {
            "v": 1,
            "alg": "dpapi",
            "ciphertext_b64": base64.b64encode(sealed).decode("ascii"),
        }
    # POSIX: no DPAPI — store obfuscated only under 0600 (not crypto-strong alone)
    return {
        "v": 1,
        "alg": "plain_0600",
        "ciphertext_b64": base64.b64encode(raw).decode("ascii"),
    }


def decrypt_blob(payload: dict[str, Any]) -> bytes:
    alg = payload.get("alg")
    data = base64.b64decode(payload["ciphertext_b64"])
    if alg == "dpapi":
        return _dpapi_unprotect(data)
    if alg == "plain_0600":
        return data
    raise ValueError(f"unknown vault alg: {alg}")


def save_secrets(ux_dir: Path, secrets: dict[str, Any]) -> None:
    """Write encrypted secrets vault, integrity seal, and lockdown ACLs.

    Legitimate Settings / save_settings calls go through here and refresh the
    tamper seal so they do not trip botscope.ux.tamper.
    """
    from botscope.ux.tamper import (
        check_runtime_vault_rewrite,
        clear_trusted_vault,
        seal_path,
        trip_and_exit,
        write_integrity_seal,
    )

    ux_dir = Path(ux_dir)
    ux_dir.mkdir(parents=True, exist_ok=True)
    lockdown_path(ux_dir)

    # Detect unauthorized vault rewrite since last trusted load/save.
    rewrite = check_runtime_vault_rewrite(ux_dir)
    if rewrite.tripped:
        trip_and_exit(ux_dir, reason=rewrite.reason)

    clean = {k: v for k, v in secrets.items() if v is not None and v != ""}
    path = vault_path(ux_dir)
    if not clean:
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        seal = seal_path(ux_dir)
        if seal.exists():
            try:
                seal.unlink()
            except OSError:
                pass
        clear_trusted_vault()
        return
    raw = json.dumps(clean, separators=(",", ":")).encode("utf-8")
    sealed = encrypt_blob(raw)
    vault_bytes = json.dumps(sealed, indent=2).encode("utf-8")
    path.write_bytes(vault_bytes)
    lockdown_path(path)
    write_integrity_seal(ux_dir, vault_bytes, sealed)


def load_secrets(ux_dir: Path) -> dict[str, Any]:
    path = vault_path(ux_dir)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = decrypt_blob(payload)
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
        return {}


def split_settings_dict(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Shard secret fields out of a settings dict."""
    public = dict(data)
    secrets: dict[str, Any] = {}
    for key in SECRET_FIELDS:
        if key in public:
            val = public.pop(key)
            if val is not None and val != "":
                secrets[key] = val
    return public, secrets


def merge_secrets(public: dict[str, Any], secrets: dict[str, Any]) -> dict[str, Any]:
    out = dict(public)
    for key in SECRET_FIELDS:
        if key in secrets:
            out[key] = secrets[key]
    return out
