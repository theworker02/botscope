"""Coarse geo aggregation with mandatory scientific caveats."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from botscope.normalize.event import NormalizedEvent

GEO_CAVEAT = (
    "IP geolocation indicates network registration / routing affinity, "
    "not the physical location of a person. Treat country codes as coarse "
    "sensor metadata only. BotScope does not invent coordinates."
)


@dataclass(frozen=True)
class GeoCaveat:
    text: str = GEO_CAVEAT

    def to_dict(self) -> dict[str, str]:
        return {"caveat": self.text}


@dataclass
class GeoAggregate:
    """Counts of coarse country / region tags found on events."""

    by_country: dict[str, int] = field(default_factory=dict)
    tagged_events: int = 0
    untagged_events: int = 0
    caveat: str = GEO_CAVEAT

    def to_dict(self) -> dict[str, Any]:
        return {
            "by_country": dict(self.by_country),
            "tagged_events": self.tagged_events,
            "untagged_events": self.untagged_events,
            "caveat": self.caveat,
        }


def _country_of(event: NormalizedEvent) -> str | None:
    extras = event.extras or {}
    for key in ("country", "country_code", "geo_country", "cc"):
        value = extras.get(key)
        if value:
            return str(value).upper()[:8]
    return None


def aggregate_geo(events: Iterable[NormalizedEvent]) -> GeoAggregate:
    counts: Counter[str] = Counter()
    tagged = 0
    untagged = 0
    for event in events:
        cc = _country_of(event)
        if cc:
            counts[cc] += 1
            tagged += 1
        else:
            untagged += 1
    return GeoAggregate(
        by_country=dict(counts.most_common()),
        tagged_events=tagged,
        untagged_events=untagged,
    )
