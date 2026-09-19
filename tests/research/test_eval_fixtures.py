"""Research methodology companion tests."""

from __future__ import annotations

from botscope.datasets import labeled_mini_eval, load_labeled_mini


def test_labeled_mini_loads() -> None:
    rows = load_labeled_mini()
    assert len(rows) >= 6
    assert "label" in rows[0]


def test_labeled_mini_classifier_eval() -> None:
    report = labeled_mini_eval()
    assert report.n == len(load_labeled_mini())
    assert report.accuracy >= 0.875
