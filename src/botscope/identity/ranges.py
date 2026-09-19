"""In-memory index of published crawler CIDR ranges for identity corroboration."""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass
class PublishedRangeIndex:
    """Maps operator tokens → published networks (never invent ranges)."""

    networks_by_operator: dict[str, list[ipaddress._BaseNetwork]] = field(default_factory=dict)

    def add(self, operator: str, networks: Iterable[ipaddress._BaseNetwork]) -> None:
        key = operator.strip().lower()
        bucket = self.networks_by_operator.setdefault(key, [])
        for net in networks:
            if net not in bucket:
                bucket.append(net)

    def add_cidrs(self, operator: str, cidrs: Iterable[str]) -> None:
        nets: list[ipaddress._BaseNetwork] = []
        for cidr in cidrs:
            try:
                nets.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                continue
        self.add(operator, nets)

    def operators_for_ip(self, address: str) -> list[str]:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return []
        hits: list[str] = []
        for operator, nets in self.networks_by_operator.items():
            if any(ip in net for net in nets):
                hits.append(operator)
        return hits

    def __len__(self) -> int:
        return sum(len(v) for v in self.networks_by_operator.values())
