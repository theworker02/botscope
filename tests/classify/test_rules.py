"""Classifier accuracy tests against rules + labeled fixture."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from botscope.classify.engine import Classifier
from botscope.classify.rules import RuleEngine
from botscope.classify.taxonomy import BotCategory
from botscope.datasets import labeled_mini_eval, load_labeled_mini
from botscope.identity.engine import IdentityEngine, IdentityStatus
from botscope.identity.ranges import PublishedRangeIndex
from botscope.normalize.event import NormalizedEvent
from botscope.signatures.store import SignatureStore


def _event(**kwargs) -> NormalizedEvent:
    return NormalizedEvent(
        timestamp=datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc),
        **kwargs,
    )


@pytest.mark.parametrize(
    "ua,path,expected",
    [
        ("Mozilla/5.0 (compatible; Googlebot/2.1)", "/robots.txt", BotCategory.VERIFIED_SEARCH_CRAWLER),
        ("Mozilla/5.0 (compatible; GPTBot/1.0)", "/", BotCategory.AI_CRAWLER),
        ("Mozilla/5.0 (compatible; SemrushBot/7~bl)", "/feed", BotCategory.SCRAPER),
        ("Scrapy/2.11", "/products", BotCategory.SCRAPER),
        ("python-requests/2.31", "/api/v1/items", BotCategory.API_AUTOMATION),
        ("Prometheus/2.45.0", "/metrics", BotCategory.MONITORING_HEALTH_CHECK),
        ("curl/8.0", "/health", BotCategory.MONITORING_HEALTH_CHECK),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "/index.html", BotCategory.HUMAN_LIKELY),
    ],
)
def test_rules_key_categories(ua: str, path: str, expected: BotCategory) -> None:
    clf = Classifier()
    result = clf.classify(_event(user_agent=ua, path=path))
    assert result.category == expected


def test_identity_cidr_corroboration() -> None:
    index = PublishedRangeIndex()
    index.add_cidrs("google", ["203.0.113.0/24"])
    engine = IdentityEngine(SignatureStore.load_bundled(), range_index=index)
    result = engine.verify(
        _event(
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)",
            src_address="203.0.113.10",
        )
    )
    assert result.status == IdentityStatus.VERIFIED
    assert any("published crawler ranges" in e.lower() for e in result.evidence)


def test_labeled_mini_classifier_accuracy() -> None:
    rows = load_labeled_mini()
    assert len(rows) >= 6
    report = labeled_mini_eval()
    assert report.n == len(rows)
    assert report.accuracy >= 0.875


def test_rule_engine_scraper_beats_generic() -> None:
    matches = RuleEngine().evaluate(
        _event(user_agent="Mozilla/5.0 (compatible; SemrushBot/7~bl)", path="/x")
    )
    best = max(matches, key=lambda m: m.confidence)
    assert best.category == BotCategory.SCRAPER
