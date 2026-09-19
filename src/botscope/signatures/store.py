"""Versioned bot signature database."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Signature:
    name: str
    category: str
    evidence: list[str]
    source: str
    verification_method: str
    date_checked: str
    confidence: float
    notes: str = ""
    ua_patterns: list[str] = field(default_factory=list)
    rdns_suffixes: list[str] = field(default_factory=list)
    expected_asns: list[int] = field(default_factory=list)
    network_owner_tokens: list[str] = field(default_factory=list)
    # Never invent CIDR ranges — only include when authoritative source exists.
    network_ranges: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Signature:
        return cls(
            name=data["name"],
            category=data["category"],
            evidence=list(data.get("evidence", [])),
            source=data.get("source", ""),
            verification_method=data.get("verification_method", ""),
            date_checked=data.get("date_checked", ""),
            confidence=float(data.get("confidence", 0.5)),
            notes=data.get("notes", ""),
            ua_patterns=list(data.get("ua_patterns", [])),
            rdns_suffixes=list(data.get("rdns_suffixes", [])),
            expected_asns=[int(x) for x in data.get("expected_asns", [])],
            network_owner_tokens=list(data.get("network_owner_tokens", [])),
            network_ranges=list(data.get("network_ranges", [])),
        )


class SignatureStore:
    """Load and query versioned bot signatures."""

    VERSION = "2.0.0"

    def __init__(self, signatures: list[Signature] | None = None) -> None:
        self._signatures = list(signatures or [])
        self._compiled: list[tuple[re.Pattern[str], Signature]] = [
            (re.compile(pat, re.IGNORECASE), sig)
            for sig in self._signatures
            for pat in sig.ua_patterns
        ]

    @classmethod
    def load_bundled(cls) -> SignatureStore:
        sigs: list[Signature] = []
        # Prefer package data under botscope/signatures/data
        try:
            data_root = resources.files("botscope.signatures").joinpath("data")
            if data_root.is_dir():
                for path in sorted(data_root.rglob("*.json")):
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(payload, list):
                        sigs.extend(Signature.from_dict(item) for item in payload)
                    else:
                        sigs.append(Signature.from_dict(payload))
        except (FileNotFoundError, ModuleNotFoundError, TypeError):
            pass

        # Fallback to repository signatures/ directory during editable installs
        repo_root = Path(__file__).resolve().parents[3]
        alt = repo_root / "signatures"
        if alt.is_dir() and not sigs:
            for path in sorted(alt.rglob("*.json")):
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    sigs.extend(Signature.from_dict(item) for item in payload)
                else:
                    sigs.append(Signature.from_dict(payload))

        return cls(sigs)

    def __iter__(self) -> Iterator[Signature]:
        return iter(self._signatures)

    def __len__(self) -> int:
        return len(self._signatures)

    def match_user_agent(self, user_agent: str) -> Signature | None:
        if not user_agent:
            return None
        for pattern, sig in self._compiled:
            if pattern.search(user_agent):
                return sig
        return None

    def by_category(self, category: str) -> list[Signature]:
        return [s for s in self._signatures if s.category == category]
