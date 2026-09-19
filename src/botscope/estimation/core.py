"""Estimation helpers — local shares + Internet-wide engine.

Status: IMPLEMENTED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from botscope.estimation.internet import (
    InternetEstimate,
)
from botscope.estimation.internet import (
    internet_wide_estimate as _internet_wide_estimate,
)


@dataclass
class LocalShareEstimate:
    automated: float | None
    human_likely: float | None
    unknown: float | None
    denominator: str
    population: str
    caveat: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "automated": self.automated,
            "human_likely": self.human_likely,
            "unknown": self.unknown,
            "denominator": self.denominator,
            "population": self.population,
            "caveat": self.caveat,
            "status": "IMPLEMENTED",
        }


def local_share_estimate(
    automated: float | None,
    human_likely: float | None,
    unknown: float | None,
    *,
    denominator: str = "requests",
    population: str = "local sensor / authorized log corpus",
) -> LocalShareEstimate:
    return LocalShareEstimate(
        automated=automated,
        human_likely=human_likely,
        unknown=unknown,
        denominator=denominator,
        population=population,
        caveat=(
            "These shares describe only the analyzed population. "
            "Combine with additional traffic-share sources via "
            "botscope.estimation.internet_wide_estimate for a gated Internet headline."
        ),
    )


def internet_wide_estimate(*args: Any, **kwargs: Any) -> InternetEstimate:
    """Delegate to the multi-source weighting engine (gate opens when criteria pass)."""
    if args and hasattr(args[0], "observations"):
        return _internet_wide_estimate(args[0])
    if "snapshot" in kwargs:
        return _internet_wide_estimate(kwargs["snapshot"])
    if "shares" in kwargs:
        return _internet_wide_estimate(kwargs["shares"])
    if args:
        return _internet_wide_estimate(args[0])
    raise TypeError("Pass a FederationSnapshot or iterable of traffic-share observations")
