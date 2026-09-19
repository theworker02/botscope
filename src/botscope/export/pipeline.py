"""Unified multi-format export jobs for Observatory / CLI / Python API."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from botscope.api.analyzer import AnalysisResult
from botscope.normalize.event import NormalizedEvent
from botscope.reports.generator import (
    build_report,
    export_csv_categories,
    export_html,
    export_json,
    export_markdown,
)
from botscope.statistics.aggregate import ObservatoryStats, aggregate_events


@dataclass
class ExportArtifact:
    format: str
    path: Path

    def to_dict(self) -> dict[str, Any]:
        return {"format": self.format, "path": str(self.path)}


@dataclass
class ExportJob:
    """Describe and run a multi-format export into an output directory."""

    output_dir: Path
    formats: Sequence[str] = ("json", "markdown", "html", "csv")
    stem: str = "botscope_report"
    artifacts: list[ExportArtifact] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def run(
        self,
        report: dict[str, Any],
    ) -> list[ExportArtifact]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        writers = {
            "json": (export_json, f"{self.stem}.json"),
            "markdown": (export_markdown, f"{self.stem}.md"),
            "html": (export_html, f"{self.stem}.html"),
            "csv": (export_csv_categories, f"{self.stem}_categories.csv"),
        }
        self.artifacts = []
        for fmt in self.formats:
            key = fmt.lower()
            if key not in writers:
                raise ValueError(f"Unsupported export format: {fmt}")
            writer, name = writers[key]
            path = writer(report, self.output_dir / name)
            self.artifacts.append(ExportArtifact(format=key, path=path))
        return list(self.artifacts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "formats": list(self.formats),
            "stem": self.stem,
            "generated_at": self.generated_at,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


def export_analysis(
    result: AnalysisResult | None = None,
    *,
    events: Iterable[NormalizedEvent] | None = None,
    stats: ObservatoryStats | None = None,
    output_dir: str | Path,
    formats: Sequence[str] = ("json", "markdown", "html", "csv"),
    is_demo: bool = False,
    stem: str = "botscope_report",
) -> ExportJob:
    """Build a report from an AnalysisResult (or events/stats) and export."""
    if result is not None:
        report = result.report or build_report(
            result.stats, events=result.events, is_demo=result.is_demo
        )
        demo = result.is_demo
    else:
        event_list = list(events or [])
        st = stats or aggregate_events(event_list, is_demo=is_demo)
        report = build_report(st, events=event_list, is_demo=is_demo)
        demo = is_demo
    if demo and not report.get("demo_notice"):
        report = dict(report)
        report["demo_notice"] = "DEMO DATA — not real measurements."
    job = ExportJob(output_dir=Path(output_dir), formats=formats, stem=stem)
    job.run(report)
    return job
