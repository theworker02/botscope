"""Pure dashboard statistics for Observatory Phase 5 (no Qt)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES, BotCategory
from botscope.normalize.event import NormalizedEvent
from botscope.signatures.store import SignatureStore
from botscope.statistics.aggregate import ObservatoryStats, aggregate_events

CONFIDENCE_BUCKETS = (
    ("Very high", 0.85, 1.01),
    ("High", 0.70, 0.85),
    ("Moderate", 0.50, 0.70),
    ("Low", 0.30, 0.50),
    ("Unresolved", 0.0, 0.30),
)


@dataclass(frozen=True)
class CompositionShare:
    automated: float
    human_likely: float
    unknown: float
    automated_count: int
    human_count: int
    unknown_count: int
    total: int
    denominator: str


@dataclass(frozen=True)
class ActorShare:
    name: str
    count: int
    share: float
    category: str | None = None


@dataclass(frozen=True)
class TrafficPulse:
    auto_pp_delta: float | None
    human_pp_delta: float | None
    unknown_pp_delta: float | None
    largest_actor: str | None
    largest_change: str | None
    new_identities: int
    summary_lines: list[str]


def composition_from_stats(
    stats: ObservatoryStats,
    *,
    denominator: str = "requests",
) -> CompositionShare:
    den = denominator if denominator in {"requests", "bytes"} else "requests"
    total = stats.total_events if den == "requests" else stats.total_bytes
    cats = stats.by_category if den == "requests" else stats.by_category_bytes
    auto_cats = {c.value for c in AUTOMATION_CATEGORIES}
    auto_n = sum(v for k, v in cats.items() if k in auto_cats)
    human_n = cats.get(BotCategory.HUMAN_LIKELY.value, 0)
    cats.get(BotCategory.UNKNOWN.value, 0) + cats.get(
        BotCategory.UNKNOWN_AUTOMATION.value, 0
    )
    # Unknown automation counted in automated for share tiles; keep UA separate for unknown %
    unknown_only = cats.get(BotCategory.UNKNOWN.value, 0)
    if total <= 0:
        return CompositionShare(0.0, 0.0, 0.0, 0, 0, 0, 0, den)
    return CompositionShare(
        automated=auto_n / total,
        human_likely=human_n / total,
        unknown=unknown_only / total,
        automated_count=auto_n,
        human_count=human_n,
        unknown_count=unknown_only,
        total=total,
        denominator=den,
    )


def confidence_distribution(events: Iterable[NormalizedEvent]) -> list[tuple[str, int]]:
    buckets = {name: 0 for name, _, _ in CONFIDENCE_BUCKETS}
    for event in events:
        conf = event.confidence
        if conf is None:
            buckets["Unresolved"] += 1
            continue
        placed = False
        for name, lo, hi in CONFIDENCE_BUCKETS:
            if lo <= conf < hi:
                buckets[name] += 1
                placed = True
                break
        if not placed:
            buckets["Unresolved"] += 1
    return [(name, buckets[name]) for name, _, _ in CONFIDENCE_BUCKETS]


def top_automated_actors(
    events: Iterable[NormalizedEvent],
    *,
    limit: int = 8,
    signatures: SignatureStore | None = None,
) -> list[ActorShare]:
    """Attribute automated events to known signature names or category."""
    store = signatures or SignatureStore.load_bundled()
    auto_cats = {c.value for c in AUTOMATION_CATEGORIES}
    counts: Counter[str] = Counter()
    categories: dict[str, str] = {}
    total_auto = 0
    for event in events:
        cat = event.classification or ""
        if cat not in auto_cats:
            continue
        total_auto += 1
        ua = event.user_agent or ""
        sig = store.match_user_agent(ua)
        if sig is not None:
            name = sig.name
            categories[name] = sig.category
        else:
            attr = (event.extras or {}).get("attribution")
            name = str(attr) if attr else f"Unattributed ({cat})"
            categories[name] = cat
        counts[name] += 1
    if total_auto == 0:
        return []
    actors: list[ActorShare] = []
    for name, count in counts.most_common(limit):
        actors.append(
            ActorShare(
                name=name,
                count=count,
                share=count / total_auto,
                category=categories.get(name),
            )
        )
    return actors


def build_traffic_pulse(
    events: list[NormalizedEvent],
    *,
    denominator: str = "requests",
) -> TrafficPulse:
    """Compare first half vs second half of the observation window (percentage points)."""
    timed = [e for e in events if e.timestamp is not None]
    if len(timed) < 4:
        actors = top_automated_actors(events, limit=1)
        lines = ["Insufficient temporal span for period-over-period pulse."]
        if actors:
            lines.append(f"Largest automated actor: {actors[0].name}")
        return TrafficPulse(
            None,
            None,
            None,
            actors[0].name if actors else None,
            None,
            0,
            lines,
        )

    timed.sort(key=lambda e: e.timestamp)  # type: ignore[arg-type, return-value]
    mid = len(timed) // 2
    first = timed[:mid]
    second = timed[mid:]
    s1 = aggregate_events(first, is_demo=False)
    s2 = aggregate_events(second, is_demo=False)
    c1 = composition_from_stats(s1, denominator=denominator)
    c2 = composition_from_stats(s2, denominator=denominator)

    def pp(a: float, b: float) -> float:
        return (b - a) * 100.0

    auto_d = pp(c1.automated, c2.automated)
    human_d = pp(c1.human_likely, c2.human_likely)
    unk_d = pp(c1.unknown, c2.unknown)

    actors = top_automated_actors(events, limit=1)
    largest = actors[0].name if actors else None

    # New identities = signature matches in second half not in first
    store = SignatureStore.load_bundled()
    def names(evs: list[NormalizedEvent]) -> set[str]:
        out: set[str] = set()
        for e in evs:
            sig = store.match_user_agent(e.user_agent or "")
            if sig:
                out.add(sig.name)
        return out

    new_ids = len(names(second) - names(first))

    changes = [
        ("Automated", auto_d),
        ("Human-likely", human_d),
        ("Unknown", unk_d),
    ]
    biggest = max(changes, key=lambda x: abs(x[1]))
    direction = "increased" if biggest[1] >= 0 else "decreased"
    largest_change = (
        f"{biggest[0]} traffic {direction} by {abs(biggest[1]):.1f} pp "
        f"(first half → second half of observation window)"
    )

    def arrow(v: float) -> str:
        return "↑" if v >= 0 else "↓"

    lines = [
        f"Automated traffic        {arrow(auto_d)} {abs(auto_d):.1f} pp",
        f"Human-likely traffic     {arrow(human_d)} {abs(human_d):.1f} pp",
        f"Unknown traffic          {arrow(unk_d)} {abs(unk_d):.1f} pp",
    ]
    if largest:
        lines.append(f"Largest automated actor: {largest}")
    lines.append(f"Largest detected change: {largest_change}")
    lines.append(f"New automated identities (2nd half): {new_ids}")
    lines.append(
        "Deltas are percentage-point changes between the first and second "
        "halves of the observation window — not causal claims."
    )

    return TrafficPulse(
        auto_pp_delta=auto_d,
        human_pp_delta=human_d,
        unknown_pp_delta=unk_d,
        largest_actor=largest,
        largest_change=largest_change,
        new_identities=new_ids,
        summary_lines=lines,
    )


def explain_composition(comp: CompositionShare, actors: list[ActorShare]) -> str:
    den = "requests" if comp.denominator == "requests" else "bytes"
    lines = [
        f"Automated traffic represents {comp.automated * 100:.1f}% of eligible {den} "
        f"in the selected period ({comp.automated_count:,} of {comp.total:,}).",
        f"Human-likely: {comp.human_likely * 100:.1f}% ({comp.human_count:,}).",
        f"Unknown: {comp.unknown * 100:.1f}% ({comp.unknown_count:,}).",
    ]
    if actors:
        top = actors[0]
        lines.append(
            f"Most attributed automated volume is associated with {top.name} "
            f"({top.share * 100:.1f}% of automated {den})."
        )
    lines.append(
        "Classifications are evidence-backed heuristics. "
        "BotScope does not claim certainty for every event."
    )
    return "\n\n".join(lines)


def metric_provenance(
    *,
    metric: str,
    numerator: int,
    denominator: int,
    denominator_label: str,
    sources: list[str],
    filters: list[str],
    time_range: str,
    ruleset_version: str,
    is_demo: bool,
) -> dict[str, Any]:
    return {
        "metric": metric,
        "numerator": numerator,
        "denominator": denominator,
        "denominator_label": denominator_label,
        "share": (numerator / denominator) if denominator else None,
        "sources": sources,
        "filters": filters,
        "time_range": time_range,
        "ruleset_version": ruleset_version,
        "is_demo": is_demo,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
