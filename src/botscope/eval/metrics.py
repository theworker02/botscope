"""Classification evaluation metrics (macro/micro/per-class)."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassScore:
    label: str
    precision: float
    recall: float
    f1: float
    support: int

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1": round(self.f1, 6),
            "support": self.support,
        }


@dataclass
class ConfusionMatrix:
    labels: list[str]
    matrix: dict[str, dict[str, int]]

    def to_dict(self) -> dict:
        return {"labels": list(self.labels), "matrix": {k: dict(v) for k, v in self.matrix.items()}}


@dataclass
class EvalReport:
    n: int
    accuracy: float
    macro_f1: float
    micro_f1: float
    per_class: list[ClassScore]
    confusion: ConfusionMatrix
    note: str = "Computed from labeled fixtures only."

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "accuracy": round(self.accuracy, 6),
            "macro_f1": round(self.macro_f1, 6),
            "micro_f1": round(self.micro_f1, 6),
            "per_class": [c.to_dict() for c in self.per_class],
            "confusion": self.confusion.to_dict(),
            "note": self.note,
        }


def precision_recall(tp: int, fp: int, fn: int) -> tuple[float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def evaluate_labels(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    labels: Iterable[str] | None = None,
) -> EvalReport:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal length")
    label_set = sorted(set(labels) if labels is not None else (set(y_true) | set(y_pred)))
    conf: dict[str, Counter[str]] = defaultdict(Counter)
    for t, p in zip(y_true, y_pred, strict=False):
        conf[t][p] += 1

    per_class: list[ClassScore] = []
    f1s: list[float] = []
    total_tp = total_fp = total_fn = 0
    for label in label_set:
        tp = conf[label][label]
        fp = sum(conf[other][label] for other in label_set if other != label)
        fn = sum(count for pred, count in conf[label].items() if pred != label)
        precision, recall = precision_recall(tp, fp, fn)
        f1 = f1_score(precision, recall)
        support = sum(conf[label].values())
        per_class.append(
            ClassScore(label=label, precision=precision, recall=recall, f1=f1, support=support)
        )
        f1s.append(f1)
        total_tp += tp
        total_fp += fp
        total_fn += fn

    n = len(y_true)
    accuracy = (sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == p) / n) if n else 0.0
    micro_p, micro_r = precision_recall(total_tp, total_fp, total_fn)
    micro = f1_score(micro_p, micro_r)
    macro = sum(f1s) / len(f1s) if f1s else 0.0
    matrix = ConfusionMatrix(
        labels=label_set,
        matrix={row: {col: conf[row][col] for col in label_set} for row in label_set},
    )
    return EvalReport(
        n=n,
        accuracy=accuracy,
        macro_f1=macro,
        micro_f1=micro,
        per_class=per_class,
        confusion=matrix,
    )
