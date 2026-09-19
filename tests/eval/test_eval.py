"""Evaluation harness tests."""

from __future__ import annotations

from botscope.eval import evaluate_labels


def test_evaluate_labels_perfect() -> None:
    y_true = ["A", "B", "A", "B"]
    y_pred = ["A", "B", "A", "B"]
    report = evaluate_labels(y_true, y_pred)
    assert report.n == 4
    assert report.accuracy == 1.0
    assert report.macro_f1 == 1.0
    assert report.micro_f1 == 1.0


def test_evaluate_labels_confusion() -> None:
    y_true = ["A", "A", "B", "B"]
    y_pred = ["A", "B", "B", "A"]
    report = evaluate_labels(y_true, y_pred)
    assert report.accuracy == 0.5
    assert report.confusion.matrix["A"]["A"] == 1
    assert report.confusion.matrix["A"]["B"] == 1
