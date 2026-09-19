"""ASN enrichment helpers (offline table optional).

Status: PARTIAL

Looks up Autonomous System numbers from an optional local CSV/JSON table.
Does not perform live WHOIS. Network lookups remain OFF by default.
"""

from __future__ import annotations

from botscope.asn.table import (
    AsnRecord,
    AsnTable,
    load_asn_table,
)

__all__ = [
    "AsnRecord",
    "AsnTable",
    "load_asn_table",
]
