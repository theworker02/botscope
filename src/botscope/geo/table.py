"""Optional offline coarse country table (CSV/JSON), mirroring ASN shape.

Status: PARTIAL — never invents coordinates; stamps extras only.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import Any, Iterator

from botscope.geo.aggregate import GEO_CAVEAT


@dataclass(frozen=True)
class GeoRecord:
    prefix: str
    country: str
    region: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "prefix": self.prefix,
            "country": self.country,
            "region": self.region,
        }


class GeoTable:
    """Prefix → coarse country codes from a local file (no network)."""

    def __init__(self, records: list[GeoRecord] | None = None) -> None:
        self._prefixes: list[tuple[Any, GeoRecord]] = []
        for record in records or []:
            self.add(record)

    def add(self, record: GeoRecord) -> None:
        try:
            net = ip_network(record.prefix, strict=False)
        except ValueError:
            return
        self._prefixes.append((net, record))

    def __len__(self) -> int:
        return len(self._prefixes)

    def lookup_ip(self, address: str) -> GeoRecord | None:
        try:
            ip = ip_address(address)
        except ValueError:
            return None
        for net, record in self._prefixes:
            if ip in net:
                return record
        return None

    def iter_records(self) -> Iterator[GeoRecord]:
        for _, record in self._prefixes:
            yield record


def load_geo_table(path: str | Path | None = None) -> GeoTable:
    """Load optional offline geo prefix table (JSON list or CSV)."""
    if path is None:
        return GeoTable()
    path = Path(path)
    if not path.exists():
        return GeoTable()
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        records = [
            GeoRecord(
                prefix=str(row["prefix"]),
                country=str(row.get("country") or row.get("cc") or "ZZ").upper()[:8],
                region=row.get("region"),
            )
            for row in data
            if row.get("prefix")
        ]
        return GeoTable(records)
    records = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get("prefix"):
                continue
            records.append(
                GeoRecord(
                    prefix=str(row["prefix"]),
                    country=str(row.get("country") or row.get("cc") or "ZZ").upper()[:8],
                    region=row.get("region") or None,
                )
            )
    return GeoTable(records)


def geo_table_caveat() -> str:
    return GEO_CAVEAT
