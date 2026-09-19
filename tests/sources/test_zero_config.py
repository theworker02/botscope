"""Zero-config credential policy tests."""

from __future__ import annotations

from botscope.sources.base import AuthenticationMode
from botscope.sources.federation import default_sources, zero_auth_federation


def test_no_auth_required_for_default_enabled_sources() -> None:
    fed = zero_auth_federation()
    for sid in fed.enabled:
        src = fed.sources[sid]
        assert src.authentication == AuthenticationMode.NONE, (
            f"{sid} is enabled but requires auth — breaks zero-config"
        )


def test_radar_is_optional_and_disabled() -> None:
    fed = zero_auth_federation()
    assert "cloudflare.radar" in fed.sources
    assert "cloudflare.radar" not in fed.enabled
    assert fed.sources["cloudflare.radar"].authentication == AuthenticationMode.REQUIRED_TOKEN


def test_majority_of_providers_are_zero_auth() -> None:
    sources = default_sources()
    zero = sum(1 for s in sources if s.authentication == AuthenticationMode.NONE)
    assert zero >= 10
    assert zero / len(sources) >= 0.8
