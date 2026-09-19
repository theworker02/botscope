"""Dataset path helpers.

Status: IMPLEMENTED for demo/fixture discovery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def repo_datasets_root() -> Path:
    # src/botscope/datasets -> repo root / datasets
    return Path(__file__).resolve().parents[3] / "datasets"


def fixtures_root() -> Path:
    return repo_datasets_root() / "fixtures"


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
    """Prefer package demo log; also mirror under datasets/demo."""
    from botscope.demo.corpus import ensure_demo_log

    pkg = ensure_demo_log()
    dest = repo_datasets_root() / "demo" / "demo_access.log"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.read_text(encoding="utf-8") != pkg.read_text(
        encoding="utf-8"
    ):
        dest.write_text(pkg.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def load_labeled_mini() -> list[dict[str, Any]]:
    """Load hand-labeled mini fixture rows (for eval / calibration)."""
    path = fixtures_root() / "labeled_mini.jsonl"
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def labeled_mini_eval():
    """Run the real classifier against labeled mini fixture rows."""
    from datetime import datetime, timezone

    from botscope.classify.engine import Classifier
    from botscope.eval import evaluate_labels
    from botscope.normalize.event import NormalizedEvent, ProvenanceLevel, SourceType

    rows = load_labeled_mini()
    classifier = Classifier()
    y_true: list[str] = []
    y_pred: list[str] = []
    for row in rows:
        ts = row.get("timestamp") or datetime.now(timezone.utc).isoformat()
        event = NormalizedEvent(
            event_id=str(row.get("event_id") or "fx"),
            timestamp=datetime.fromisoformat(str(ts).replace("Z", "+00:00")),
            source_type=SourceType.WEB_LOG,
            provenance=ProvenanceLevel.OBSERVED,
            user_agent=row.get("user_agent"),
            path=row.get("path"),
            status=row.get("status"),
        )
        result = classifier.classify(event)
        y_true.append(str(row["label"]))
        y_pred.append(result.category.value)
    return evaluate_labels(y_true, y_pred)
