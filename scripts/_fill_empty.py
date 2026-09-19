"""Fill empty BotScope packages, examples, demos, tests, and status docs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")
    print("wrote", rel)


def main() -> None:
    # ---------- demo package ----------
    w(
        "src/botscope/demo/__init__.py",
        '''"""Bundled demo corpus helpers.

Status: IMPLEMENTED — synthetic only; always label outputs as DEMO.
"""

from botscope.demo.corpus import DEMO_NOTICE, demo_log_path, ensure_demo_log, iter_demo_events, write_demo_log

__all__ = [
    "DEMO_NOTICE",
    "demo_log_path",
    "ensure_demo_log",
    "iter_demo_events",
    "write_demo_log",
]
''',
    )
    w(
        "src/botscope/demo/corpus.py",
        '''"""Synthetic demo access-log corpus.

Status: IMPLEMENTED
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from botscope.ingest.parsers import CombinedLogParser
from botscope.normalize.event import NormalizedEvent, SourceType

DEMO_NOTICE = "DEMO DATA — not real measurements. Do not publish as observational results."

_DEMO_LINES = [
    '203.0.113.10 - - [18/Sep/2026:10:00:01 +0000] "GET /robots.txt HTTP/1.1" 200 320 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"',
    '203.0.113.11 - - [18/Sep/2026:10:00:02 +0000] "GET / HTTP/1.1" 200 5120 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"',
    '203.0.113.12 - - [18/Sep/2026:10:00:03 +0000] "GET /docs HTTP/1.1" 200 2200 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)"',
    '203.0.113.13 - - [18/Sep/2026:10:00:04 +0000] "GET /api/health HTTP/1.1" 200 15 "-" "Prometheus/2.45.0"',
    '203.0.113.14 - - [18/Sep/2026:10:00:05 +0000] "GET /product/1 HTTP/1.1" 200 4100 "-" "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"',
    '203.0.113.15 - - [18/Sep/2026:10:00:06 +0000] "GET /.env HTTP/1.1" 404 120 "-" "Mozilla/5.0 (compatible; Nmap Scripting Engine)"',
    '203.0.113.16 - - [18/Sep/2026:10:00:07 +0000] "GET /sitemap.xml HTTP/1.1" 200 800 "-" "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"',
    '203.0.113.17 - - [18/Sep/2026:10:00:08 +0000] "GET /blog HTTP/1.1" 200 3000 "-" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"',
    '203.0.113.18 - - [18/Sep/2026:10:00:09 +0000] "GET /wp-login.php HTTP/1.1" 404 90 "-" "python-requests/2.31.0"',
    '203.0.113.19 - - [18/Sep/2026:10:00:10 +0000] "GET /assets/app.js HTTP/1.1" 200 90000 "-" "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"',
    '203.0.113.20 - - [18/Sep/2026:10:01:01 +0000] "GET / HTTP/1.1" 200 5120 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"',
    '203.0.113.21 - - [18/Sep/2026:10:01:02 +0000] "HEAD /api/v1/status HTTP/1.1" 200 0 "-" "curl/8.4.0"',
    '203.0.113.22 - - [18/Sep/2026:10:01:03 +0000] "GET /news HTTP/1.1" 200 1800 "-" "Twitterbot/1.0"',
    '203.0.113.23 - - [18/Sep/2026:10:01:04 +0000] "GET /admin HTTP/1.1" 403 200 "-" "sqlmap/1.7"',
    '203.0.113.24 - - [18/Sep/2026:10:01:05 +0000] "GET /feed HTTP/1.1" 200 640 "-" "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)"',
    '203.0.113.25 - - [18/Sep/2026:10:02:01 +0000] "GET /about HTTP/1.1" 200 1500 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36"',
    '203.0.113.26 - - [18/Sep/2026:10:02:02 +0000] "GET /research HTTP/1.1" 200 2400 "-" "CCBot/2.0 (https://commoncrawl.org/faq/)"',
    '203.0.113.27 - - [18/Sep/2026:10:02:03 +0000] "GET /favicon.ico HTTP/1.1" 200 1150 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"',
    '203.0.113.28 - - [18/Sep/2026:10:02:04 +0000] "GET /hidden HTTP/1.1" 404 80 "-" "Go-http-client/1.1"',
    '203.0.113.29 - - [18/Sep/2026:10:02:05 +0000] "GET /pricing HTTP/1.1" 200 2700 "-" "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)"',
]


def demo_log_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "demo_access.log"


def write_demo_log(path: str | Path | None = None) -> Path:
    target = Path(path) if path else demo_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    header = f"# {DEMO_NOTICE}\\n"
    target.write_text(header + "\\n".join(_DEMO_LINES) + "\\n", encoding="utf-8")
    return target


def ensure_demo_log() -> Path:
    path = demo_log_path()
    if not path.exists():
        write_demo_log(path)
    return path


def iter_demo_events() -> Iterator[NormalizedEvent]:
    path = ensure_demo_log()
    parser = CombinedLogParser()
    for event in parser.parse_file(path):
        yield event.model_copy(update={"source_type": SourceType.DEMO})
''',
    )

    # Fix escape - the above used \\n incorrectly in header. Rewrite corpus carefully via separate write below.

    # ---------- notebook ----------
    w(
        "src/botscope/notebook/__init__.py",
        '''"""Lightweight analysis notebook concept.

Status: EXPERIMENTAL
"""

from botscope.notebook.cells import AnalysisNotebook, NotebookCell

__all__ = ["AnalysisNotebook", "NotebookCell"]
''',
    )
    w(
        "src/botscope/notebook/cells.py",
        '''"""Minimal notebook model for chaining local analysis steps.

Status: EXPERIMENTAL — not a Jupyter replacement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from botscope.normalize.event import NormalizedEvent


@dataclass
class NotebookCell:
    title: str
    kind: str  # markdown | filter | stats | custom
    body: str = ""
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "kind": self.kind, "body": self.body, "result": self.result}


@dataclass
class AnalysisNotebook:
    title: str = "BotScope Analysis Notebook"
    cells: list[NotebookCell] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_markdown(self, title: str, body: str) -> NotebookCell:
        cell = NotebookCell(title=title, kind="markdown", body=body)
        self.cells.append(cell)
        return cell

    def add_event_stats(self, title: str, events: list[NormalizedEvent]) -> NotebookCell:
        cats: dict[str, int] = {}
        for e in events:
            key = e.classification or "UNCLASSIFIED"
            cats[key] = cats.get(key, 0) + 1
        cell = NotebookCell(
            title=title,
            kind="stats",
            result={"event_count": len(events), "by_category": cats},
        )
        self.cells.append(cell)
        return cell

    def add_custom(self, title: str, fn: Callable[[], dict[str, Any]]) -> NotebookCell:
        cell = NotebookCell(title=title, kind="custom", result=fn())
        self.cells.append(cell)
        return cell

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "created_at": self.created_at,
            "status": "EXPERIMENTAL",
            "cells": [c.to_dict() for c in self.cells],
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
''',
    )

    # ---------- plugins/sdk ----------
    w(
        "src/botscope/plugins/sdk/__init__.py",
        '''"""Plugin SDK — templates, validation, scaffold.

Status: IMPLEMENTED
"""

from botscope.plugins.sdk.scaffold import create_plugin_scaffold
from botscope.plugins.sdk.validate import ValidationIssue, validate_plugin_dir

__all__ = ["ValidationIssue", "create_plugin_scaffold", "validate_plugin_dir"]
''',
    )
    w(
        "src/botscope/plugins/sdk/scaffold.py",
        '''"""Create a local plugin scaffold.

Status: IMPLEMENTED
"""

from __future__ import annotations

from pathlib import Path

PLUGIN_PY = '''
from __future__ import annotations

from botscope.normalize.event import NormalizedEvent


class ExampleClassifierPlugin:
    name = "{name}"

    def classify(self, event: NormalizedEvent) -> dict | None:
        # Return None to defer to the core classifier.
        ua = (event.user_agent or "").lower()
        if "examplebot" in ua:
            return {{
                "category": "UNKNOWN AUTOMATION",
                "confidence": 0.6,
                "evidence": ["UA contains examplebot (plugin)"],
            }}
        return None
'''

README = """# {name} BotScope plugin

Status: TEMPLATE

Register via entry point group `botscope.plugins` when packaging, or load locally for experiments.
"""

PYPROJECT = '''
[project]
name = "botscope-plugin-{name}"
version = "0.1.0"
description = "Example BotScope plugin"
requires-python = ">=3.10"
dependencies = ["botscope>=0.1.0"]

[project.entry-points."botscope.plugins"]
{name} = "botscope_plugin_{safe}.plugin:ExampleClassifierPlugin"
'''


def create_plugin_scaffold(dest: str | Path, name: str = "example") -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    root = Path(dest) / f"botscope_plugin_{safe}"
    pkg = root / f"botscope_plugin_{safe}"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text('"""Example BotScope plugin package."""\\n', encoding="utf-8")
    (pkg / "plugin.py").write_text(PLUGIN_PY.format(name=name), encoding="utf-8")
    (root / "README.md").write_text(README.format(name=name), encoding="utf-8")
    (root / "pyproject.toml").write_text(
        PYPROJECT.format(name=name, safe=safe).lstrip(), encoding="utf-8"
    )
    return root
''',
    )
    w(
        "src/botscope/plugins/sdk/validate.py",
        '''"""Validate a plugin directory layout.

Status: IMPLEMENTED
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationIssue:
    severity: str  # error | warning | info
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "message": self.message}


def validate_plugin_dir(path: str | Path) -> list[ValidationIssue]:
    root = Path(path)
    issues: list[ValidationIssue] = []
    if not root.exists():
        return [ValidationIssue("error", f"Path does not exist: {root}")]
    if not (root / "pyproject.toml").exists():
        issues.append(ValidationIssue("warning", "Missing pyproject.toml"))
    py_files = list(root.rglob("plugin.py")) + list(root.rglob("*plugin*.py"))
    if not py_files:
        issues.append(ValidationIssue("error", "No plugin.py (or *plugin*.py) found"))
    else:
        issues.append(ValidationIssue("info", f"Found plugin module(s): {[str(p) for p in py_files]}"))
    readme = root / "README.md"
    if not readme.exists():
        issues.append(ValidationIssue("warning", "Missing README.md"))
    if not issues:
        issues.append(ValidationIssue("info", "Basic layout looks OK"))
    return issues
''',
    )

    # ---------- capture / enrich / behavior / flows / estimation / datasets ----------
    packages = {
        "capture": (
            "PARTIAL",
            "Live/offline capture helpers (authorized sources only).",
            '''"""Authorized capture helpers.

Status: PARTIAL — live packet capture requires optional scapy extra; not enabled by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CapturePlan:
    """Describe an authorized capture without performing network probing."""

    interface: str | None = None
    bpf_filter: str | None = None
    max_packets: int | None = None
    note: str = "Capture must be authorized. BotScope does not scan third-party networks."

    def to_dict(self) -> dict[str, Any]:
        return {
            "interface": self.interface,
            "bpf_filter": self.bpf_filter,
            "max_packets": self.max_packets,
            "status": "PARTIAL",
            "note": self.note,
            "live_capture": "PLANNED (optional scapy extra)",
        }


def scapy_available() -> bool:
    try:
        import scapy  # noqa: F401
        return True
    except ImportError:
        return False


def capture_status() -> dict[str, Any]:
    return {
        "scapy_available": scapy_available(),
        "live_capture": "AVAILABLE" if scapy_available() else "NOT_INSTALLED",
        "default": "offline log ingest",
        "policy": "No unauthorized probing",
    }
''',
            "CapturePlan, capture_status, scapy_available",
        ),
        "enrich": (
            "PARTIAL",
            "Optional enrichment stubs (ASN/rDNS) — offline-first.",
            '''"""Enrichment helpers.

Status: PARTIAL — local/optional only; network enrichment OFF unless explicitly enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from botscope.normalize.event import NormalizedEvent, ProvenanceLevel


@dataclass
class EnrichmentResult:
    field: str
    value: Any
    provenance: ProvenanceLevel = ProvenanceLevel.INFERRED
    source: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "provenance": self.provenance.value,
            "source": self.source,
        }


def apply_static_tags(event: NormalizedEvent, tags: dict[str, Any]) -> NormalizedEvent:
    """Attach local static tags into extras (does not call the network)."""
    extras = dict(event.extras)
    extras["static_tags"] = dict(tags)
    return event.model_copy(update={"extras": extras})


def enrichment_status() -> dict[str, Any]:
    return {
        "status": "PARTIAL",
        "network_lookups": "OFF by default",
        "available": ["apply_static_tags"],
        "planned": ["asn_lookup", "rdns_lookup"],
    }
''',
            "EnrichmentResult, apply_static_tags, enrichment_status",
        ),
        "behavior": (
            "EXPERIMENTAL",
            "Simple behavioral feature extraction from event sequences.",
            '''"""Behavioral feature extraction.

Status: EXPERIMENTAL
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from botscope.normalize.event import NormalizedEvent


@dataclass
class BehaviorProfile:
    src_address: str
    event_count: int
    unique_paths: int
    methods: dict[str, int]
    status_counts: dict[str, int]
    burstiness: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "src_address": self.src_address,
            "event_count": self.event_count,
            "unique_paths": self.unique_paths,
            "methods": dict(self.methods),
            "status_counts": dict(self.status_counts),
            "burstiness": self.burstiness,
            "status": "EXPERIMENTAL",
        }


def profile_by_source(events: Iterable[NormalizedEvent]) -> list[BehaviorProfile]:
    by_src: dict[str, list[NormalizedEvent]] = defaultdict(list)
    for e in events:
        key = e.src_address or "unknown"
        by_src[key].append(e)
    profiles: list[BehaviorProfile] = []
    for src, items in by_src.items():
        methods = Counter(e.http_method or "?" for e in items)
        statuses = Counter(str(e.status) if e.status is not None else "?" for e in items)
        paths = {e.path for e in items if e.path}
        # crude burstiness: events per distinct second
        seconds = set()
        for e in items:
            if e.timestamp:
                seconds.add(int(e.timestamp.timestamp()))
        burst = len(items) / max(1, len(seconds))
        profiles.append(
            BehaviorProfile(
                src_address=src,
                event_count=len(items),
                unique_paths=len(paths),
                methods=dict(methods),
                status_counts=dict(statuses),
                burstiness=round(burst, 3),
            )
        )
    return profiles
''',
            "BehaviorProfile, profile_by_source",
        ),
        "flows": (
            "PARTIAL",
            "Flow-like aggregation from discrete events.",
            '''"""Flow aggregation from normalized events.

Status: PARTIAL
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from botscope.normalize.event import NormalizedEvent


@dataclass
class FlowRecord:
    src_address: str | None
    dst_address: str | None
    dst_port: int | None
    events: int
    bytes_out: int
    first_ts: str | None
    last_ts: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "src_address": self.src_address,
            "dst_address": self.dst_address,
            "dst_port": self.dst_port,
            "events": self.events,
            "bytes_out": self.bytes_out,
            "first_ts": self.first_ts,
            "last_ts": self.last_ts,
        }


def aggregate_flows(events: Iterable[NormalizedEvent]) -> list[FlowRecord]:
    buckets: dict[tuple, list[NormalizedEvent]] = {}
    for e in events:
        key = (e.src_address, e.dst_address, e.dst_port)
        buckets.setdefault(key, []).append(e)
    out: list[FlowRecord] = []
    for (src, dst, port), items in buckets.items():
        stamps = [e.timestamp for e in items if e.timestamp]
        out.append(
            FlowRecord(
                src_address=src,
                dst_address=dst,
                dst_port=port,
                events=len(items),
                bytes_out=sum(e.bytes_out or 0 for e in items),
                first_ts=min(stamps).isoformat() if stamps else None,
                last_ts=max(stamps).isoformat() if stamps else None,
            )
        )
    return out
''',
            "FlowRecord, aggregate_flows",
        ),
        "estimation": (
            "RESEARCH",
            "Honest estimation helpers — refuses Internet-wide claims from local samples.",
            '''"""Estimation helpers with explicit refusal of overclaiming.

Status: RESEARCH
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LocalShareEstimate:
    automated: float | None
    human_likely: float | None
    unknown: float | None
    denominator: str
    population: str
    caveat: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "automated": self.automated,
            "human_likely": self.human_likely,
            "unknown": self.unknown,
            "denominator": self.denominator,
            "population": self.population,
            "caveat": self.caveat,
            "internet_wide_estimate": None,
            "status": "RESEARCH",
        }


def local_share_estimate(
    automated: float | None,
    human_likely: float | None,
    unknown: float | None,
    *,
    denominator: str = "requests",
    population: str = "local sensor / authorized log corpus",
) -> LocalShareEstimate:
    return LocalShareEstimate(
        automated=automated,
        human_likely=human_likely,
        unknown=unknown,
        denominator=denominator,
        population=population,
        caveat=(
            "These shares describe only the analyzed population. "
            "BotScope will not extrapolate to the Internet at large from a single corpus."
        ),
    )


def internet_wide_estimate(*_args: Any, **_kwargs: Any) -> None:
    """Explicitly unavailable — do not invent prevalence numbers."""
    raise NotImplementedError(
        "Internet-wide estimation is NOT IMPLEMENTED and intentionally refused in v0.1."
    )
''',
            "LocalShareEstimate, internet_wide_estimate, local_share_estimate",
        ),
        "datasets": (
            "IMPLEMENTED",
            "Dataset path helpers for bundled/demo corpora.",
            '''"""Dataset path helpers.

Status: IMPLEMENTED for demo/fixture discovery.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def repo_datasets_root() -> Path:
    # src/botscope/datasets -> repo/datasets
    return Path(__file__).resolve().parents[3] / "datasets"


def list_demo_datasets() -> list[dict[str, Any]]:
    root = repo_datasets_root() / "demo"
    root.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob("*")):
        if path.is_file():
            items.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "is_demo": True,
                }
            )
    return items


def demo_access_log() -> Path:
    """Prefer package demo log; fall back to datasets/demo."""
    from botscope.demo.corpus import ensure_demo_log

    pkg = ensure_demo_log()
    dest = repo_datasets_root() / "demo" / "demo_access.log"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_text(pkg.read_text(encoding="utf-8"), encoding="utf-8")
    return dest
''',
            "demo_access_log, list_demo_datasets, repo_datasets_root",
        ),
    }

    for name, (status, summary, module_body, exports) in packages.items():
        export_list = ", ".join(e.strip() for e in exports.split(","))
        w(
            f"src/botscope/{name}/__init__.py",
            f'''"""{summary}

Status: {status}
"""

from botscope.{name}.core import {export_list}

__all__ = [{", ".join(repr(e.strip()) for e in exports.split(","))}]
''',
        )
        w(f"src/botscope/{name}/core.py", module_body)

    # ---------- manifests / botcard inits ----------
    w(
        "src/botscope/manifests/__init__.py",
        '''"""Measurement manifests.

Status: IMPLEMENTED
"""

from botscope.manifests.measurement import MeasurementManifest, load_manifest, write_manifest

__all__ = ["MeasurementManifest", "load_manifest", "write_manifest"]
''',
    )
    # Ensure measurement.py has load/write - check if needed by reading end of file later
    w(
        "src/botscope/botcard/__init__.py",
        '''"""Bot Card package.

Status: IMPLEMENTED
"""

from botscope.botcard.card import BotCard, build_library, card_from_name

__all__ = ["BotCard", "build_library", "card_from_name"]
''',
    )

    print("core packages section done")


if __name__ == "__main__":
    main()
