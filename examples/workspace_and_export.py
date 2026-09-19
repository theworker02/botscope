"""Example: save Analysis Workspace + export a multi-format report.

Run from repo root after `pip install -e .`:

  python examples/workspace_and_export.py
"""

from __future__ import annotations

from pathlib import Path

from botscope.api import Analyzer
from botscope.demo import ensure_demo_log
from botscope.export import export_analysis
from botscope.gui.session_io import save_analysis_session
from botscope.workspace import AnalysisWorkspace, ChartOverlay


def main() -> None:
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    out = Path("examples_output")
    out.mkdir(exist_ok=True)
    session_dir = out / "example_workspace.bscope"
    ws = AnalysisWorkspace(
        denominator="requests",
        query='classification eq "AI CRAWLER"',
        chart_overlays=[ChartOverlay(chart_id="categories", categories=["AI CRAWLER"])],
        notes=["Example workspace saved from examples/workspace_and_export.py"],
    )
    saved = save_analysis_session(
        session_dir,
        result.events,
        source_path=ensure_demo_log(),
        is_demo=True,
        workspace=ws,
        remember=False,
    )
    job = export_analysis(saved.result, output_dir=out / "reports", formats=("markdown", "json"))
    print(f"Session: {saved.path}")
    print(f"Workspace: {saved.path / 'workspace.json'}")
    for art in job.artifacts:
        print(f"Export: {art.path}")


if __name__ == "__main__":
    main()
