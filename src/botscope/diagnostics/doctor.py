"""Diagnostics — doctor checks and sanitized support bundles.

Status: IMPLEMENTED
"""

from __future__ import annotations

import json
import platform
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from botscope.__version__ import __version__
from botscope.native import native_status
from botscope.network.client import NetworkClient
from botscope.signatures.store import SignatureStore


@dataclass
class CheckResult:
    name: str
    status: str  # ok | warn | fail | info
    detail: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "data": dict(self.data),
        }


def _pkg_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except Exception:
        return None


def run_doctor() -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            "botscope_version",
            "ok",
            f"BotScope {__version__}",
            {"version": __version__},
        )
    )
    checks.append(
        CheckResult(
            "python",
            "ok",
            f"Python {sys.version.split()[0]} on {platform.system()}",
            {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "machine": platform.machine(),
            },
        )
    )

    for dep in ("click", "pydantic", "rich", "platformdirs", "packaging"):
        ver = _pkg_version(dep)
        checks.append(
            CheckResult(
                f"dep:{dep}",
                "ok" if ver else "fail",
                f"{dep} {ver}" if ver else f"{dep} missing",
                {"version": ver},
            )
        )

    for optional in ("PySide6", "httpx", "scapy", "duckdb", "numpy"):
        ver = _pkg_version(optional)
        checks.append(
            CheckResult(
                f"optional:{optional}",
                "ok" if ver else "info",
                f"{optional} {ver}" if ver else f"{optional} not installed (optional)",
                {"version": ver},
            )
        )

    native = native_status()
    checks.append(
        CheckResult(
            "native_backend",
            "ok",
            f"backend={native.get('backend')} performance={native.get('performance')}",
            native,
        )
    )

    try:
        store = SignatureStore.load_bundled()
        count = len(store)
        checks.append(
            CheckResult(
                "signatures",
                "ok",
                f"Bundled signatures loaded (n={count}, version={store.VERSION})",
                {"version": store.VERSION, "count": count},
            )
        )
    except Exception as exc:  # pragma: no cover
        checks.append(CheckResult("signatures", "fail", f"Failed to load signatures: {exc}"))

    net = NetworkClient().status()
    contrib = net.get("contribution", "OFF")
    checks.append(
        CheckResult(
            "network_contribution",
            "ok" if contrib == "OFF" else "warn",
            f"contribution={contrib} (default OFF)",
            {k: net[k] for k in net if k != "sensor_id"},
        )
    )

    try:
        from botscope.identity import load_published_range_index

        _index, range_status = load_published_range_index()
        prefix_n = int(range_status.get("prefix_count") or 0)
        checks.append(
            CheckResult(
                "identity_published_ranges",
                "ok" if prefix_n > 0 else "warn",
                range_status.get("detail") or "published crawler ranges",
                range_status,
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(
            CheckResult(
                "identity_published_ranges",
                "warn",
                f"Could not load published ranges: {exc}",
            )
        )

    # Import path sanity for Phase II modules
    for mod in (
        "botscope.provenance",
        "botscope.quality",
        "botscope.compare",
        "botscope.research",
        "botscope.diagnostics",
        "botscope.identity",
    ):
        try:
            __import__(mod)
            checks.append(CheckResult(f"module:{mod}", "ok", "importable"))
        except Exception as exc:
            checks.append(CheckResult(f"module:{mod}", "fail", str(exc)))

    return checks


def doctor_report() -> dict[str, Any]:
    checks = run_doctor()
    statuses = [c.status for c in checks]
    overall = "ok"
    if "fail" in statuses:
        overall = "fail"
    elif "warn" in statuses:
        overall = "warn"
    return {
        "overall": overall,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "botscope_version": __version__,
        "checks": [c.to_dict() for c in checks],
    }


_REDACT_KEYS = {"sensor_id", "ip", "src_address", "dst_address", "path", "user", "home", "salt"}


def sanitize_for_bundle(data: Any) -> Any:
    """Recursively redact likely-sensitive keys and absolute home paths."""
    home = str(Path.home())
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if str(k).lower() in _REDACT_KEYS or "salt" in str(k).lower():
                out[k] = "<redacted>"
            else:
                out[k] = sanitize_for_bundle(v)
        return out
    if isinstance(data, list):
        return [sanitize_for_bundle(x) for x in data]
    if isinstance(data, str) and home and home in data:
        return data.replace(home, "<HOME>")
    return data


def write_doctor_bundle(path: str | Path) -> Path:
    """Write a sanitized diagnostic zip suitable for support tickets."""
    path = Path(path)
    if path.suffix.lower() != ".zip":
        path = path.with_suffix(".zip")
    path.parent.mkdir(parents=True, exist_ok=True)
    report = sanitize_for_bundle(doctor_report())
    env = sanitize_for_bundle(
        {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": "<redacted>",
            "cwd": "<redacted>",
        }
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doctor.json", json.dumps(report, indent=2))
        zf.writestr("environment.json", json.dumps(env, indent=2))
        zf.writestr(
            "README.txt",
            (
                "BotScope sanitized doctor bundle\n"
                "Do not add raw logs with PII before sharing.\n"
                "Network contribution settings are included without sensor identifiers.\n"
            ),
        )
    return path
