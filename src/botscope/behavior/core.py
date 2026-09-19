"""Behavioral feature extraction from normalized events.

Status: IMPLEMENTED
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES
from botscope.normalize.event import NormalizedEvent


def _entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    ent = 0.0
    for n in counts.values():
        p = n / total
        if p > 0:
            ent -= p * math.log2(p)
    return round(ent, 4)


@dataclass
class BehaviorProfile:
    src_address: str
    event_count: int
    unique_paths: int
    unique_user_agents: int
    methods: dict[str, int]
    status_counts: dict[str, int]
    burstiness: float
    mean_inter_arrival_s: float | None = None
    stdev_inter_arrival_s: float | None = None
    majority_classification: str | None = None
    automation_fraction: float | None = None
    path_entropy: float = 0.0
    method_entropy: float = 0.0
    bot_like_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "src_address": self.src_address,
            "event_count": self.event_count,
            "unique_paths": self.unique_paths,
            "unique_user_agents": self.unique_user_agents,
            "methods": dict(self.methods),
            "status_counts": dict(self.status_counts),
            "burstiness": self.burstiness,
            "mean_inter_arrival_s": self.mean_inter_arrival_s,
            "stdev_inter_arrival_s": self.stdev_inter_arrival_s,
            "majority_classification": self.majority_classification,
            "automation_fraction": self.automation_fraction,
            "path_entropy": self.path_entropy,
            "method_entropy": self.method_entropy,
            "bot_like_score": self.bot_like_score,
            "status": "IMPLEMENTED",
        }


def _inter_arrivals(items: list[NormalizedEvent]) -> tuple[float | None, float | None]:
    stamps = sorted(e.timestamp.timestamp() for e in items if e.timestamp)
    if len(stamps) < 2:
        return None, None
    deltas = [stamps[i] - stamps[i - 1] for i in range(1, len(stamps))]
    if not deltas:
        return None, None
    mu = mean(deltas)
    sd = pstdev(deltas) if len(deltas) > 1 else 0.0
    return round(mu, 4), round(sd, 4)


def _bot_like_score(
    *,
    burstiness: float,
    automation_fraction: float | None,
    path_entropy: float,
    unique_uas: int,
    event_count: int,
) -> float:
    auto = automation_fraction or 0.0
    # High burst + high automation + low UA diversity → bot-like
    ua_mono = 1.0 if unique_uas <= 1 and event_count >= 3 else 0.0
    score = (
        0.35 * min(1.0, burstiness / 5.0)
        + 0.40 * auto
        + 0.15 * ua_mono
        + 0.10 * min(1.0, path_entropy / 3.0)
    )
    return round(max(0.0, min(1.0, score)), 3)


def profile_by_source(events: Iterable[NormalizedEvent]) -> list[BehaviorProfile]:
    by_src: dict[str, list[NormalizedEvent]] = defaultdict(list)
    for e in events:
        key = e.src_address or "unknown"
        by_src[key].append(e)
    auto_labels = {c.value for c in AUTOMATION_CATEGORIES}
    profiles: list[BehaviorProfile] = []
    for src, items in by_src.items():
        methods = Counter(e.http_method or "?" for e in items)
        statuses = Counter(str(e.status) if e.status is not None else "?" for e in items)
        paths = [e.path for e in items if e.path]
        path_counts = Counter(paths)
        uas = {e.user_agent for e in items if e.user_agent}
        seconds: set[int] = set()
        for e in items:
            if e.timestamp:
                seconds.add(int(e.timestamp.timestamp()))
        burst = len(items) / max(1, len(seconds))
        cats = Counter(e.classification or "UNCLASSIFIED" for e in items)
        majority = cats.most_common(1)[0][0] if cats else None
        auto_n = sum(n for lab, n in cats.items() if lab in auto_labels)
        auto_frac = (auto_n / len(items)) if items else None
        mu, sd = _inter_arrivals(items)
        path_ent = _entropy(path_counts)
        method_ent = _entropy(methods)
        profiles.append(
            BehaviorProfile(
                src_address=src,
                event_count=len(items),
                unique_paths=len(path_counts),
                unique_user_agents=len(uas),
                methods=dict(methods),
                status_counts=dict(statuses),
                burstiness=round(burst, 3),
                mean_inter_arrival_s=mu,
                stdev_inter_arrival_s=sd,
                majority_classification=majority,
                automation_fraction=round(auto_frac, 4) if auto_frac is not None else None,
                path_entropy=path_ent,
                method_entropy=method_ent,
                bot_like_score=_bot_like_score(
                    burstiness=burst,
                    automation_fraction=auto_frac,
                    path_entropy=path_ent,
                    unique_uas=len(uas),
                    event_count=len(items),
                ),
            )
        )
    profiles.sort(key=lambda p: p.event_count, reverse=True)
    return profiles
