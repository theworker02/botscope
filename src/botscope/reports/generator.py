"""Report generation — HTML, JSON, CSV, Markdown."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from botscope.__version__ import __version__
from botscope.normalize.event import NormalizedEvent, ProvenanceLevel
from botscope.statistics.aggregate import ObservatoryStats


def build_report(
    stats: ObservatoryStats,
    *,
    events: Iterable[NormalizedEvent] | None = None,
    is_demo: bool = False,
    flows: list[dict[str, Any]] | None = None,
    behavior: list[dict[str, Any]] | None = None,
    geo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    events_list = list(events or [])
    timestamps = [e.timestamp for e in events_list if e.timestamp]
    period_start = min(timestamps).isoformat() if timestamps else None
    period_end = max(timestamps).isoformat() if timestamps else None
    report: dict[str, Any] = {
        "title": "BotScope Analysis Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "botscope_version": __version__,
        "is_demo": is_demo or stats.is_demo,
        "observation_period": {"start": period_start, "end": period_end},
        "traffic_totals": {
            "events": stats.total_events,
            "bytes": stats.total_bytes,
            "provenance": ProvenanceLevel.OBSERVED.value,
        },
        "shares": {
            "automated": stats.automation_fraction("requests"),
            "human_likely": stats.human_fraction("requests"),
            "unknown": stats.unknown_fraction("requests"),
            "denominator": "requests",
            "provenance": ProvenanceLevel.CLASSIFIED.value,
        },
        "categories": stats.by_category,
        "confidence_histogram": stats.confidence_histogram,
        "top_user_agents": stats.top_user_agents,
        "methodology": {
            "summary": (
                "Classifications are evidence-backed heuristic results from the v2 "
                "rules + identity engines (optional ML fill). Confidence values are "
                "heuristic scores or model probabilities, not population prevalences."
            ),
            "limitations": [
                "Results apply only to the analyzed sensor/source population.",
                "User-Agent alone does not verify bot identity.",
                "UNKNOWN is a valid scientific outcome.",
                "No Internet-wide estimate is computed from a single analysis.",
            ],
        },
        "demo_notice": "DEMO DATA — not real measurements." if (is_demo or stats.is_demo) else None,
    }
    if flows is not None:
        report["flows"] = flows[:200]
    if behavior is not None:
        report["behavior"] = behavior[:200]
    if geo is not None:
        report["geo"] = geo
    return report


def export_json(report: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def export_markdown(report: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    shares = report.get("shares", {})
    lines = [
        f"# {report.get('title', 'BotScope Report')}",
        "",
        f"Generated: {report.get('generated_at')}",
        f"BotScope version: {report.get('botscope_version')}",
        "",
    ]
    if report.get("demo_notice"):
        lines += [f"**{report['demo_notice']}**", ""]
    lines += [
        "## Observation period",
        f"- Start: {report.get('observation_period', {}).get('start')}",
        f"- End: {report.get('observation_period', {}).get('end')}",
        "",
        "## Traffic totals (OBSERVED)",
        f"- Events: {report.get('traffic_totals', {}).get('events')}",
        f"- Bytes: {report.get('traffic_totals', {}).get('bytes')}",
        "",
        "## Shares (CLASSIFIED, % of requests)",
        f"- Automated: {_pct(shares.get('automated'))}",
        f"- Human-likely: {_pct(shares.get('human_likely'))}",
        f"- Unknown: {_pct(shares.get('unknown'))}",
        "",
        "## Categories",
    ]
    for cat, count in sorted((report.get("categories") or {}).items(), key=lambda x: -x[1]):
        lines.append(f"- {cat}: {count}")
    lines += [
        "",
        "## Methodology",
        report.get("methodology", {}).get("summary", ""),
        "",
        "### Limitations",
    ]
    for item in report.get("methodology", {}).get("limitations", []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def export_csv_categories(report: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category", "count", "provenance"])
        for cat, count in (report.get("categories") or {}).items():
            writer.writerow([cat, count, ProvenanceLevel.CLASSIFIED.value])
    return path


def export_html(report: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    notice = (
        f"<p class='demo'><strong>{report['demo_notice']}</strong></p>"
        if report.get("demo_notice")
        else ""
    )
    shares = report.get("shares", {})
    cats = "".join(
        f"<li>{cat}: {count}</li>"
        for cat, count in sorted((report.get("categories") or {}).items(), key=lambda x: -x[1])
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>BotScope Report</title>
  <style>
    body {{ font-family: "IBM Plex Sans", "Segoe UI", sans-serif; margin: 2rem; color: #1b2430;
           background: linear-gradient(180deg, #eef3f7, #f7f4ef); }}
    h1 {{ font-family: "IBM Plex Serif", Georgia, serif; }}
    .demo {{ color: #8a4b08; background: #fff3cd; padding: .75rem; }}
    .prov {{ font-size: .85rem; color: #516072; }}
  </style>
</head>
<body>
  <h1>BotScope Analysis Report</h1>
  {notice}
  <p class="prov">Provenance labels: OBSERVED totals · CLASSIFIED shares</p>
  <p>Generated: {report.get('generated_at')}<br/>Version: {report.get('botscope_version')}</p>
  <h2>Shares (% of requests)</h2>
  <ul>
    <li>Automated: {_pct(shares.get('automated'))}</li>
    <li>Human-likely: {_pct(shares.get('human_likely'))}</li>
    <li>Unknown: {_pct(shares.get('unknown'))}</li>
  </ul>
  <h2>Categories</h2>
  <ul>{cats}</ul>
  <h2>Limitations</h2>
  <ul>
    {''.join(f'<li>{x}</li>' for x in report.get('methodology', {}).get('limitations', []))}
  </ul>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
    return path


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"
