"""Offline ASN lookup table loader and query helpers."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AsnRecord:
    asn: int
    name: str
    prefix: str | None = None
    country: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "asn": self.asn,
            "name": self.name,
            "prefix": self.prefix,
            "country": self.country,
        }


class AsnTable:
    """In-memory ASN directory. Prefer exact ASN field; optional prefix match."""

    def __init__(self, records: list[AsnRecord] | None = None) -> None:
        self._by_asn: dict[int, AsnRecord] = {}
        self._prefixes: list[tuple[Any, AsnRecord]] = []
        for record in records or []:
            self.add(record)

    def add(self, record: AsnRecord) -> None:
        self._by_asn[record.asn] = record
        if record.prefix:
            try:
                net = ip_network(record.prefix, strict=False)
                self._prefixes.append((net, record))
            except ValueError:
                pass

    def __len__(self) -> int:
        return len(self._by_asn)

    def lookup_asn(self, asn: int) -> AsnRecord | None:
        return self._by_asn.get(asn)

    def lookup_ip(self, address: str) -> AsnRecord | None:
        try:
            ip = ip_address(address)
        except ValueError:
            return None
        for net, record in self._prefixes:
            if ip in net:
                return record
        return None

    def iter_records(self) -> Iterator[AsnRecord]:
        yield from self._by_asn.values()


def load_asn_table(path: str | Path | None = None) -> AsnTable:
    """Load an optional offline ASN table (JSON list or CSV).

    If ``path`` is None or missing, returns an empty table (honest PARTIAL).
    """
    if path is None:
        return AsnTable()
    path = Path(path)
    if not path.exists():
        return AsnTable()
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        records = [
            AsnRecord(
                asn=int(row["asn"]),
                name=str(row.get("name") or f"AS{row['asn']}"),
                prefix=row.get("prefix"),
                country=row.get("country"),
            )
            for row in data
        ]
        return AsnTable(records)
    # CSV: asn,name,prefix,country
    records = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get("asn"):
                continue
            records.append(
                AsnRecord(
                    asn=int(row["asn"]),
                    name=str(row.get("name") or f"AS{row['asn']}"),
                    prefix=row.get("prefix") or None,
                    country=row.get("country") or None,
                )
            )
    return AsnTable(records)
