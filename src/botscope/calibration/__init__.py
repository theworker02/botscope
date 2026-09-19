"""Confidence calibration helpers.

Status: IMPLEMENTED (metrics only — does not retrain classifiers)

Provides Brier score, Expected Calibration Error (ECE), and reliability
diagram bin data from (confidence, correctness) pairs. Correctness must
come from labeled fixtures — never invented.
"""

from __future__ import annotations

from botscope.calibration.metrics import (
    CalibrationReport,
    ReliabilityBin,
    brier_score,
    calibrate_report,
    expected_calibration_error,
    reliability_diagram,
)

__all__ = [
    "CalibrationReport",
    "ReliabilityBin",
    "brier_score",
    "calibrate_report",
    "expected_calibration_error",
    "reliability_diagram",
]