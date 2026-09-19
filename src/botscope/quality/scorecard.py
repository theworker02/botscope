"""Multi-dimension data quality scorecard.

Status: IMPLEMENTED

Deliberately avoids a single misleading overall percentage.
Each dimension is scored and reported separately with explicit rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from botscope.normalize.event import NormalizedEvent


@dataclass(frozen=True)
class DimensionScore:
    name: str
    score: float  # 0.0 – 1.0 within this dimension only
    label: str  # e.g. poor / fair / good / excellent
    rationale: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "label": self.label,
            "rationale": self.rationale,
            "metrics": dict(self.metrics),
        }


@dataclass
class QualityScorecard:
    dimensions: list[DimensionScore]
    event_count: int
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: list[str] = field(default_factory=list)

    def dimension(self, name: str) -> DimensionScore | None:
        for d in self.dimensions:
            if d.name == name:
                return d
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_count": self.event_count,
            "generated_at": self.generated_at,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "notes": list(self.notes),
            "policy": (
                "No single overall quality percentage is published. "
                "Interpret each dimension independently."
            ),
        }


def _label(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.65:
        return "good"
    if score >= 0.40:
        return "fair"
    return "poor"


def _completeness(events: list[NormalizedEvent]) -> DimensionScore:
    keys = ("timestamp", "src_address", "user_agent", "path", "status", "http_method")
    if not events:
        return DimensionScore(
            "completeness",
            0.0,
            "poor",
            "No events to assess.",
            {"fields": list(keys)},
        )
    present = {k: 0 for k in keys}
    for e in events:
        if e.timestamp:
            present["timestamp"] += 1
        if e.src_address:
            present["src_address"] += 1
        if e.user_agent:
            present["user_agent"] += 1
        if e.path:
            present["path"] += 1
        if e.status is not None:
            present["status"] += 1
        if e.http_method:
            present["http_method"] += 1
    rates = {k: v / len(events) for k, v in present.items()}
    score = sum(rates.values()) / len(rates)
    return DimensionScore(
        "completeness",
        score,
        _label(score),
        "Fraction of events with core fields populated.",
        {"field_presence_rate": {k: round(v, 4) for k, v in rates.items()}},
    )


def _consistency(events: list[NormalizedEvent]) -> DimensionScore:
    if not events:
        return DimensionScore("consistency", 0.0, "poor", "No events to assess.")
    bad = 0
    for e in events:
        if e.status is not None and not (100 <= e.status <= 599):
            bad += 1
        if e.bytes_out is not None and e.bytes_out < 0:
            bad += 1
        if e.src_port is not None and not (0 <= e.src_port <= 65535):
            bad += 1
        if e.confidence is not None and not (0.0 <= e.confidence <= 1.0):
            bad += 1
    rate_ok = 1.0 - (bad / len(events))
    return DimensionScore(
        "consistency",
        rate_ok,
        _label(rate_ok),
        "Share of events passing basic value-range checks.",
        {"violations": bad, "checked_events": len(events)},
    )


def _evidence_coverage(events: list[NormalizedEvent]) -> DimensionScore:
    classified = [e for e in events if e.classification is not None]
    if not classified:
        return DimensionScore(
            "evidence_coverage",
            0.0,
            "poor",
            "No classified events; evidence coverage not applicable yet.",
            {"classified": 0},
        )
    with_ev = sum(1 for e in classified if e.evidence)
    score = with_ev / len(classified)
    return DimensionScore(
        "evidence_coverage",
        score,
        _label(score),
        "Share of classified events that carry inspectable evidence statements.",
        {"classified": len(classified), "with_evidence": with_ev},
    )


def _provenance_clarity(events: list[NormalizedEvent]) -> DimensionScore:
    if not events:
        return DimensionScore("provenance_clarity", 0.0, "poor", "No events to assess.")
    # All NormalizedEvent instances carry an explicit provenance enum — strong baseline.
    labeled = sum(1 for e in events if e.provenance is not None)
    score = labeled / len(events)
    classified_ok = sum(
        1
        for e in events
        if e.classification is None or e.provenance.value in {"CLASSIFIED", "INFERRED", "ESTIMATED"}
    )
    # Mild penalty if classification present but provenance still OBSERVED only.
    mismatch = len(events) - classified_ok
    adjusted = max(0.0, score - (mismatch / len(events)) * 0.25)
    return DimensionScore(
        "provenance_clarity",
        adjusted,
        _label(adjusted),
        "Events carry explicit ProvenanceLevel; penalty if classified without interpretive level.",
        {"labeled": labeled, "classification_provenance_mismatches": mismatch},
    )


def _diversity(events: list[NormalizedEvent]) -> DimensionScore:
    if not events:
        return DimensionScore("source_diversity", 0.0, "poor", "No events to assess.")
    uas = {e.user_agent for e in events if e.user_agent}
    paths = {e.path for e in events if e.path}
    srcs = {e.src_address for e in events if e.src_address}
    # Soft saturation curves — diversity is context-dependent.
    ua_score = min(1.0, len(uas) / 12.0)
    path_score = min(1.0, len(paths) / 20.0)
    src_score = min(1.0, len(srcs) / 15.0)
    score = (ua_score + path_score + src_score) / 3.0
    return DimensionScore(
        "source_diversity",
        score,
        _label(score),
        "Heuristic diversity of user-agents, paths, and sources (not a population claim).",
        {
            "unique_user_agents": len(uas),
            "unique_paths": len(paths),
            "unique_sources": len(srcs),
        },
    )


def _temporal_coverage(events: list[NormalizedEvent]) -> DimensionScore:
    stamps = [e.timestamp for e in events if e.timestamp]
    if len(stamps) < 2:
        return DimensionScore(
            "temporal_coverage",
            0.2 if stamps else 0.0,
            "poor",
            "Need multiple timestamps to assess temporal span.",
            {"timestamped": len(stamps)},
        )
    span = (max(stamps) - min(stamps)).total_seconds()
    # Soft score: minutes→hours→day
    if span <= 0:
        score = 0.3
    elif span < 3600:
        score = 0.45
    elif span < 86400:
        score = 0.7
    else:
        score = 0.9
    return DimensionScore(
        "temporal_coverage",
        score,
        _label(score),
        "Longer observation windows generally support more stable share estimates.",
        {"span_seconds": span, "timestamped": len(stamps)},
    )


def build_scorecard(events: Iterable[NormalizedEvent]) -> QualityScorecard:
    events_list = list(events)
    dimensions = [
        _completeness(events_list),
        _consistency(events_list),
        _evidence_coverage(events_list),
        _provenance_clarity(events_list),
        _diversity(events_list),
        _temporal_coverage(events_list),
    ]
    return QualityScorecard(
        dimensions=dimensions,
        event_count=len(events_list),
        notes=[
            "Do not average dimensions into a single quality percentage for publication.",
            "Quality describes the local dataset, not Internet bot prevalence.",
            "Demo/synthetic data should be labeled separately from production measurements.",
        ],
    )
