#!/usr/bin/env python3
"""Build JSON/Markdown reports from a demo analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

from botscope.api import Analyzer
from botscope.demo import DEMO_NOTICE, ensure_demo_log
from botscope.reports.generator import export_json, export_markdown


def main() -> None:
    print(DEMO_NOTICE)
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    with tempfile.TemporaryDirectory() as tmp:
        md = export_markdown(result.report, Path(tmp) / "report.md")
        js = export_json(result.report, Path(tmp) / "report.json")
        print("markdown:", md, "bytes=", md.stat().st_size)
        print("json:", js, "bytes=", js.stat().st_size)
        print(md.read_text(encoding="utf-8")[:400])


if __name__ == "__main__":
    main()
