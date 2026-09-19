"""Shared live-event classify + privacy loop for workers and CLI.

Status: IMPLEMENTED
"""

from __future__ import annotations

from botscope.classify.engine import Classifier
from botscope.identity import IdentityEngine, load_published_range_index
from botscope.normalize.event import NormalizedEvent
from botscope.privacy.transforms import PrivacyConfig, PrivacyTransform
from botscope.signatures.store import SignatureStore


def build_live_classifier() -> Classifier:
    """Classifier with published crawler ranges (cache-first)."""
    signatures = SignatureStore.load_bundled()
    index, _status = load_published_range_index()
    identity = IdentityEngine(signatures, range_index=index)
    return Classifier(signatures=signatures, identity=identity)


def classify_live_event(
    event: NormalizedEvent,
    *,
    classifier: Classifier | None = None,
    privacy: PrivacyConfig | PrivacyTransform | None = None,
    sensor_id: str | None = None,
) -> NormalizedEvent:
    """Apply privacy + classify; optionally stamp ``sensor_id``."""
    clf = classifier or build_live_classifier()
    if isinstance(privacy, PrivacyTransform):
        transform = privacy
    else:
        transform = PrivacyTransform(privacy or PrivacyConfig())
    event = transform.apply(event)
    if sensor_id and not event.sensor_id:
        event = event.model_copy(update={"sensor_id": sensor_id})
    result = clf.classify(event)
    return event.with_classification(
        category=result.category.value,
        confidence=result.confidence,
        evidence=[
            ("+ " if e.polarity == "for" else "- ") + e.statement for e in result.evidence
        ],
    )
