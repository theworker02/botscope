"""Research export + citation tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

from botscope.api import Analyzer
from botscope.demo import ensure_demo_log
from botscope.research import build_research_bundle, citation_plain


def test_research_bundle_and_citation(tmp_path: Path):
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    out = build_research_bundle(
        result.events, tmp_path / "bundle.zip", report=result.report, is_demo=True
    )
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert "events.jsonl" in names
    assert "provenance.json" in names
    assert "quality_scorecard.json" in names
    assert "citation.json" in names
    text = citation_plain()
    assert "BotScope" in text
    assert "DOI" not in text
