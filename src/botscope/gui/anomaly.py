"""Explainable offline anomaly detection for Observatory (Phase 6).

Statistical deviations only — never labeled malicious.
Uses timeline volume + composition share spikes and new identities.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES
from botscope.gui.dashboard_stats import composition_from_stats
from botscope.normalize.event import NormalizedEvent
from botscope.signatures.store import SignatureStore
from botscope.statistics.aggregate import aggregate_events


@dataclass(frozen=True)
class AnomalyFinding:
    time_label: str
    metric: str
    baseline: float
    observed: float
    severity: str  # low | moderate | high
    reason: str
    related: str = ""

    def to_dict(self) -> dict:
        return {
            "time": self.time_label,
            "metric": self.metric,
            "baseline": self.baseline,
            "observed": self.observed,
            "severity": self.severity,
            "reason": self.reason,
            "related_traffic": self.related,
            "note": "Anomalous relative to this dataset's own baseline — not a malice label.",
        }


def _severity(z: float) -> str:
    az = abs(z)
    if az >= 4.0:
        return "high"
    if az >= 2.5:
        return "moderate"
    return "low"


def detect_anomalies(
    events: list[NormalizedEvent],
    *,
    denominator: str = "requests",
    z_threshold: float = 2.5,
) -> list[AnomalyFinding]:
    """Detect volume / share / identity anomalies within one loaded dataset."""
    timed = [e for e in events if e.timestamp is not None]
    findings: list[AnomalyFinding] = []
    if len(timed) < 8:
        return findings

    timed.sort(key=lambda e: e.timestamp)  # type: ignore[arg-type, return-value]
    # Bucket by hour
    buckets: dict[str, list[NormalizedEvent]] = {}
    for e in timed:
        key = e.timestamp.strftime("%Y-%m-%d %H:00")  # type: ignore[union-attr]
        buckets.setdefault(key, []).append(e)

    if len(buckets) < 3:
        return findings

    volumes = {k: float(len(v)) for k, v in buckets.items()}
    mean_v = sum(volumes.values()) / len(volumes)
    var_v = sum((x - mean_v) ** 2 for x in volumes.values()) / len(volumes)
    std_v = var_v**0.5 or 1.0

    auto_shares: dict[str, float] = {}
    unk_shares: dict[str, float] = {}
    for k, evs in buckets.items():
        stats = aggregate_events(evs, is_demo=False)
        comp = composition_from_stats(stats, denominator=denominator)
        auto_shares[k] = comp.automated * 100.0
        unk_shares[k] = comp.unknown * 100.0

    def mean_std(d: dict[str, float]) -> tuple[float, float]:
        vals = list(d.values())
        m = sum(vals) / len(vals)
        sd = (sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5 or 1.0
        return m, sd

    mean_a, std_a = mean_std(auto_shares)
    mean_u, std_u = mean_std(unk_shares)

    for k in sorted(buckets):
        vol = volumes[k]
        z_vol = (vol - mean_v) / std_v
        if abs(z_vol) >= z_threshold:
            findings.append(
                AnomalyFinding(
                    time_label=k,
                    metric="traffic_volume",
                    baseline=round(mean_v, 2),
                    observed=vol,
                    severity=_severity(z_vol),
                    reason=(
                        f"Hourly event count z={z_vol:.1f} vs dataset mean "
                        f"({mean_v:.1f} ± {std_v:.1f})."
                    ),
                    related=f"{int(vol)} events in bucket",
                )
            )
        z_a = (auto_shares[k] - mean_a) / std_a
        if abs(z_a) >= z_threshold:
            findings.append(
                AnomalyFinding(
                    time_label=k,
                    metric="automated_share_pp",
                    baseline=round(mean_a, 2),
                    observed=round(auto_shares[k], 2),
                    severity=_severity(z_a),
                    reason=(
                        f"Automated share z={z_a:.1f} (percentage points of {denominator})."
                    ),
                    related=f"automated={auto_shares[k]:.1f} pp",
                )
            )
        z_u = (unk_shares[k] - mean_u) / std_u
        if abs(z_u) >= z_threshold:
            findings.append(
                AnomalyFinding(
                    time_label=k,
                    metric="unknown_share_pp",
                    baseline=round(mean_u, 2),
                    observed=round(unk_shares[k], 2),
                    severity=_severity(z_u),
                    reason=(
                        f"Unknown share z={z_u:.1f} (percentage points of {denominator})."
                    ),
                    related=f"unknown={unk_shares[k]:.1f} pp",
                )
            )

    # New identities: signatures in last quartile not seen earlier
    store = SignatureStore.load_bundled()
    auto_cats = {c.value for c in AUTOMATION_CATEGORIES}
    q = max(1, len(timed) // 4)
    early, late = timed[:-q], timed[-q:]

    def names(evs: Iterable[NormalizedEvent]) -> set[str]:
        out: set[str] = set()
        for e in evs:
            if (e.classification or "") not in auto_cats:
                continue
            sig = store.match_user_agent(e.user_agent or "")
            if sig:
                out.add(sig.name)
        return out

    new_ids = names(late) - names(early)
    if new_ids:
        findings.append(
            AnomalyFinding(
                time_label=late[0].timestamp.strftime("%Y-%m-%d %H:%M")  # type: ignore[union-attr]
                if late[0].timestamp
                else "late window",
                metric="new_automated_identities",
                baseline=0.0,
                observed=float(len(new_ids)),
                severity="moderate" if len(new_ids) >= 3 else "low",
                reason="Signatures observed in the final quartile that were absent earlier.",
                related=", ".join(sorted(new_ids)[:8]),
            )
        )

    # Disappearances
    gone = names(early) - names(late)
    if gone and len(early) >= 4:
        findings.append(
            AnomalyFinding(
                time_label="late window",
                metric="identity_disappearance",
                baseline=float(len(gone)),
                observed=0.0,
                severity="low",
                reason="Previously seen automated identities absent in the final quartile.",
                related=", ".join(sorted(gone)[:8]),
            )
        )

    findings.sort(key=lambda f: {"high": 0, "moderate": 1, "low": 2}[f.severity])
    return findings


def compare_windows(
    events: list[NormalizedEvent],
    *,
    start_a: datetime | None,
    end_a: datetime | None,
    start_b: datetime | None,
    end_b: datetime | None,
    denominator: str = "requests",
) -> dict:
    """Compare composition between two time windows. Labels pp vs relative % carefully."""

    def slice_win(start, end) -> list[NormalizedEvent]:
        out = []
        for e in events:
            if e.timestamp is None:
                continue
            if start and e.timestamp < start:
                continue
            if end and e.timestamp > end:
                continue
            out.append(e)
        return out

    a = slice_win(start_a, end_a)
    b = slice_win(start_b, end_b)
    ca = composition_from_stats(aggregate_events(a, is_demo=False), denominator=denominator)
    cb = composition_from_stats(aggregate_events(b, is_demo=False), denominator=denominator)

    def row(name: str, va: float, vb: float, na: int, nb: int) -> dict:
        pp = (vb - va) * 100.0
        rel = ((vb - va) / va * 100.0) if va > 0 else None
        return {
            "metric": name,
            "window_a_share": va,
            "window_b_share": vb,
            "window_a_count": na,
            "window_b_count": nb,
            "percentage_point_change": pp,
            "relative_percent_change": rel,
            "display": (
                f"{va * 100:.1f}% → {vb * 100:.1f}%  "
                f"({pp:+.1f} pp"
                + (f", {rel:+.1f}% relative" if rel is not None else "")
                + ")"
            ),
        }

    return {
        "denominator": denominator,
        "window_a_events": len(a),
        "window_b_events": len(b),
        "rows": [
            row("Automated", ca.automated, cb.automated, ca.automated_count, cb.automated_count),
            row("Human-likely", ca.human_likely, cb.human_likely, ca.human_count, cb.human_count),
            row("Unknown", ca.unknown, cb.unknown, ca.unknown_count, cb.unknown_count),
        ],
        "note": (
            "Percentage-point (pp) change is absolute share difference. "
            "Relative % change is (B−A)/A — do not conflate the two."
        ),
    }
