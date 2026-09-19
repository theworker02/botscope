"""Published range loader + Analyzer identity integration."""

from __future__ import annotations

from datetime import datetime, timezone

from botscope.api.analyzer import Analyzer
from botscope.asn import AsnRecord, AsnTable
from botscope.identity import (
    IdentityStatus,
    index_from_prefix_documents,
    load_published_range_index,
)
from botscope.normalize.event import NormalizedEvent


GOOGLE_DOC = {
    "creationTime": "2026-09-18T00:00:00.000000",
    "prefixes": [{"ipv4Prefix": "66.249.64.0/24"}],
}
BING_DOC = {
    "creationTime": "2026-09-18T00:00:00.000000",
    "prefixes": [{"ipv4Prefix": "40.77.167.0/24"}],
}


def test_index_from_prefix_documents() -> None:
    index = index_from_prefix_documents(
        google_common=GOOGLE_DOC,
        bing=BING_DOC,
    )
    assert len(index) >= 2
    assert "google" in index.operators_for_ip("66.249.64.10")
    assert "microsoft" in index.operators_for_ip("40.77.167.5")


def test_load_disabled_returns_empty() -> None:
    index, status = load_published_range_index(enabled=False)
    assert len(index) == 0
    assert status["enabled"] is False


def test_analyzer_verifies_googlebot_via_injected_ranges() -> None:
    index = index_from_prefix_documents(google_common=GOOGLE_DOC)
    analyzer = Analyzer(use_identity_ranges=False, range_index=index)
    event = NormalizedEvent(
        timestamp=datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc),
        user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)",
        src_address="66.249.64.12",
        path="/",
    )
    result = analyzer.classify_event(event)
    assert result.identity_status == IdentityStatus.VERIFIED.value
    assert any("published crawler ranges" in e.statement.lower() for e in result.evidence)


def test_analyzer_unverified_without_ranges() -> None:
    analyzer = Analyzer(use_identity_ranges=False)
    event = NormalizedEvent(
        timestamp=datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc),
        user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)",
        src_address="66.249.64.12",
        path="/",
    )
    result = analyzer.classify_event(event)
    assert result.identity_status == IdentityStatus.UNVERIFIED_CLAIM.value


def test_analyzer_asn_enrichment_before_classify() -> None:
    table = AsnTable(
        [
            AsnRecord(asn=15169, name="GOOGLE", prefix="66.249.64.0/24"),
        ]
    )
    analyzer = Analyzer(use_identity_ranges=False, asn_table=table)
    event = NormalizedEvent(
        timestamp=datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc),
        user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)",
        src_address="66.249.64.20",
        path="/",
    )
    # Enrichment happens inside classify_event
    result = analyzer.classify_event(event)
    # ASN + network_owner from table should verify without CIDR index
    assert result.identity_status == IdentityStatus.VERIFIED.value
    assert result.attribution == "Googlebot"
