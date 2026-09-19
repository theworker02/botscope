"""Enrich / geo table / flows / behavior / ML scaffold tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from botscope.asn import load_asn_table
from botscope.behavior import profile_by_source
from botscope.classify.engine import Classifier
from botscope.classify.ml import MlModel
from botscope.enrich import enrich_event, enrichment_status
from botscope.flows import aggregate_flows
from botscope.geo import aggregate_geo, load_geo_table
from botscope.normalize.event import NormalizedEvent, SourceType


def test_geo_table_and_enrich(tmp_path: Path) -> None:
    geo_path = Path("datasets/fixtures/geo_sample.json")
    if not geo_path.exists():
        geo_path = tmp_path / "geo.json"
        geo_path.write_text(
            '[{"prefix": "203.0.113.0/24", "country": "ZZ"}]',
            encoding="utf-8",
        )
    asn_path = Path("datasets/fixtures/asn_sample.json")
    geo = load_geo_table(geo_path)
    asn = load_asn_table(asn_path) if asn_path.exists() else None
    event = NormalizedEvent(
        src_address="203.0.113.5",
        source_type=SourceType.WEB_LOG,
    )
    enriched = enrich_event(event, asn_table=asn, geo_table=geo)
    assert enriched.extras.get("country") == "ZZ"
    agg = aggregate_geo([enriched])
    assert agg.tagged_events == 1
    st = enrichment_status()
    assert "enrich_event composer" in st["available"]


def test_flows_and_behavior() -> None:
    base = datetime.now(timezone.utc)
    events = [
        NormalizedEvent(
            timestamp=base,
            src_address="1.1.1.1",
            dst_address="2.2.2.2",
            dst_port=80,
            bytes_out=10,
            bytes_in=5,
            classification="AI CRAWLER",
            path="/a",
            http_method="GET",
            status=200,
            source_type=SourceType.WEB_LOG,
        ),
        NormalizedEvent(
            timestamp=base + timedelta(seconds=2),
            src_address="1.1.1.1",
            dst_address="2.2.2.2",
            dst_port=80,
            bytes_out=20,
            bytes_in=7,
            classification="AI CRAWLER",
            path="/b",
            http_method="GET",
            status=200,
            source_type=SourceType.WEB_LOG,
        ),
    ]
    flows = aggregate_flows(events)
    assert len(flows) == 1
    assert flows[0].bytes_in == 12
    assert flows[0].majority_classification == "AI CRAWLER"
    profiles = profile_by_source(events)
    assert profiles[0].mean_inter_arrival_s is not None
    assert profiles[0].majority_classification == "AI CRAWLER"


def test_ml_scaffold_advisory_only() -> None:
    model = MlModel()
    event = NormalizedEvent(
        user_agent="Googlebot/2.1",
        path="/robots.txt",
        source_type=SourceType.WEB_LOG,
    )
    pred = model.predict(event)
    assert pred is not None
    assert pred.score > 0
    assert pred.to_dict()["status"] == "IMPLEMENTED"
    clf = Classifier(ml_model=model)
    result = clf.classify(event)
    assert "ml" in result.extras or any("ML model" in e.statement for e in result.evidence)
