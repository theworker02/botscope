"""Source Fabric Phase 5 tests (deterministic, no live network)."""

from __future__ import annotations

from botscope.sources.base import SourceStatus
from botscope.sources.federation import default_sources, zero_auth_federation
from botscope.sources.registry import REGISTRY, get_entry


def test_default_sources_count_in_target_band() -> None:
    sources = default_sources()
    ids = {s.source_id for s in sources}
    # ~10–20 real providers (Radar included as optional)
    assert 10 <= len(ids) <= 20
    assert "google.crawler_ip_ranges" in ids
    assert "bing.bingbot_ip_ranges" in ids
    assert "openai.gptbot" in ids
    assert "github.meta" in ids
    assert "cloudflare.radar" in ids


def test_zero_auth_federation_disables_radar() -> None:
    fed = zero_auth_federation()
    assert "cloudflare.radar" not in fed.enabled
    assert "commoncrawl.collinfo" in fed.enabled


def test_registry_covers_federation_ids() -> None:
    fed_ids = {s.source_id for s in default_sources()}
    # Local sensor is catalog-only
    for sid in fed_ids:
        entry = get_entry(sid)
        assert entry is not None, f"missing catalog entry for {sid}"


def test_no_catalog_status_is_not_connected() -> None:
    for entry in REGISTRY:
        assert entry.status != SourceStatus.NOT_CONNECTED
        # Public zero-auth sources must not use vague NOT CONNECTED labeling
        if not entry.authentication_required:
            assert "NOT CONNECTED" not in (entry.notes or "").upper()


def test_radar_is_auth_required() -> None:
    radar = get_entry("cloudflare.radar")
    assert radar is not None
    assert radar.authentication_required is True
    assert radar.status == SourceStatus.AUTH_REQUIRED
