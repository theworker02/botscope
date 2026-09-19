"""Enrichment helpers.

Status: PARTIAL — local/optional only; network enrichment OFF unless explicitly enabled.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from typing import Any

from botscope.asn import AsnTable
from botscope.geo.aggregate import GEO_CAVEAT
from botscope.geo.table import GeoTable
from botscope.normalize.event import NormalizedEvent, ProvenanceLevel


@dataclass
class EnrichmentResult:
    field: str
    value: Any
    provenance: ProvenanceLevel = ProvenanceLevel.INFERRED
    source: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "provenance": self.provenance.value,
            "source": self.source,
        }


def apply_static_tags(event: NormalizedEvent, tags: dict[str, Any]) -> NormalizedEvent:
    """Attach local static tags into extras (does not call the network)."""
    extras = dict(event.extras)
    extras["static_tags"] = dict(tags)
    return event.model_copy(update={"extras": extras})


def apply_asn(event: NormalizedEvent, asn_table: AsnTable | None) -> NormalizedEvent:
    if not asn_table or not event.src_address:
        return event
    if event.asn is not None and event.network_owner:
        return event
    record = asn_table.lookup_ip(event.src_address)
    if record is None:
        return event
    updates: dict[str, Any] = {}
    if event.asn is None:
        updates["asn"] = record.asn
    if not event.network_owner:
        updates["network_owner"] = record.name
    if not updates:
        return event
    extras = dict(event.extras)
    extras["asn_enrichment"] = "offline_table"
    if record.country and "country" not in extras and "country_code" not in extras:
        extras["country"] = record.country
        extras["geo_caveat"] = GEO_CAVEAT
    updates["extras"] = extras
    return event.model_copy(update=updates)


def apply_geo(event: NormalizedEvent, geo_table: GeoTable | None) -> NormalizedEvent:
    if not geo_table or not event.src_address:
        return event
    extras = dict(event.extras)
    if extras.get("country") or extras.get("country_code"):
        return event
    record = geo_table.lookup_ip(event.src_address)
    if record is None:
        return event
    extras["country"] = record.country
    if record.region:
        extras["region"] = record.region
    extras["geo_enrichment"] = "offline_table"
    extras["geo_caveat"] = GEO_CAVEAT
    return event.model_copy(update={"extras": extras})


def reverse_dns_lookup(
    address: str,
    *,
    enabled: bool = False,
    timeout_s: float = 0.5,
) -> str | None:
    """Optional PTR lookup — OFF unless explicitly enabled (may use network)."""
    if not enabled or not address:
        return None
    previous = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout_s)
        name, _alias, _addrs = socket.gethostbyaddr(address)
        return name
    except OSError:
        return None
    finally:
        socket.setdefaulttimeout(previous)


def apply_rdns(
    event: NormalizedEvent,
    *,
    enabled: bool = False,
) -> NormalizedEvent:
    if not enabled or event.reverse_dns or not event.src_address:
        return event
    name = reverse_dns_lookup(event.src_address, enabled=True)
    if not name:
        return event
    extras = dict(event.extras)
    extras["rdns_enrichment"] = "ptr_lookup"
    return event.model_copy(update={"reverse_dns": name, "extras": extras})


def enrich_event(
    event: NormalizedEvent,
    *,
    asn_table: AsnTable | None = None,
    geo_table: GeoTable | None = None,
    static_tags: dict[str, Any] | None = None,
    rdns: bool = False,
) -> NormalizedEvent:
    """Compose offline enrichment; rDNS only when ``rdns=True``."""
    event = apply_asn(event, asn_table)
    event = apply_geo(event, geo_table)
    if static_tags:
        event = apply_static_tags(event, static_tags)
    if rdns:
        event = apply_rdns(event, enabled=True)
    return event


def enrichment_status() -> dict[str, Any]:
    rdns_env = os.environ.get("BOTSCOPE_RDNS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return {
        "status": "PARTIAL",
        "network_lookups": "OFF by default",
        "available": [
            "apply_static_tags",
            "offline_asn_table_via_BOTSCOPE_ASN_TABLE",
            "offline_geo_table_via_BOTSCOPE_GEO_TABLE",
            "enrich_event composer",
            "optional_rdns_via_BOTSCOPE_RDNS_or_flag",
        ],
        "rdns_env_enabled": rdns_env,
        "planned": [],
    }
