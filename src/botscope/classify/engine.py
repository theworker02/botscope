"""Classification engine combining rules, identity, and optional ML."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from botscope.classify.result import (
    MODEL_VERSION,
    RULESET_VERSION,
    ClassificationResult,
    EvidenceItem,
)
from botscope.classify.rules import RuleEngine
from botscope.classify.taxonomy import BotCategory
from botscope.identity.engine import IdentityEngine, IdentityStatus
from botscope.normalize.event import NormalizedEvent
from botscope.signatures.store import SignatureStore

if TYPE_CHECKING:
    from botscope.classify.ml import MlModel


class Classifier:
    """Evidence-backed classifier. Prefers UNKNOWN over forced attribution."""

    def __init__(
        self,
        rules: RuleEngine | None = None,
        identity: IdentityEngine | None = None,
        signatures: SignatureStore | None = None,
        ml_model: MlModel | None = None,
    ) -> None:
        self.signatures = signatures or SignatureStore.load_bundled()
        self.rules = rules or RuleEngine()
        self.identity = identity or IdentityEngine(self.signatures)
        self.ml_model = ml_model

    def classify(self, event: NormalizedEvent) -> ClassificationResult:
        identity = self.identity.verify(event)
        matches = self.rules.evaluate(event)
        evidence: list[EvidenceItem] = []
        ml_extras: dict[str, Any] = {}

        for match in matches:
            evidence.append(match.evidence)

        for statement in identity.evidence:
            polarity = "against" if identity.status in {
                IdentityStatus.MISMATCH,
                IdentityStatus.UNVERIFIED_CLAIM,
            } and "alone" in statement.lower() else "for"
            if identity.status == IdentityStatus.MISMATCH:
                polarity = "against" if "mismatch" in statement.lower() else polarity
            evidence.append(EvidenceItem(statement=statement, polarity=polarity))

        ml_pred = None
        if self.ml_model is not None:
            ml_pred = self.ml_model.predict(event)
            if ml_pred is not None:
                ml_extras["ml"] = ml_pred.to_dict()
                evidence.append(
                    EvidenceItem(
                        statement=(
                            f"ML model {ml_pred.model_id} P={ml_pred.score:.2f} "
                            f"→ {ml_pred.category}"
                        ),
                        polarity="for",
                    )
                )

        # Prefer verified identity category when corroboration succeeds.
        if identity.status == IdentityStatus.VERIFIED and identity.signature is not None:
            try:
                category = BotCategory(identity.signature.category)
            except ValueError:
                category = BotCategory.UNKNOWN_AUTOMATION
            return ClassificationResult(
                category=category,
                confidence=identity.confidence,
                evidence=evidence,
                model_version=MODEL_VERSION,
                ruleset_version=RULESET_VERSION,
                attribution=identity.claimed_name,
                identity_status=identity.status.value,
                extras=ml_extras,
            )

        if not matches:
            # Use ML as primary when rules have no match (still never above VERIFIED).
            if ml_pred is not None and ml_pred.score >= 0.35:
                try:
                    ml_cat = BotCategory(ml_pred.category)
                except ValueError:
                    ml_cat = BotCategory.UNKNOWN
                return ClassificationResult(
                    category=ml_cat,
                    confidence=max(0.05, min(0.95, ml_pred.score)),
                    evidence=evidence
                    or [
                        EvidenceItem(
                            statement="ML model filled gap with no rule matches",
                            polarity="for",
                        )
                    ],
                    model_version=MODEL_VERSION,
                    ruleset_version=RULESET_VERSION,
                    attribution=identity.claimed_name,
                    identity_status=identity.status.value,
                    extras={
                        "confidence_note": (
                            f"Confidence from ML model {ml_pred.model_id} probability"
                        ),
                        "matched_rules": [],
                        "decision_path": "ml",
                        **ml_extras,
                    },
                )
            extras = {
                "confidence_note": (
                    "Insufficient rule/ML evidence — UNKNOWN is a valid outcome"
                ),
                "matched_rules": [],
                "decision_path": "unknown",
                **ml_extras,
            }
            return ClassificationResult(
                category=BotCategory.UNKNOWN,
                confidence=0.2,
                evidence=evidence
                or [
                    EvidenceItem(
                        statement="Insufficient evidence for classification",
                        polarity="against",
                    )
                ],
                model_version=MODEL_VERSION,
                ruleset_version=RULESET_VERSION,
                attribution=identity.claimed_name,
                identity_status=identity.status.value,
                extras=extras,
            )

        # Choose highest-confidence non-generic match when available.
        ranked = sorted(matches, key=lambda m: m.confidence, reverse=True)
        best = ranked[0]

        # If UA claims a bot but identity mismatched, do not upgrade to verified category.
        category = best.category
        confidence = best.confidence
        attribution = identity.claimed_name

        if identity.status == IdentityStatus.MISMATCH:
            category = BotCategory.UNKNOWN_AUTOMATION
            confidence = min(confidence, 0.45)
            evidence.append(
                EvidenceItem(
                    statement="Claimed identity failed verification — not attributing to operator",
                    polarity="against",
                    rule_id=None,
                )
            )
            attribution = None
        elif identity.status == IdentityStatus.UNVERIFIED_CLAIM:
            # Keep category from rules but lower confidence and withhold verified attribution.
            confidence = min(confidence, 0.55)
            evidence.append(
                EvidenceItem(
                    statement="Identity remains an unverified claim",
                    polarity="against",
                )
            )

        # Cap confidence — v2 rule scores are heuristics unless from ML probabilities.
        confidence = max(0.05, min(0.95, confidence))

        extras = {
            "confidence_note": (
                "v2 rule confidence is a heuristic score; ML paths expose model probabilities. "
                "Neither is a calibrated population prevalence."
            ),
            "matched_rules": [m.rule_id for m in matches],
            **ml_extras,
        }
        return ClassificationResult(
            category=category,
            confidence=confidence,
            evidence=evidence,
            model_version=MODEL_VERSION,
            ruleset_version=RULESET_VERSION,
            attribution=attribution if identity.status == IdentityStatus.VERIFIED else None,
            identity_status=identity.status.value,
            extras=extras,
        )
