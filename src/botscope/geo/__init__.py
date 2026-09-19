"""Optional aggregate geo helpers.

Status: PARTIAL

Maps coarse country/region tags when present on events. Explicitly does
**not** claim IP address equals person location. No fake precision.
"""

from __future__ import annotations

from botscope.geo.aggregate import (
    GEO_CAVEAT,
    GeoAggregate,
    GeoCaveat,
    aggregate_geo,
)
from botscope.geo.table import GeoRecord, GeoTable, load_geo_table

__all__ = [
    "GeoAggregate",
    "GeoCaveat",
    "GEO_CAVEAT",
    "aggregate_geo",
    "GeoRecord",
    "GeoTable",
    "load_geo_table",
]
