"""Aggregate statistics with explicit provenance."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Literal

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES, BotCategory
from botscope.normalize.event import NormalizedEvent, ProvenanceLevel


Denominator = Literal["requests", "bytes", "connections"]


@dataclass
class ObservatoryStats:
    total_events: int = 0
    total_bytes: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_category_bytes: dict[str, int] = field(default_factory=dict)
    confidence_histogram: dict[str, int] = field(default_factory=dict)
    top_user_agents: list[tuple[str, int]] = field(default_factory=list)
    timeline: list[tuple[str, int, int, int]] = field(default_factory=list)
    # bucket, total, automated, human
    provenance: ProvenanceLevel = ProvenanceLevel.CLASSIFIED
    is_demo: bool = False

    def automation_fraction(self, denominator: Denominator = "requests") -> float | None:
        if denominator == "requests":
            if self.total_events == 0:
                return None
            auto = sum(
                count
                for cat, count in self.by_category.items()
                if cat in {c.value for c in AUTOMATION_CATEGORIES}
            )
            return auto / self.total_events
        if denominator == "bytes":
            if self.total_bytes == 0:
                return None
            auto = sum(
                count
                for cat, count in self.by_category_bytes.items()
                if cat in {c.value for c in AUTOMATION_CATEGORIES}
            )
            return auto / self.total_bytes
        # connections approximated by unique src in timeline build — not tracked here yet
        return self.automation_fraction("requests")

    def human_fraction(self, denominator: Denominator = "requests") -> float | None:
        if denominator == "requests":
            if self.total_events == 0:
                return None
            return self.by_category.get(BotCategory.HUMAN_LIKELY.value, 0) / self.total_events
        if denominator == "bytes":
            if self.total_bytes == 0:
                return None
            return self.by_category_bytes.get(BotCategory.HUMAN_LIKELY.value, 0) / self.total_bytes
        return self.human_fraction("requests")

    def unknown_fraction(self, denominator: Denominator = "requests") -> float | None:
        if self.total_events == 0:
            return None
        unknown = self.by_category.get(BotCategory.UNKNOWN.value, 0)
        if denominator == "requests":
            return unknown / self.total_events
        if denominator == "bytes" and self.total_bytes:
            return self.by_category_bytes.get(BotCategory.UNKNOWN.value, 0) / self.total_bytes
        return unknown / self.total_events

    def to_dict(self) -> dict:
        return {
            "total_events": self.total_events,
            "total_bytes": self.total_bytes,
            "by_category": self.by_category,
            "by_category_bytes": self.by_category_bytes,
            "confidence_histogram": self.confidence_histogram,
            "top_user_agents": self.top_user_agents,
            "timeline": self.timeline,
            "automation_fraction_requests": self.automation_fraction("requests"),
            "human_fraction_requests": self.human_fraction("requests"),
            "unknown_fraction_requests": self.unknown_fraction("requests"),
            "provenance": self.provenance.value,
            "is_demo": self.is_demo,
        }


def aggregate_events(
    events: Iterable[NormalizedEvent],
    *,
    is_demo: bool = False,
    timeline_bucket: str = "hour",
) -> ObservatoryStats:
    by_category: Counter[str] = Counter()
    by_category_bytes: Counter[str] = Counter()
    confidence_hist: Counter[str] = Counter()
    ua_counts: Counter[str] = Counter()
    timeline_total: dict[str, int] = defaultdict(int)
    timeline_auto: dict[str, int] = defaultdict(int)
    timeline_human: dict[str, int] = defaultdict(int)
    total_events = 0
    total_bytes = 0
    auto_labels = {c.value for c in AUTOMATION_CATEGORIES}

    for event in events:
        total_events += 1
        nbytes = int(event.bytes_out or 0) + int(event.bytes_in or 0)
        total_bytes += nbytes
        cat = event.classification or BotCategory.UNKNOWN.value
        by_category[cat] += 1
        by_category_bytes[cat] += nbytes
        if event.confidence is not None:
            bucket = f"{int(event.confidence * 10) / 10:.1f}"
            confidence_hist[bucket] += 1
        if event.user_agent:
            ua_counts[event.user_agent] += 1

        ts = event.timestamp
        key = _bucket_time(ts, timeline_bucket)
        timeline_total[key] += 1
        if cat in auto_labels:
            timeline_auto[key] += 1
        if cat == BotCategory.HUMAN_LIKELY.value:
            timeline_human[key] += 1

    timeline = [
        (k, timeline_total[k], timeline_auto.get(k, 0), timeline_human.get(k, 0))
        for k in sorted(timeline_total)
    ]
    return ObservatoryStats(
        total_events=total_events,
        total_bytes=total_bytes,
        by_category=dict(by_category),
        by_category_bytes=dict(by_category_bytes),
        confidence_histogram=dict(confidence_hist),
        top_user_agents=ua_counts.most_common(20),
        timeline=timeline,
        provenance=ProvenanceLevel.CLASSIFIED,
        is_demo=is_demo,
    )


def _bucket_time(ts: datetime, bucket: str) -> str:
    if bucket == "second":
        return ts.strftime("%Y-%m-%dT%H:%M:%S")
    if bucket == "minute":
        return ts.strftime("%Y-%m-%dT%H:%M")
    if bucket == "hour":
        return ts.strftime("%Y-%m-%dT%H:00")
    if bucket == "day":
        return ts.strftime("%Y-%m-%d")
    if bucket == "week":
        return f"{ts.strftime('%Y')}-W{ts.isocalendar().week:02d}"
    if bucket == "month":
        return ts.strftime("%Y-%m")
    return ts.strftime("%Y-%m-%dT%H:00")
