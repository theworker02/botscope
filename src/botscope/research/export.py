"""Research export bundles and citation helpers.

Status: IMPLEMENTED
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from botscope.__version__ import __version__
from botscope.normalize.event import NormalizedEvent
from botscope.provenance.engine import claim_safe_totals, summarize_corpus
from botscope.quality.scorecard import build_scorecard

CITATION_TEXT = """\
BotScope Contributors. ({year}). BotScope (Version {version}) [Computer software].
https://github.com/theworker02/botscope
"""

CITATION_BIBTEX = """\
@software{{botscope{year},
  title        = {{BotScope}},
  author       = {{BotScope Contributors}},
  year         = {{{year}}},
  version      = {{{version}}},
  url          = {{https://github.com/theworker02/botscope}},
  note         = {{Python-first observability for automated Internet traffic}}
}}
"""


def citation_plain(*, version: str | None = None, year: int | None = None) -> str:
    year = year or datetime.now(timezone.utc).year
    version = version or __version__
    return CITATION_TEXT.format(year=year, version=version).strip()


def citation_bibtex(*, version: str | None = None, year: int | None = None) -> str:
    year = year or datetime.now(timezone.utc).year
    version = version or __version__
    return CITATION_BIBTEX.format(year=year, version=version).strip()


def citation_cff_snippet() -> str:
    """Return a short CFF-oriented citation reminder (no invented DOI)."""
    return (
        f"title: BotScope\n"
        f"version: {__version__}\n"
        f"url: https://github.com/theworker02/botscope\n"
        f"license: SEE LICENSE\n"
        f"# DOI: not assigned — do not invent one\n"
    )


@dataclass
class ResearchBundleManifest:
    created_at: str
    botscope_version: str
    event_count: int
    is_demo: bool
    files: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "botscope_version": self.botscope_version,
            "event_count": self.event_count,
            "is_demo": self.is_demo,
            "files": list(self.files),
            "limitations": list(self.limitations),
        }


DEFAULT_LIMITATIONS = [
    "Results apply only to the analyzed sensor/source population.",
    "Classifications are heuristic and evidence-backed, not ground truth.",
    "Confidence values are not calibrated probabilities.",
    "UNKNOWN is a valid scientific outcome.",
    "No Internet-wide estimate is implied by a local analysis.",
]


def build_research_bundle(
    events: Iterable[NormalizedEvent],
    output: str | Path,
    *,
    report: dict[str, Any] | None = None,
    is_demo: bool = False,
    extra_meta: dict[str, Any] | None = None,
) -> Path:
    """Write a zip research bundle with events, provenance, quality, and citation."""
    events_list = list(events)
    output = Path(output)
    if output.suffix.lower() != ".zip":
        output = output.with_suffix(".zip")
    output.parent.mkdir(parents=True, exist_ok=True)

    provenance = summarize_corpus(events_list).to_dict()
    quality = build_scorecard(events_list).to_dict()
    claims = claim_safe_totals(events_list)
    citation = {
        "plain": citation_plain(),
        "bibtex": citation_bibtex(),
        "cff_snippet": citation_cff_snippet(),
    }
    methodology = {
        "summary": (
            "BotScope v2 uses rules + identity heuristics with inspectable evidence "
            "(optional ML fill via feature_logistic_v1). "
            "Measurement provenance distinguishes OBSERVED counts from CLASSIFIED shares."
        ),
        "limitations": list(DEFAULT_LIMITATIONS),
        "is_demo": is_demo,
    }
    if extra_meta:
        methodology["extra"] = extra_meta

    files_written = [
        "events.jsonl",
        "provenance.json",
        "quality_scorecard.json",
        "claim_safe_totals.json",
        "citation.json",
        "methodology.json",
        "manifest.json",
    ]
    if report is not None:
        files_written.append("report.json")

    manifest = ResearchBundleManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        botscope_version=__version__,
        event_count=len(events_list),
        is_demo=is_demo,
        files=files_written,
        limitations=list(DEFAULT_LIMITATIONS),
    )

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        lines = "\n".join(e.model_dump_json() for e in events_list) + ("\n" if events_list else "")
        zf.writestr("events.jsonl", lines)
        zf.writestr("provenance.json", json.dumps(provenance, indent=2))
        zf.writestr("quality_scorecard.json", json.dumps(quality, indent=2))
        zf.writestr("claim_safe_totals.json", json.dumps(claims, indent=2))
        zf.writestr("citation.json", json.dumps(citation, indent=2))
        zf.writestr("methodology.json", json.dumps(methodology, indent=2))
        zf.writestr("manifest.json", json.dumps(manifest.to_dict(), indent=2))
        if report is not None:
            zf.writestr("report.json", json.dumps(report, indent=2))

    return output
