"""Measurement provenance engine and inspector API.

Status: IMPLEMENTED

Builds on Agent 1's ProvenanceLevel enum without modifying normalize/event.py.
Provides field-level provenance tracking, session inspection, and audit trails.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from botscope.normalize.event import NormalizedEvent, ProvenanceLevel


class FieldRole(str, Enum):
    """How a field participates in measurement claims."""

    OBSERVED_RAW = "observed_raw"
    DERIVED = "derived"
    CLASSIFIED = "classified"
    INFERRED = "inferred"
    ESTIMATED = "estimated"
    ANNOTATED = "annotated"
    UNKNOWN = "unknown"


# Fields that are typically direct sensor observations when present.
OBSERVED_FIELDS = frozenset(
    {
        "timestamp",
        "src_address",
        "dst_address",
        "src_port",
        "dst_port",
        "transport",
        "protocol",
        "http_method",
        "host",
        "path",
        "status",
        "user_agent",
        "bytes_in",
        "bytes_out",
        "duration",
        "raw_ref",
        "source_type",
        "sensor_id",
    }
)

CLASSIFIED_FIELDS = frozenset({"classification", "confidence", "evidence"})
INFERRED_FIELDS = frozenset({"asn", "network_owner", "reverse_dns", "forward_dns"})


@dataclass(frozen=True)
class FieldProvenance:
    field: str
    role: FieldRole
    level: ProvenanceLevel
    present: bool
    note: str | None = None


@dataclass
class EventProvenanceReport:
    event_id: str
    event_level: ProvenanceLevel
    fields: list[FieldProvenance] = field(default_factory=list)
    evidence_count: int = 0
    privacy_transforms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_level": self.event_level.value,
            "evidence_count": self.evidence_count,
            "privacy_transforms": list(self.privacy_transforms),
            "fields": [
                {
                    "field": f.field,
                    "role": f.role.value,
                    "level": f.level.value,
                    "present": f.present,
                    "note": f.note,
                }
                for f in self.fields
            ],
        }


@dataclass
class CorpusProvenanceSummary:
    total_events: int = 0
    by_event_level: dict[str, int] = field(default_factory=dict)
    field_presence: dict[str, int] = field(default_factory=dict)
    field_roles: dict[str, str] = field(default_factory=dict)
    events_with_evidence: int = 0
    events_with_privacy_transform: int = 0
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_events": self.total_events,
            "by_event_level": dict(self.by_event_level),
            "field_presence": dict(self.field_presence),
            "field_roles": dict(self.field_roles),
            "events_with_evidence": self.events_with_evidence,
            "events_with_privacy_transform": self.events_with_privacy_transform,
            "generated_at": self.generated_at,
            "notes": [
                "Event-level provenance is taken from NormalizedEvent.provenance.",
                "Field roles are heuristic defaults for v0.1 inspection, not sensor truth.",
                "Missing fields remain absent — absence is not fabricated as zero.",
            ],
        }


def _role_for_field(name: str) -> FieldRole:
    if name in OBSERVED_FIELDS:
        return FieldRole.OBSERVED_RAW
    if name in CLASSIFIED_FIELDS:
        return FieldRole.CLASSIFIED
    if name in INFERRED_FIELDS:
        return FieldRole.INFERRED
    if name in {"privacy_transform", "extras", "tls_metadata"}:
        return FieldRole.DERIVED
    return FieldRole.UNKNOWN


def _level_for_role(role: FieldRole) -> ProvenanceLevel:
    if role is FieldRole.OBSERVED_RAW:
        return ProvenanceLevel.OBSERVED
    if role is FieldRole.CLASSIFIED:
        return ProvenanceLevel.CLASSIFIED
    if role is FieldRole.INFERRED:
        return ProvenanceLevel.INFERRED
    if role is FieldRole.ESTIMATED:
        return ProvenanceLevel.ESTIMATED
    return ProvenanceLevel.OBSERVED


def inspect_event(event: NormalizedEvent) -> EventProvenanceReport:
    """Inspect a single event's field-level provenance."""
    fields: list[FieldProvenance] = []
    data = event.model_dump()
    for name, value in data.items():
        if name in {"event_id", "provenance"}:
            continue
        present = value is not None and value != [] and value != {}
        role = _role_for_field(name)
        note = None
        if name == "confidence" and present:
            note = "Heuristic score, not a calibrated probability"
        if name in INFERRED_FIELDS and present:
            note = "Typically enrichment; treat as INFERRED unless sensor-observed"
        fields.append(
            FieldProvenance(
                field=name,
                role=role,
                level=_level_for_role(role),
                present=bool(present),
                note=note,
            )
        )
    return EventProvenanceReport(
        event_id=event.event_id,
        event_level=event.provenance,
        fields=fields,
        evidence_count=len(event.evidence or []),
        privacy_transforms=list(event.privacy_transform or []),
    )


def summarize_corpus(events: Iterable[NormalizedEvent]) -> CorpusProvenanceSummary:
    """Aggregate provenance across a corpus for research audits."""
    level_counts: Counter[str] = Counter()
    presence: Counter[str] = Counter()
    roles: dict[str, str] = {}
    total = 0
    with_evidence = 0
    with_privacy = 0
    for event in events:
        total += 1
        level_counts[event.provenance.value] += 1
        if event.evidence:
            with_evidence += 1
        if event.privacy_transform:
            with_privacy += 1
        report = inspect_event(event)
        for fp in report.fields:
            roles.setdefault(fp.field, fp.role.value)
            if fp.present:
                presence[fp.field] += 1
    return CorpusProvenanceSummary(
        total_events=total,
        by_event_level=dict(level_counts),
        field_presence=dict(presence),
        field_roles=roles,
        events_with_evidence=with_evidence,
        events_with_privacy_transform=with_privacy,
    )


def iter_classified_only(events: Iterable[NormalizedEvent]) -> Iterator[NormalizedEvent]:
    """Yield events whose provenance is CLASSIFIED (or higher interpretive layers)."""
    interpretive = {
        ProvenanceLevel.CLASSIFIED,
        ProvenanceLevel.INFERRED,
        ProvenanceLevel.ESTIMATED,
    }
    for event in events:
        if event.provenance in interpretive or event.classification is not None:
            yield event


def claim_safe_totals(events: Iterable[NormalizedEvent]) -> dict[str, Any]:
    """Separate OBSERVED counts from CLASSIFIED shares for honest reporting."""
    events_list = list(events)
    observed_n = len(events_list)
    classified_n = sum(1 for e in events_list if e.classification is not None)
    unknown_n = sum(1 for e in events_list if e.classification == "UNKNOWN")
    return {
        "observed_event_count": observed_n,
        "classified_event_count": classified_n,
        "unknown_classification_count": unknown_n,
        "provenance": {
            "counts": ProvenanceLevel.OBSERVED.value,
            "classifications": ProvenanceLevel.CLASSIFIED.value,
        },
        "disclaimer": (
            "Do not present classified shares as Internet-wide estimates. "
            "Results apply only to the analyzed sensor/source population."
        ),
    }
