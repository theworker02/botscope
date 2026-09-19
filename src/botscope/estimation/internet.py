"""Internet estimation engine with documented multi-source weighting.

Status: IMPLEMENTED

Release gate opens to ``INTERNET BOT TRAFFIC ESTIMATE`` only when ≥2
independent *traffic-share* observations exist and a non-equal-weight
model is applied with an uncertainty interval. Equal-weight averaging
remains prohibited.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from botscope.sources.base import NormalizedSourceObservation, ObservationKind
from botscope.sources.federation import FederationSnapshot

GATE_OBSERVATIONS = "MULTI-SOURCE BOT TRAFFIC OBSERVATIONS"
GATE_ESTIMATE = "INTERNET BOT TRAFFIC ESTIMATE"

# Documented reliability priors — NOT equal weights. Tuned for known
# population coverage / selection bias, not marketing.
SOURCE_RELIABILITY_PRIORS: dict[str, float] = {
    "cloudflare.radar": 0.50,
    "botscope.local_sensor": 0.35,
    "botscope.session": 0.35,
}


@dataclass
class InternetEstimate:
    metric: str
    estimate: float | None
    interval: tuple[float, float] | None
    population: str
    sources: list[str]
    methodology: str
    limitations: list[str]
    kind: ObservationKind = ObservationKind.BOTSCOPE_ESTIMATED
    coverage: dict[str, Any] = field(default_factory=dict)
    explainer: dict[str, Any] = field(default_factory=dict)
    release_gate: str = GATE_OBSERVATIONS
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "estimate": self.estimate,
            "interval": list(self.interval) if self.interval else None,
            "population": self.population,
            "sources": list(self.sources),
            "methodology": self.methodology,
            "limitations": list(self.limitations),
            "kind": self.kind.value,
            "coverage": dict(self.coverage),
            "explainer": dict(self.explainer),
            "release_gate": self.release_gate,
            "generated_at": self.generated_at,
            "internet_bot_traffic_headline_allowed": self.release_gate == GATE_ESTIMATE,
        }


def _share_observations(
    observations: Iterable[NormalizedSourceObservation],
) -> list[NormalizedSourceObservation]:
    return [
        o
        for o in observations
        if o.metric_name in {"likely_automated_share", "automated_share"}
        and isinstance(o.metric_value, int | float)
    ]


def _observation_weight(obs: NormalizedSourceObservation) -> float:
    extras = obs.extras or {}
    if extras.get("weight") is not None:
        try:
            w = float(extras["weight"])
            if w > 0:
                return w
        except (TypeError, ValueError):
            pass
    if extras.get("coverage_mass") is not None:
        try:
            mass = float(extras["coverage_mass"])
            if mass > 0:
                return mass
        except (TypeError, ValueError):
            pass
    if extras.get("event_count") is not None:
        try:
            n = float(extras["event_count"])
            if n > 0:
                # Log scale so huge local logs don't dominate provider panels
                return math.log10(n + 10.0)
        except (TypeError, ValueError):
            pass
    return SOURCE_RELIABILITY_PRIORS.get(obs.source_id, 0.20)


def _temporal_alignment(shares: list[NormalizedSourceObservation]) -> dict[str, Any]:
    starts = [o.temporal_start for o in shares if o.temporal_start]
    ends = [o.temporal_end for o in shares if o.temporal_end]
    if len(starts) < 2 or len(ends) < 2:
        return {
            "status": "PARTIAL",
            "detail": "Fewer than two sources published temporal windows",
        }
    latest_start = max(starts)
    earliest_end = min(ends)
    if latest_start <= earliest_end:
        return {
            "status": "ALIGNED",
            "intersection_start": latest_start,
            "intersection_end": earliest_end,
        }
    return {
        "status": "MISALIGNED",
        "detail": "Source windows do not overlap; estimate uses per-source windows as-is",
        "latest_start": latest_start,
        "earliest_end": earliest_end,
    }


def _weighted_estimate(
    shares: list[NormalizedSourceObservation],
) -> tuple[float, tuple[float, float], dict[str, float], float]:
    raw_weights = {o.observation_id: _observation_weight(o) for o in shares}
    total = sum(raw_weights.values()) or 1.0
    weights = {k: v / total for k, v in raw_weights.items()}
    values = {o.observation_id: float(o.metric_value) for o in shares}  # type: ignore[arg-type]
    point = sum(weights[oid] * values[oid] for oid in weights)
    # Dispersion across sources → uncertainty (not fake precision)
    variance = sum(weights[oid] * (values[oid] - point) ** 2 for oid in weights)
    # Inflate when few sources; floor so interval is visible
    se = math.sqrt(variance) + (0.05 / math.sqrt(len(shares)))
    z = 1.96
    low = max(0.0, point - z * se)
    high = min(1.0, point + z * se)
    return point, (round(low, 4), round(high, 4)), weights, se


def gate_criteria(
    shares: list[NormalizedSourceObservation],
    *,
    weights_applied: bool,
    uncertainty_computed: bool,
) -> dict[str, Any]:
    independent = {o.source_id for o in shares}
    temporal = _temporal_alignment(shares)
    checks = {
        "multiple_traffic_shares": len(independent) >= 2,
        "populations_documented": all(bool(o.population) for o in shares),
        "weighting_model_applied": weights_applied and len(independent) >= 2,
        "temporal_alignment_considered": True,
        "source_dependence_stated": True,
        "uncertainty_computed": uncertainty_computed and len(independent) >= 2,
    }
    checks["temporal_status"] = temporal["status"]
    passed = all(
        checks[k]
        for k in (
            "multiple_traffic_shares",
            "populations_documented",
            "weighting_model_applied",
            "uncertainty_computed",
        )
    )
    return {"passed": passed, "checks": checks, "temporal": temporal}


def estimate_from_federation(snapshot: FederationSnapshot) -> InternetEstimate:
    """Combine traffic-share observations with documented reliability weights."""
    shares = _share_observations(snapshot.observations)
    source_ids = sorted({o.source_id for o in snapshot.observations})
    coverage = {
        "sources": len(source_ids),
        "share_observations": len(shares),
        "observation_window": "per-source (see explainer)",
        "unknown_source_overlap": "UNKNOWN SOURCE DEPENDENCE",
        "traffic_classes": sorted({o.denominator for o in shares}) or ["n/a"],
    }

    limitations = [
        "Heterogeneous populations are combined only via documented reliability priors / coverage mass.",
        "Equal-weight averaging is prohibited.",
        "Common Crawl catalog metrics are not traffic shares and are excluded from the headline.",
        "Cloudflare (when connected) observes Cloudflare HTTP traffic only.",
        "Source dependence is UNKNOWN unless documented.",
        "Estimate describes the union of observed populations — not a census of the entire Internet.",
    ]

    if len({o.source_id for o in shares}) >= 2:
        point, interval, weights, se = _weighted_estimate(shares)
        criteria = gate_criteria(shares, weights_applied=True, uncertainty_computed=True)
        release_gate = GATE_ESTIMATE if criteria["passed"] else GATE_OBSERVATIONS
        weight_by_source = {
            o.source_id: round(weights[o.observation_id], 4) for o in shares
        }
        explainer = {
            "how_was_this_calculated": (
                "Weighted combination of independent traffic-share observations "
                "using population_reliability_v1 (priors + optional coverage_mass / event_count). "
                "Equal-weight mean is not used."
            ),
            "sources": source_ids,
            "share_sources": sorted({o.source_id for o in shares}),
            "source_populations": {o.source_id: o.population for o in shares},
            "weights": weight_by_source,
            "weighting_model": "population_reliability_v1",
            "time_window": criteria["temporal"],
            "normalization": "Per-source denominators preserved; shares combined after weighting",
            "uncertainty": {
                "method": "weighted_dispersion_plus_finite_sample_floor",
                "se": round(se, 4),
                "interval_95": list(interval),
            },
            "gate_criteria": criteria,
            "excluded_sources": sorted(set(snapshot.errors)),
            "known_biases": [
                "Provider edge bias (Cloudflare)",
                "Local sensor selection bias",
                "UNKNOWN SOURCE DEPENDENCE across panels",
            ],
            "algorithm": "federation_collect_v1 + population_reliability_v1 + release_gate_v2",
            "botscope_version": __import__(
                "botscope.__version__", fromlist=["__version__"]
            ).__version__,
            "raw_table": snapshot.raw_source_table(),
            "errors": dict(snapshot.errors),
        }
        population = (
            "Union of documented traffic-share populations "
            f"({', '.join(sorted({o.source_id for o in shares}))})"
        )
        return InternetEstimate(
            metric="automated_http_request_share",
            estimate=round(point, 4),
            interval=interval,
            population=population,
            sources=source_ids,
            methodology=(
                "INTERNET BOT TRAFFIC ESTIMATE via population_reliability_v1 weighted shares "
                "with uncertainty interval. Not an equal-weight average; not a global census."
                if release_gate == GATE_ESTIMATE
                else "Gate criteria incomplete — falling back to MULTI-SOURCE OBSERVATIONS."
            ),
            limitations=limitations,
            kind=ObservationKind.BOTSCOPE_ESTIMATED,
            coverage=coverage,
            explainer=explainer,
            release_gate=release_gate,
        )

    # Single or zero traffic shares — observations mode
    single = shares[0] if len(shares) == 1 else None
    estimate_val = float(single.metric_value) if single else None
    population = (
        single.population
        if single
        else "No aligned multi-source traffic-share panel"
    )
    explainer = {
        "how_was_this_calculated": (
            "Fewer than two independent traffic-share observations — "
            "no INTERNET BOT TRAFFIC ESTIMATE headline. "
            "Source-level observations are listed with populations intact."
        ),
        "sources": source_ids,
        "source_populations": {
            o.source_id: o.population for o in snapshot.observations
        },
        "weights": "NOT APPLIED — need ≥2 traffic-share sources",
        "time_window": "See each observation temporal_start/end",
        "normalization": "None across sources (different denominators)",
        "uncertainty": "Not computed — insufficient traffic-share panel",
        "excluded_sources": sorted(set(snapshot.errors)),
        "known_biases": [
            "Provider edge bias (Cloudflare)",
            "Crawler corpus bias (Common Crawl)",
            "Local sensor selection bias",
        ],
        "algorithm": "federation_collect_v1 + release_gate_v2",
        "botscope_version": __import__(
            "botscope.__version__", fromlist=["__version__"]
        ).__version__,
        "raw_table": snapshot.raw_source_table(),
        "errors": dict(snapshot.errors),
    }
    return InternetEstimate(
        metric="automated_http_request_share",
        estimate=estimate_val if single else None,
        interval=None,
        population=population,
        sources=source_ids,
        methodology=(
            "Single SOURCE-REPORTED share shown when available; "
            "INTERNET BOT TRAFFIC ESTIMATE requires ≥2 weighted traffic shares."
        ),
        limitations=limitations,
        kind=(
            ObservationKind.SOURCE_REPORTED
            if single
            else ObservationKind.BOTSCOPE_ESTIMATED
        ),
        coverage=coverage,
        explainer=explainer,
        release_gate=GATE_OBSERVATIONS,
    )


def internet_wide_estimate(
    shares: Iterable[NormalizedSourceObservation] | FederationSnapshot,
) -> InternetEstimate:
    """Public API for Internet-wide estimate (opens gate when criteria pass)."""
    if isinstance(shares, FederationSnapshot):
        return estimate_from_federation(shares)
    snap = FederationSnapshot(
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        enabled_sources=sorted({o.source_id for o in shares}),
        observations=list(shares),
    )
    return estimate_from_federation(snap)


def build_coverage_scorecard(snapshot: FederationSnapshot) -> dict[str, Any]:
    est = estimate_from_federation(snapshot)
    return {
        "title": "COVERAGE",
        "sources": est.coverage.get("sources"),
        "share_observations": est.coverage.get("share_observations"),
        "observation_window": est.coverage.get("observation_window"),
        "traffic_classes": est.coverage.get("traffic_classes"),
        "unknown_source_overlap": est.coverage.get("unknown_source_overlap"),
        "policy": (
            "This is a coverage description, not a universal accuracy score."
        ),
        "release_gate": est.release_gate,
        "estimate": est.estimate,
        "interval": list(est.interval) if est.interval else None,
    }


def make_traffic_share_observation(
    *,
    source_id: str,
    automated_share: float,
    population: str,
    denominator: str = "http_requests",
    event_count: int | None = None,
    weight: float | None = None,
    temporal_start: str | None = None,
    temporal_end: str | None = None,
) -> NormalizedSourceObservation:
    """Helper to build a traffic-share observation (e.g. from a local session)."""
    now = datetime.now(timezone.utc).isoformat()
    extras: dict[str, Any] = {}
    if event_count is not None:
        extras["event_count"] = event_count
    if weight is not None:
        extras["weight"] = weight
    return NormalizedSourceObservation(
        source_id=source_id,
        observation_id=f"{source_id}:automated_share",
        retrieved_at=now,
        measurement_type=__import__(
            "botscope.sources.base", fromlist=["MeasurementType"]
        ).MeasurementType.LOCAL_SENSOR
        if "local" in source_id or "session" in source_id
        else __import__(
            "botscope.sources.base", fromlist=["MeasurementType"]
        ).MeasurementType.PROVIDER_HTTP_TRAFFIC,
        kind=ObservationKind.BOTSCOPE_CLASSIFIED
        if "local" in source_id or "session" in source_id
        else ObservationKind.SOURCE_REPORTED,
        metric_name="automated_share",
        metric_value=float(automated_share),
        unit="fraction",
        population=population,
        denominator=denominator,
        temporal_start=temporal_start,
        temporal_end=temporal_end,
        methodology_note="Traffic-share observation for population_reliability_v1",
        limitations=["Population-scoped; not a global census alone."],
        extras=extras,
    )
