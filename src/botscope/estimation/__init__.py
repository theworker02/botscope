"""Estimation package — local shares + Internet estimates."""

from botscope.estimation.core import LocalShareEstimate, internet_wide_estimate, local_share_estimate
from botscope.estimation.internet import (
    GATE_ESTIMATE,
    GATE_OBSERVATIONS,
    InternetEstimate,
    build_coverage_scorecard,
    estimate_from_federation,
    make_traffic_share_observation,
)

__all__ = [
    "GATE_ESTIMATE",
    "GATE_OBSERVATIONS",
    "InternetEstimate",
    "LocalShareEstimate",
    "build_coverage_scorecard",
    "estimate_from_federation",
    "internet_wide_estimate",
    "local_share_estimate",
    "make_traffic_share_observation",
]
