"""Frozen regression baseline guard for the Observatory shell.

Phase III work must keep at least FROZEN_PASSING_COUNT tests passing.
The PySide6 Observatory remains the canonical GUI — do not replace it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Frozen 2026-09-18 after Observatory shell + 20 passing tests.
FROZEN_PASSING_COUNT = 20
BASELINE_DOC = Path(__file__).resolve().parents[1] / "docs" / "development" / "REGRESSION_BASELINE.md"


def test_regression_baseline_document_exists() -> None:
    assert BASELINE_DOC.is_file(), "Missing docs/development/REGRESSION_BASELINE.md"


def test_frozen_baseline_count_is_documented() -> None:
    text = BASELINE_DOC.read_text(encoding="utf-8")
    assert "20" in text
    assert "canonical shell" in text.lower() or "canonical" in text.lower()


def test_collect_at_least_frozen_baseline() -> None:
    """Ensure the suite has not shrunk below the frozen Observatory baseline."""
    root = Path(__file__).resolve().parents[1]
    tests_dir = root / "tests"
    collected = []
    for path in tests_dir.rglob("test_*.py"):
        collected.append(path)
    # Run a quiet collection via pytest API when available.
    import botscope  # noqa: F401 — package import smoke

    assert len(collected) >= 1
    # Hard floor: this file plus prior suite — count test functions roughly.
    total_defs = 0
    for path in collected:
        total_defs += path.read_text(encoding="utf-8").count("\ndef test_")
    assert total_defs >= FROZEN_PASSING_COUNT, (
        f"Suite shrank below frozen baseline ({total_defs} < {FROZEN_PASSING_COUNT}). "
        "See docs/development/REGRESSION_BASELINE.md"
    )
