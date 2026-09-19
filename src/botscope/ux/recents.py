"""Ease-of-access UX helpers — recent files and local preferences.

Status: IMPLEMENTED
Local only; never uploaded.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


def _ux_dir() -> Path:
    override = os.environ.get("BOTSCOPE_UX_DIR")
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        path = base / "BotScope"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        path = Path(xdg) / "botscope" if xdg else Path.home() / ".config" / "botscope"
    path.mkdir(parents=True, exist_ok=True)
    return path


FileKind = Literal["log", "pcap", "session", "other"]


@dataclass
class RecentFile:
    path: str
    kind: FileKind
    opened_at: str
    label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecentFile:
        kind = data.get("kind") or "other"
        if kind not in {"log", "pcap", "session", "other"}:
            kind = "other"
        return cls(
            path=str(data["path"]),
            kind=kind,  # type: ignore[arg-type]
            opened_at=str(data.get("opened_at") or ""),
            label=data.get("label"),
        )


@dataclass
class RecentFiles:
    path: Path = field(default_factory=lambda: _ux_dir() / "recent_files.json")
    max_entries: int = 25
    entries: list[RecentFile] = field(default_factory=list)

    def load(self) -> RecentFiles:
        if not self.path.exists():
            self.entries = []
            return self
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = [RecentFile.from_dict(x) for x in raw.get("entries", [])]
        except (json.JSONDecodeError, OSError, TypeError, KeyError):
            self.entries = []
        return self

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"entries": [e.to_dict() for e in self.entries]}, indent=2),
            encoding="utf-8",
        )

    def remember(self, path: str | Path, *, kind: FileKind, label: str | None = None) -> None:
        path_s = str(Path(path).resolve()) if Path(path).exists() else str(path)
        self.entries = [e for e in self.entries if e.path != path_s]
        self.entries.insert(
            0,
            RecentFile(
                path=path_s,
                kind=kind,
                opened_at=datetime.now(timezone.utc).isoformat(),
                label=label or Path(path_s).name,
            ),
        )
        self.entries = self.entries[: self.max_entries]
        self.save()

    def existing(self) -> list[RecentFile]:
        return [e for e in self.entries if Path(e.path).exists()]


@dataclass
class AppSettings:
    """Local Observatory preferences (never leave the machine by default)."""

    theme: str = "instrument"  # instrument | high_contrast
    hash_ips: bool = False
    truncate_ips: bool = False
    redact_query: bool = True
    open_last_session_on_start: bool = False
    show_welcome: bool = True
    remember_window_geometry: bool = True
    default_denominator: str = "requests"
    auto_save_session_dir: str | None = None
    cloudflare_radar_token: str | None = None
    reduce_motion: bool = False
    chart_animation: bool = True
    auto_refresh_sources: bool = True
    interface_density: str = "comfortable"  # comfortable | compact
    last_page_id: str = "observatory"
    sidebar_collapsed: bool = False
    sidebar_width: int = 220

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


def settings_path() -> Path:
    return _ux_dir() / "settings.json"


def load_settings() -> AppSettings:
    from botscope.ux.secure_store import (
        SECRET_FIELDS,
        load_secrets,
        lockdown_path,
        merge_secrets,
        save_secrets,
        split_settings_dict,
    )

    ux = _ux_dir()
    lockdown_path(ux)
    path = settings_path()
    if not path.exists():
        # Still merge vault if present (secrets-only upgrade path)
        secrets = load_secrets(ux)
        if secrets:
            return AppSettings.from_dict(merge_secrets({}, secrets))
        return AppSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return AppSettings()
        public, embedded = split_settings_dict(raw)
        vault = load_secrets(ux)
        # Prefer vault. Never let conflicting plaintext overwrite a sealed vault
        # (tamper tripwire handles exploit detection on GUI launch).
        secrets = dict(vault)
        migrate = False
        if embedded and not vault:
            secrets = dict(embedded)
            migrate = True
        elif embedded and vault:
            conflict = False
            for key in SECRET_FIELDS:
                if key not in embedded:
                    continue
                if key in vault and embedded[key] != vault[key]:
                    conflict = True
                    break
                if key not in vault:
                    secrets[key] = embedded[key]
                    migrate = True
            # Identical leftovers: strip plaintext without changing vault.
            if not conflict and all(
                embedded.get(k) == vault.get(k) for k in embedded
            ):
                migrate = True
            # On conflict, keep vault secrets and leave settings dirty for tripwire.
        if migrate:
            save_secrets(ux, secrets)
            path.write_text(json.dumps(public, indent=2), encoding="utf-8")
            lockdown_path(path)
        merged = merge_secrets(public, secrets)
        return AppSettings.from_dict(merged)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        # Self-heal: quarantine corrupt settings, continue with defaults
        try:
            quarantine = path.with_suffix(".corrupt.json")
            path.replace(quarantine)
        except OSError:
            pass
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    from botscope.ux.secure_store import lockdown_path, save_secrets, split_settings_dict

    ux = _ux_dir()
    ux.mkdir(parents=True, exist_ok=True)
    lockdown_path(ux)
    path = settings_path()
    data = settings.to_dict()
    public, secrets = split_settings_dict(data)
    # Never persist secret fields in plaintext settings.json
    save_secrets(ux, secrets)
    path.write_text(json.dumps(public, indent=2), encoding="utf-8")
    lockdown_path(path)
    # Harden sibling UX files too
    for name in ("recent_files.json", "presets.json", "secrets.vault", "secrets.seal", "security.lockout"):
        sibling = ux / name
        if sibling.exists():
            lockdown_path(sibling)


def classify_path(path: str | Path) -> FileKind:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".pcap", ".pcapng", ".cap"}:
        return "pcap"
    if suffix == ".bscope" or p.is_dir() and (p / "events.jsonl").exists():
        return "session"
    if suffix in {".log", ".txt", ".json", ".jsonl", ".ndjson"}:
        return "log"
    return "other"
