"""Classifier version comparison helpers.

Status: IMPLEMENTED
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from botscope.classify.engine import Classifier
from botscope.classify.result import MODEL_VERSION, RULESET_VERSION
from botscope.normalize.event import NormalizedEvent


@dataclass
class ClassifierVersionComparison:
    left_model: str
    right_model: str
    left_ruleset: str
    right_ruleset: str
    event_count: int
    agreement_rate: float
    confusion: dict[str, dict[str, int]]
    disagreements: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_model": self.left_model,
            "right_model": self.right_model,
            "left_ruleset": self.left_ruleset,
            "right_ruleset": self.right_ruleset,
            "event_count": self.event_count,
            "agreement_rate": round(self.agreement_rate, 4),
            "confusion": self.confusion,
            "disagreements": self.disagreements[:100],
            "disagreements_truncated": len(self.disagreements) > 100,
            "generated_at": self.generated_at,
            "note": (
                "Agreement is category equality only; confidence deltas are listed in disagreements."
            ),
        }


ClassifyFn = Callable[[NormalizedEvent], Any]


def compare_classifiers(
    events: Iterable[NormalizedEvent],
    left: Classifier | ClassifyFn | None = None,
    right: Classifier | ClassifyFn | None = None,
    *,
    left_model: str | None = None,
    right_model: str | None = None,
) -> ClassifierVersionComparison:
    """Run two classifiers (or callables) over the same events and compare labels.

    If only one classifier is supplied, compares its live results against each
    event's existing ``classification`` field (useful for re-runs vs stored labels).
    """
    events_list = list(events)
    left_clf = left or Classifier()
    right_clf = right

    def _run(clf: Classifier | ClassifyFn, event: NormalizedEvent) -> tuple[str, float | None]:
        if callable(clf) and not isinstance(clf, Classifier):
            result = clf(event)
        else:
            result = clf.classify(event)  # type: ignore[union-attr]
        cat = getattr(result, "category", None)
        if cat is not None and hasattr(cat, "value"):
            cat = cat.value
        conf = getattr(result, "confidence", None)
        return str(cat), conf

    confusion: dict[str, Counter[str]] = {}
    disagreements: list[dict[str, Any]] = []
    agree = 0

    for event in events_list:
        left_cat, left_conf = _run(left_clf, event)
        if right_clf is None:
            right_cat = event.classification or "UNCLASSIFIED"
            right_conf = event.confidence
        else:
            right_cat, right_conf = _run(right_clf, event)
        confusion.setdefault(left_cat, Counter())[right_cat] += 1
        if left_cat == right_cat:
            agree += 1
        else:
            disagreements.append(
                {
                    "event_id": event.event_id,
                    "user_agent": event.user_agent,
                    "left": left_cat,
                    "right": right_cat,
                    "left_confidence": left_conf,
                    "right_confidence": right_conf,
                }
            )

    n = len(events_list)
    conf_dict = {k: dict(v) for k, v in confusion.items()}
    return ClassifierVersionComparison(
        left_model=left_model
        or getattr(left_clf, "model_version", None)
        or MODEL_VERSION,
        right_model=right_model
        or (
            getattr(right_clf, "model_version", None)
            if right_clf is not None
            else "stored-labels"
        )
        or MODEL_VERSION,
        left_ruleset=RULESET_VERSION,
        right_ruleset=RULESET_VERSION,
        event_count=n,
        agreement_rate=(agree / n) if n else 0.0,
        confusion=conf_dict,
        disagreements=disagreements,
    )
