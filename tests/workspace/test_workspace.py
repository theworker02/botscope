"""Tests for Analysis Workspace persistence."""

from __future__ import annotations

from pathlib import Path

from botscope.workspace import (
    AnalysisWorkspace,
    ChartOverlay,
    load_workspace,
    save_workspace,
)


def test_workspace_roundtrip(tmp_path: Path) -> None:
    ws = AnalysisWorkspace(
        denominator="bytes",
        query='classification eq "AI CRAWLER"',
        filter_text="bot",
        chart_overlays=[ChartOverlay(chart_id="timeline", categories=["AI CRAWLER"])],
        notes=["review crawlers"],
    )
    path = save_workspace(tmp_path, ws)
    assert path.name == "workspace.json"
    loaded = load_workspace(tmp_path)
    assert loaded.denominator == "bytes"
    assert loaded.query.startswith("classification")
    assert loaded.chart_overlays[0].chart_id == "timeline"
    assert loaded.notes == ["review crawlers"]
