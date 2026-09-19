"""Calibration metric tests (synthetic labeled pairs — not marketing numbers)."""

from __future__ import annotations

from botscope.calibration import brier_score, calibrate_report, expected_calibration_error


def test_perfect_calibration() -> None:
    conf = [0.0, 0.0, 1.0, 1.0]
    correct = [False, False, True, True]
    assert brier_score(conf, correct) == 0.0
    assert expected_calibration_error(conf, correct, n_bins=2) == 0.0


def test_calibrate_report_shape() -> None:
    conf = [0.1, 0.2, 0.8, 0.9]
    correct = [False, True, True, False]
    report = calibrate_report(conf, correct, n_bins=5)
    assert report.n == 4
    assert 0.0 <= report.brier <= 1.0
    assert 0.0 <= report.ece <= 1.0
    assert len(report.bins) == 5
    assert "heuristic" in report.note.lower()
