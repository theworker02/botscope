"""Classification result types and versioned rule engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from botscope.classify.taxonomy import BotCategory

RULESET_VERSION = "2.0.0"
MODEL_VERSION = "rules-ml-2.0.0"


@dataclass(frozen=True)
class EvidenceItem:
    """A single inspectable evidence contribution."""

    statement: str
    polarity: str = "for"  # for | against
    rule_id: str | None = None
    weight: float = 1.0


@dataclass(frozen=True)
class ClassificationResult:
    category: BotCategory
    confidence: float
    evidence: list[EvidenceItem] = field(default_factory=list)
    model_version: str = MODEL_VERSION
    ruleset_version: str = RULESET_VERSION
    attribution: str | None = None
    identity_status: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def evidence_for(self) -> list[str]:
        return [e.statement for e in self.evidence if e.polarity == "for"]

    def evidence_against(self) -> list[str]:
        return [e.statement for e in self.evidence if e.polarity == "against"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "evidence": [
                {
                    "statement": e.statement,
                    "polarity": e.polarity,
                    "rule_id": e.rule_id,
                    "weight": e.weight,
                }
                for e in self.evidence
            ],
            "model_version": self.model_version,
            "ruleset_version": self.ruleset_version,
            "attribution": self.attribution,
            "identity_status": self.identity_status,
        }
