"""Calibration metrics for heuristic classifier confidence scores.

v2 confidence may be a rule heuristic or an ML model probability. These
helpers quantify that gap when labeled evaluation fixtures are available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ReliabilityBin:
    """One bin of a reliability diagram."""

    lower: float
    upper: float
    count: int
    mean_confidence: float
    empirical_accuracy: float

    @property
    def gap(self) -> float:
        return abs(self.mean_confidence - self.empirical_accuracy)

    def to_dict(self) -> dict:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "count": self.count,
            "mean_confidence": round(self.mean_confidence, 6),
            "empirical_accuracy": round(self.empirical_accuracy, 6),
            "gap": round(self.gap, 6),
        }


@dataclass
class CalibrationReport:
    n: int
    brier: float
    ece: float
    bins: list[ReliabilityBin] = field(default_factory=list)
    note: str = (
        "BotScope v2 confidence is heuristic or ML-model-based. Calibration metrics require "
        "labeled fixtures; they do not invent correctness labels."
    )

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "brier": round(self.brier, 6),
            "ece": round(self.ece, 6),
            "bins": [b.to_dict() for b in self.bins],
            "note": self.note,
        }


def brier_score(confidences: Sequence[float], correct: Sequence[bool]) -> float:
    """Mean squared error between confidence and binary outcome."""
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have equal length")
    if not confidences:
        return 0.0
    total = 0.0
    for c, y in zip(confidences, correct):
        outcome = 1.0 if y else 0.0
        total += (float(c) - outcome) ** 2
    return total / len(confidences)


def reliability_diagram(
    confidences: Sequence[float],
    correct: Sequence[bool],
    *,
    n_bins: int = 10,
) -> list[ReliabilityBin]:
    """Build equal-width reliability bins over [0, 1]."""
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have equal length")
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")
    bins: list[list[tuple[float, bool]]] = [[] for _ in range(n_bins)]
    for c, y in zip(confidences, correct):
        conf = min(max(float(c), 0.0), 1.0)
        idx = min(int(conf * n_bins), n_bins - 1)
        bins[idx].append((conf, y))
    out: list[ReliabilityBin] = []
    width = 1.0 / n_bins
    for i, items in enumerate(bins):
        lower = i * width
        upper = (i + 1) * width
        if not items:
            out.append(
                ReliabilityBin(
                    lower=lower,
                    upper=upper,
                    count=0,
                    mean_confidence=(lower + upper) / 2,
                    empirical_accuracy=0.0,
                )
            )
            continue
        mean_c = sum(c for c, _ in items) / len(items)
        acc = sum(1 for _, y in items if y) / len(items)
        out.append(
            ReliabilityBin(
                lower=lower,
                upper=upper,
                count=len(items),
                mean_confidence=mean_c,
                empirical_accuracy=acc,
            )
        )
    return out


def expected_calibration_error(
    confidences: Sequence[float],
    correct: Sequence[bool],
    *,
    n_bins: int = 10,
) -> float:
    """Weighted average of |confidence − accuracy| across bins."""
    bins = reliability_diagram(confidences, correct, n_bins=n_bins)
    n = len(confidences)
    if n == 0:
        return 0.0
    return sum(b.count * b.gap for b in bins) / n


def calibrate_report(
    confidences: Iterable[float],
    correct: Iterable[bool],
    *,
    n_bins: int = 10,
) -> CalibrationReport:
    conf_list = list(confidences)
    corr_list = list(correct)
    bins = reliability_diagram(conf_list, corr_list, n_bins=n_bins)
    return CalibrationReport(
        n=len(conf_list),
        brier=brier_score(conf_list, corr_list),
        ece=expected_calibration_error(conf_list, corr_list, n_bins=n_bins),
        bins=bins,
    )
