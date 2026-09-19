"""Federation unit tests (fixtures + optional network)."""

from __future__ import annotations

from pathlib import Path

import pytest

from botscope.estimation.internet import estimate_from_federation
from botscope.sources.commoncrawl import CommonCrawlCatalogSource
from botscope.sources.federation import FederationSnapshot, zero_auth_federation
from botscope.sources.registry import REGISTRY, zero_auth_entries

FIXTURES = Path(__file__).parent / "fixtures"


def test_registry_has_zero_auth_sources() -> None:
    entries = zero_auth_entries()
    assert any(e.source_id == "commoncrawl.collinfo" for e in entries)
    assert any(e.source_id == "google.crawler_ip_ranges" for e in entries)
    assert any(e.source_id == "bing.bingbot_ip_ranges" for e in entries)
    radar = next(e for e in REGISTRY if e.source_id == "cloudflare.radar")
    assert radar.authentication_required is True


def test_commoncrawl_normalize_fixture() -> None:
    sample = [
        {
            "id": "CC-MAIN-TEST",
            "name": "Test Index",
            "cdx-api": "https://index.commoncrawl.org/CC-MAIN-TEST-index",
            "from": "2026-01-01T00:00:00",
            "to": "2026-01-02T00:00:00",
        }
    ]
    src = CommonCrawlCatalogSource()
    obs = src.normalize({"collinfo": sample, "receipt": None})
    assert obs[0].metric_name == "published_crawl_index_count"
    assert obs[0].metric_value == 1
    assert "WEB CRAWL" in (obs[0].extras.get("perspective") or "")
    assert any("not a traffic" in x.lower() or "not" in x.lower() for x in obs[0].limitations)


def test_release_gate_refuses_internet_headline() -> None:
    snap = FederationSnapshot(
        retrieved_at="2026-09-18T00:00:00+00:00",
        enabled_sources=["commoncrawl.collinfo"],
        observations=[],
    )
    est = estimate_from_federation(snap)
    assert est.release_gate == "MULTI-SOURCE BOT TRAFFIC OBSERVATIONS"
    assert est.to_dict()["internet_bot_traffic_headline_allowed"] is False


def test_cloudflare_disabled_by_default() -> None:
    fed = zero_auth_federation()
    assert "cloudflare.radar" not in fed.enabled
    assert "commoncrawl.collinfo" in fed.enabled


@pytest.mark.network
def test_commoncrawl_live_fetch() -> None:
    src = CommonCrawlCatalogSource()
    report = src.availability()
    assert report.status.value in {
        "ACTIVE",
        "AVAILABLE",
        "OFFLINE_CACHED",
        "CACHED",
        "DEGRADED",
        "UNAVAILABLE",
    }
    if report.status.value == "UNAVAILABLE":
        pytest.skip(f"Common Crawl unreachable: {report.detail}")
    raw = src.fetch()
    assert isinstance(raw["collinfo"], list)
    assert len(raw["collinfo"]) > 0
    obs = src.normalize(raw)
    assert obs[0].receipt_id or raw["receipt"].receipt_id
