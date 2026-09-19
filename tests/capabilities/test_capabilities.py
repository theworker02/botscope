"""Capability / botcard / annotations / estimation smoke tests."""

from __future__ import annotations

from botscope.annotations import AnnotationStore
from botscope.botcard import load_library
from botscope.capabilities import FeatureStatus, list_features
from botscope.estimation import internet_wide_estimate, local_share_estimate


def test_features_and_botcards():
    feats = list_features()
    assert feats
    assert any(f.status is FeatureStatus.IMPLEMENTED for f in feats)
    lib = load_library()
    assert lib.cards


def test_estimation_internet_gate():
    from botscope.estimation import GATE_ESTIMATE, GATE_OBSERVATIONS, make_traffic_share_observation
    from botscope.sources.federation import FederationSnapshot

    est = local_share_estimate(0.5, 0.3, 0.2)
    assert est.to_dict()["status"] == "IMPLEMENTED"

    empty = internet_wide_estimate(
        FederationSnapshot(
            retrieved_at="2026-09-18T00:00:00+00:00",
            enabled_sources=[],
            observations=[],
        )
    )
    assert empty.release_gate == GATE_OBSERVATIONS

    opened = internet_wide_estimate(
        [
            make_traffic_share_observation(
                source_id="cloudflare.radar",
                automated_share=0.4,
                population="Cloudflare HTTP",
                weight=0.5,
            ),
            make_traffic_share_observation(
                source_id="botscope.local_sensor",
                automated_share=0.6,
                population="Local sensor",
                event_count=1000,
            ),
        ]
    )
    assert opened.release_gate == GATE_ESTIMATE
    assert opened.estimate is not None


def test_annotations(tmp_path):
    store = AnnotationStore(tmp_path)
    ann = store.add("session-1", "Interesting cluster", tags=["note"], author="tester")
    assert ann.body
    listed = store.list_annotations("session-1")
    assert len(listed) == 1
    store.close()
