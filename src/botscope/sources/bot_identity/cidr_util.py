"""Shared helpers for published crawler IP-range JSON feeds."""

from __future__ import annotations

import ipaddress
from typing import Any


def parse_prefix_list(data: dict[str, Any]) -> list[ipaddress._BaseNetwork]:
    """Parse Google/Bing-style ``prefixes`` arrays into network objects."""
    nets: list[ipaddress._BaseNetwork] = []
    for item in data.get("prefixes") or []:
        if not isinstance(item, dict):
            continue
        cidr = (
            item.get("ipv4Prefix")
            or item.get("ipv6Prefix")
            or item.get("ipv4")
            or item.get("ipv6")
        )
        if not cidr:
            continue
        try:
            nets.append(ipaddress.ip_network(str(cidr), strict=False))
        except ValueError:
            continue
    return nets


def validate_prefix_document(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["expected JSON object"]
    if "prefixes" not in data:
        return ["SOURCE SCHEMA CHANGED: missing prefixes"]
    if not isinstance(data["prefixes"], list):
        return ["prefixes must be a list"]
    return []


def ip_in_networks(address: str, networks: list[ipaddress._BaseNetwork]) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in net for net in networks)
