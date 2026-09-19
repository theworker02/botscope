"""Published crawler IP-range adapters (fixtures, no network)."""

from __future__ import annotations

import json
from pathlib import Path

from botscope.sources.bot_identity import BingbotRangesSource, GoogleCrawlerRangesSource
from botscope.sources.bot_identity.cidr_util import ip_in_networks, parse_prefix_list
from botscope.sources.federation import zero_auth_federation
from botscope.sources.registry import zero_auth_entries

SAMPLE = {
    "creationTime": "2026-09-18T00:00:00.000000",
    "prefixes": [
        {"ipv4Prefix": "192.0.2.0/24"},
        {"ipv6Prefix": "2001:db8::/32"},
    ],
}


def test_parse_and_contains() -> None:
    nets = parse_prefix_list(SAMPLE)
    assert len(nets) == 2
    assert ip_in_networks("192.0.2.10", nets)
    assert not ip_in_networks("198.51.100.1", nets)


def test_google_normalize_both_kinds() -> None:
    src = GoogleCrawlerRangesSource()
    response = {
        "common": {"payload": SAMPLE, "receipt": None},
        "special": {
            "payload": {
                "creationTime": "2026-09-18T00:00:00.000000",
                "prefixes": [{"ipv4Prefix": "198.51.100.0/24"}],
            },
            "receipt": None,
        },
    }
    obs = src.normalize(response)
    assert len(obs) == 2
    assert obs[0].metric_name.endswith("_common")
    assert obs[1].metric_value == 1


def test_bing_normalize_fixture(tmp_path: Path) -> None:
    src = BingbotRangesSource()
    raw = {"payload": SAMPLE, "receipt": None}
    assert src.validate(SAMPLE) == []
    obs = src.normalize(raw)
    assert obs[0].metric_value == 2
    assert "Bingbot" in obs[0].population
    # contains_ip via preloaded networks
    src._networks = parse_prefix_list(SAMPLE)
    assert src.contains_ip("192.0.2.1")


def test_federation_includes_bing() -> None:
    fed = zero_auth_federation()
    assert "bing.bingbot_ip_ranges" in fed.sources
    assert "bing.bingbot_ip_ranges" in fed.enabled
    assert any(e.source_id == "bing.bingbot_ip_ranges" for e in zero_auth_entries())


def test_google_fixture_file_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "ranges.json"
    path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    src = GoogleCrawlerRangesSource()
    assert src.validate(data) == []
