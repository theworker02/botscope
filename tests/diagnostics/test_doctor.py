"""Diagnostics tests."""

from __future__ import annotations

from pathlib import Path

from botscope.diagnostics import doctor_report, write_doctor_bundle


def test_doctor_and_bundle(tmp_path: Path):
    report = doctor_report()
    assert report["overall"] in {"ok", "warn", "fail"}
    assert any(c["name"] == "network_contribution" for c in report["checks"])
    path = write_doctor_bundle(tmp_path / "doctor.zip")
    assert path.exists() and path.stat().st_size > 0
