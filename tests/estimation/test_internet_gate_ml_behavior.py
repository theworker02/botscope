"""Tests for Internet estimate gate opening + ML + behavior IMPLEMENTED status."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from botscope.behavior import profile_by_source
from botscope.classify.engine import Classifier
from botscope.classify.ml import MlModel
from botscope.estimation import (
    GATE_ESTIMATE,
    GATE_OBSERVATIONS,
    estimate_from_federation,
    internet_wide_estimate,
    make_traffic_share_observation,
)
from botscope.normalize.event import NormalizedEvent, SourceType
from botscope.sources.base import SourceQuery
from botscope.sources.federation import FederationSnapshot
from botscope.sources.local import LocalSensorSource


def test_internet_gate_opens_with_two_weighted_shares() -> None:
    shares = [
        make_traffic_share_observation(
            source_id="cloudflare.radar",
            automated_share=0.40,
            population="Cloudflare-observed HTTP",
            temporal_start="2026-09-01T00:00:00+00:00",
            temporal_end="2026-09-18T00:00:00+00:00",
            weight=0.5,
        ),
        make_traffic_share_observation(
            source_id="botscope.local_sensor",
            automated_share=0.60,
            population="Authorized local sensor",
            temporal_start="2026-09-01T00:00:00+00:00",
            temporal_end="2026-09-18T00:00:00+00:00",
            event_count=10_000,
        ),
    ]
    snap = FederationSnapshot(
        retrieved_at="2026-09-18T00:00:00+00:00",
        enabled_sources=["cloudflare.radar", "botscope.local_sensor"],
        observations=shares,
    )
    est = estimate_from_federation(snap)
    assert est.release_gate == GATE_ESTIMATE
    assert est.to_dict()["internet_bot_traffic_headline_allowed"] is True
    assert est.estimate is not None
    assert est.interval is not None
    assert 0.0 <= est.estimate <= 1.0
    assert est.explainer["weighting_model"] == "population_reliability_v1"

    via_api = internet_wide_estimate(snap)
    assert via_api.release_gate == GATE_ESTIMATE


def test_internet_gate_stays_closed_without_shares() -> None:
    snap = FederationSnapshot(
        retrieved_at="2026-09-18T00:00:00+00:00",
        enabled_sources=["commoncrawl.collinfo"],
        observations=[],
    )
    est = estimate_from_federation(snap)
    assert est.release_gate == GATE_OBSERVATIONS
    assert est.to_dict()["internet_bot_traffic_headline_allowed"] is False


def test_local_sensor_emits_share() -> None:
    src = LocalSensorSource()
    raw = src.fetch(
        SourceQuery(extras={"automated_share": 0.55, "event_count": 100})
    )
    obs = src.normalize(raw)
    assert len(obs) == 1
    assert obs[0].metric_name == "automated_share"
    assert obs[0].metric_value == 0.55


def test_ml_model_implemented_and_used() -> None:
    model = MlModel.default()
    event = NormalizedEvent(
        user_agent="Mozilla/5.0 (compatible; GPTBot/1.0)",
        path="/",
        source_type=SourceType.WEB_LOG,
    )
    pred = model.predict(event)
    assert pred is not None
    assert pred.to_dict()["status"] == "IMPLEMENTED"
    assert pred.probabilities
    clf = Classifier(ml_model=model)
    result = clf.classify(event)
    assert "ml" in result.extras
    assert "advisory only" not in " ".join(e.statement for e in result.evidence).lower()


def test_behavior_implemented_fields() -> None:
    base = datetime.now(timezone.utc)
    events = [
        NormalizedEvent(
            timestamp=base + timedelta(seconds=i),
            src_address="9.9.9.9",
            path=f"/p{i % 2}",
            http_method="GET",
            user_agent="bot",
            classification="AI CRAWLER",
            source_type=SourceType.WEB_LOG,
        )
        for i in range(6)
    ]
    profiles = profile_by_source(events)
    assert profiles[0].to_dict()["status"] == "IMPLEMENTED"
    assert profiles[0].bot_like_score >= 0
    assert profiles[0].automation_fraction == 1.0
    assert profiles[0].path_entropy >= 0
