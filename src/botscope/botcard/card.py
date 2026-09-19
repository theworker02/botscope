"""Bot Card representation and library view data.

Status: IMPLEMENTED
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from botscope.signatures.store import Signature, SignatureStore


@dataclass
class BotCard:
    """Human-inspectable card for a known automation identity."""

    name: str
    category: str
    evidence: list[str] = field(default_factory=list)
    source: str = ""
    verification_method: str = ""
    date_checked: str = ""
    confidence: float = 0.0
    notes: str = ""
    ua_patterns: list[str] = field(default_factory=list)
    identity_caveat: str = (
        "User-Agent matches are hypotheses until identity checks succeed. "
        "UNKNOWN remains valid when verification is incomplete."
    )

    @classmethod
    def from_signature(cls, sig: Signature) -> BotCard:
        return cls(
            name=sig.name,
            category=sig.category,
            evidence=list(sig.evidence),
            source=sig.source,
            verification_method=sig.verification_method,
            date_checked=sig.date_checked,
            confidence=sig.confidence,
            notes=sig.notes,
            ua_patterns=list(sig.ua_patterns),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "evidence": list(self.evidence),
            "source": self.source,
            "verification_method": self.verification_method,
            "date_checked": self.date_checked,
            "confidence": self.confidence,
            "notes": self.notes,
            "ua_patterns": list(self.ua_patterns),
            "identity_caveat": self.identity_caveat,
        }


@dataclass
class BotCardLibrary:
    cards: list[BotCard]
    signature_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signature_version": self.signature_version,
            "count": len(self.cards),
            "cards": [c.to_dict() for c in self.cards],
        }

    def by_category(self) -> dict[str, list[BotCard]]:
        out: dict[str, list[BotCard]] = {}
        for card in self.cards:
            out.setdefault(card.category, []).append(card)
        return out


def load_library(store: SignatureStore | None = None) -> BotCardLibrary:
    store = store or SignatureStore.load_bundled()
    cards = [BotCard.from_signature(sig) for sig in store]
    return BotCardLibrary(cards=cards, signature_version=store.VERSION)


def library_index(cards: Iterable[BotCard] | None = None) -> list[dict[str, str]]:
    if cards is None:
        cards = load_library().cards
    return [
        {"name": c.name, "category": c.category, "date_checked": c.date_checked}
        for c in cards
    ]
