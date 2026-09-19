"""Measurement manifests for reproducibility.

Status: IMPLEMENTED
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from botscope.__version__ import __version__
from botscope.classify.result import MODEL_VERSION, RULESET_VERSION
from botscope.native import native_status
from botscope.signatures.store import SignatureStore


@dataclass
class MeasurementManifest:
    """Describe how a measurement was produced so others can interpret it."""

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    botscope_version: str = __version__
    classifier_version: str = MODEL_VERSION
    ruleset_version: str = RULESET_VERSION
    signature_version: str = SignatureStore.VERSION
    native_backend: str | None = None
    source_path: str | None = None
    source_hash: str | None = None
    source_type: str | None = None
    is_demo: bool = False
    privacy: dict[str, Any] = field(default_factory=dict)
    network_contribution: str = "OFF"
    event_count: int | None = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.native_backend is None:
            self.native_backend = str(native_status().get("backend"))
        if not self.notes:
            self.notes = [
                "Manifest describes local measurement context only.",
                "Do not treat outputs as Internet-wide statistics.",
            ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "botscope_version": self.botscope_version,
            "classifier_version": self.classifier_version,
            "ruleset_version": self.ruleset_version,
            "signature_version": self.signature_version,
            "native_backend": self.native_backend,
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "source_type": self.source_type,
            "is_demo": self.is_demo,
            "privacy": dict(self.privacy),
            "network_contribution": self.network_contribution,
            "event_count": self.event_count,
            "notes": list(self.notes),
        }

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> MeasurementManifest:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            botscope_version=data.get("botscope_version", __version__),
            classifier_version=data.get("classifier_version", MODEL_VERSION),
            ruleset_version=data.get("ruleset_version", RULESET_VERSION),
            signature_version=data.get("signature_version", SignatureStore.VERSION),
            native_backend=data.get("native_backend"),
            source_path=data.get("source_path"),
            source_hash=data.get("source_hash"),
            source_type=data.get("source_type"),
            is_demo=bool(data.get("is_demo", False)),
            privacy=dict(data.get("privacy") or {}),
            network_contribution=data.get("network_contribution", "OFF"),
            event_count=data.get("event_count"),
            notes=list(data.get("notes") or []),
        )
