"""Classification evaluation harness.

Status: IMPLEMENTED

Precision / recall / F1 and confusion matrices over labeled fixtures.
Labels must come from datasets — never fabricated for marketing.
"""

from __future__ import annotations

from botscope.eval.metrics import (
    ClassScore,
    ConfusionMatrix,
    EvalReport,
    evaluate_labels,
    f1_score,
    precision_recall,
)

__all__ = [
    "ClassScore",
    "ConfusionMatrix",
    "EvalReport",
    "evaluate_labels",
    "f1_score",
    "precision_recall",
]
