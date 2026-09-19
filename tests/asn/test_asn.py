"""ASN table tests."""

from __future__ import annotations

import json
from pathlib import Path

from botscope.asn import AsnRecord, AsnTable, load_asn_table


def test_asn_table_lookup(tmp_path: Path) -> None:
    data = [
        {"asn": 15169, "name": "GOOGLE", "prefix": "8.8.8.0/24", "country": "US"},
        {"asn": 13335, "name": "CLOUDFLARE", "prefix": "1.1.1.0/24", "country": "US"},
    ]
    path = tmp_path / "asn.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    table = load_asn_table(path)
    assert len(table) == 2
    assert table.lookup_asn(15169).name == "GOOGLE"
    hit = table.lookup_ip("8.8.8.8")
    assert hit is not None
    assert hit.asn == 15169
    assert table.lookup_ip("9.9.9.9") is None


def test_empty_table_when_missing() -> None:
    table = load_asn_table(None)
    assert len(table) == 0
    assert isinstance(AsnTable([AsnRecord(1, "TEST")]).lookup_asn(1), AsnRecord)
