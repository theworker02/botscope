"""Session comparison and change detection.

Status: IMPLEMENTED
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from botscope.normalize.event import NormalizedEvent
from botscope.storage.session import SessionStore


@dataclass
class CategoryDelta:
    category: str
    left: int
    right: int

    @property
    def delta(self) -> int:
        return self.right - self.left

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "left": self.left,
            "right": self.right,
            "delta": self.delta,
        }


@dataclass
class SessionComparison:
    left_label: str
    right_label: str
    left_events: int
    right_events: int
    category_deltas: list[CategoryDelta]
    shared_event_ids: int
    only_left_ids: int
    only_right_ids: int
    classification_changes: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_label": self.left_label,
            "right_label": self.right_label,
            "left_events": self.left_events,
            "right_events": self.right_events,
            "category_deltas": [c.to_dict() for c in self.category_deltas],
            "shared_event_ids": self.shared_event_ids,
            "only_left_ids": self.only_left_ids,
            "only_right_ids": self.only_right_ids,
            "classification_changes": self.classification_changes[:100],
            "classification_changes_truncated": len(self.classification_changes) > 100,
            "generated_at": self.generated_at,
        }


def _category_counts(events: Iterable[NormalizedEvent]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for e in events:
        counts[e.classification or "UNCLASSIFIED"] += 1
    return counts


def compare_event_sets(
    left: Iterable[NormalizedEvent],
    right: Iterable[NormalizedEvent],
    *,
    left_label: str = "left",
    right_label: str = "right",
    track_id_changes: bool = True,
) -> SessionComparison:
    left_list = list(left)
    right_list = list(right)
    left_counts = _category_counts(left_list)
    right_counts = _category_counts(right_list)
    cats = sorted(set(left_counts) | set(right_counts))
    deltas = [
        CategoryDelta(category=c, left=left_counts.get(c, 0), right=right_counts.get(c, 0))
        for c in cats
    ]
    left_ids = {e.event_id: e for e in left_list}
    right_ids = {e.event_id: e for e in right_list}
    shared = set(left_ids) & set(right_ids)
    changes: list[dict[str, Any]] = []
    if track_id_changes:
        for eid in sorted(shared):
            a = left_ids[eid]
            b = right_ids[eid]
            if a.classification != b.classification or a.confidence != b.confidence:
                changes.append(
                    {
                        "event_id": eid,
                        "left_classification": a.classification,
                        "right_classification": b.classification,
                        "left_confidence": a.confidence,
                        "right_confidence": b.confidence,
                    }
                )
    return SessionComparison(
        left_label=left_label,
        right_label=right_label,
        left_events=len(left_list),
        right_events=len(right_list),
        category_deltas=deltas,
        shared_event_ids=len(shared),
        only_left_ids=len(set(left_ids) - shared),
        only_right_ids=len(set(right_ids) - shared),
        classification_changes=changes,
    )


def compare_sessions(
    left_path: str | Path,
    right_path: str | Path,
) -> SessionComparison:
    """Compare two .bscope session directories by loading events."""
    left_store = SessionStore(left_path)
    right_store = SessionStore(right_path)
    try:
        left_events = list(left_store.iter_events())
        right_events = list(right_store.iter_events())
        left_meta = left_store.get_session(left_store.latest_session_id() or "")
        right_meta = right_store.get_session(right_store.latest_session_id() or "")
        left_label = (
            f"{left_path}@{left_meta.classifier_version}" if left_meta else str(left_path)
        )
        right_label = (
            f"{right_path}@{right_meta.classifier_version}" if right_meta else str(right_path)
        )
        return compare_event_sets(
            left_events,
            right_events,
            left_label=left_label,
            right_label=right_label,
        )
    finally:
        left_store.close()
        right_store.close()
