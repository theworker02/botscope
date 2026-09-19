"""Export pipeline tests."""

from __future__ import annotations

from pathlib import Path

from botscope.api.analyzer import Analyzer
from botscope.demo import ensure_demo_log
from botscope.export import export_analysis


def test_export_analysis_multi_format(tmp_path: Path) -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    job = export_analysis(
        result,
        output_dir=tmp_path,
        formats=("json", "markdown", "html", "csv"),
    )
    assert len(job.artifacts) == 4
    for art in job.artifacts:
        assert art.path.exists()
        assert art.path.stat().st_size > 0
