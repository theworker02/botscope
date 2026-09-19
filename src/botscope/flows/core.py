"""Flow aggregation from normalized events.

Status: PARTIAL
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from botscope.normalize.event import NormalizedEvent


@dataclass
class FlowRecord:
    src_address: str | None
    dst_address: str | None
    dst_port: int | None
    events: int
    bytes_out: int
    bytes_in: int
    first_ts: str | None
    last_ts: str | None
    majority_classification: str | None = None
    classifications: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "src_address": self.src_address,
            "dst_address": self.dst_address,
            "dst_port": self.dst_port,
            "events": self.events,
            "bytes_out": self.bytes_out,
            "bytes_in": self.bytes_in,
            "first_ts": self.first_ts,
            "last_ts": self.last_ts,
            "majority_classification": self.majority_classification,
            "classifications": dict(self.classifications or {}),
            "status": "PARTIAL",
        }


def aggregate_flows(events: Iterable[NormalizedEvent]) -> list[FlowRecord]:
    buckets: dict[tuple, list[NormalizedEvent]] = {}
    for e in events:
        key = (e.src_address, e.dst_address, e.dst_port)
        buckets.setdefault(key, []).append(e)
    out: list[FlowRecord] = []
    for (src, dst, port), items in buckets.items():
        stamps = [e.timestamp for e in items if e.timestamp]
        cats = Counter(e.classification or "UNCLASSIFIED" for e in items)
        majority = cats.most_common(1)[0][0] if cats else None
        out.append(
            FlowRecord(
                src_address=src,
                dst_address=dst,
                dst_port=port,
                events=len(items),
                bytes_out=sum(e.bytes_out or 0 for e in items),
                bytes_in=sum(e.bytes_in or 0 for e in items),
                first_ts=min(stamps).isoformat() if stamps else None,
                last_ts=max(stamps).isoformat() if stamps else None,
                majority_classification=majority,
                classifications=dict(cats),
            )
        )
    out.sort(key=lambda f: f.events, reverse=True)
    return out
