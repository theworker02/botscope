"""Minimal notebook model for chaining local analysis steps.

Status: EXPERIMENTAL — not a Jupyter replacement.
"""

from __future__ import annotationsimport jsonfrom collections.abc import Callablefrom dataclasses import dataclass, fieldfrom datetime import datetime, timezonefrom pathlib import Pathfrom typing import Anyfrom botscope.normalize.event import NormalizedEventfrom botscope.query import filter_events, parse_simple_query@dataclass
class NotebookCell:
    title: str
    kind: str  # markdown | filter | stats | custom
    body: str = ""
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "kind": self.kind,
            "body": self.body,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NotebookCell:
        return cls(
            title=str(data.get("title") or ""),
            kind=str(data.get("kind") or "markdown"),
            body=str(data.get("body") or ""),
            result=dict(data.get("result") or {}),
        )


@dataclass
class AnalysisNotebook:
    title: str = "BotScope Analysis Notebook"
    cells: list[NotebookCell] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

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

    def add_filter(
        self,
        title: str,
        events: list[NormalizedEvent],
        expression: str,
    ) -> NotebookCell:
        """Filter events with the shared query language and store counts."""
        preds = parse_simple_query(expression)
        matched = list(filter_events(events, preds))
        cats: dict[str, int] = {}
        for e in matched:
            key = e.classification or "UNCLASSIFIED"
            cats[key] = cats.get(key, 0) + 1
        cell = NotebookCell(
            title=title,
            kind="filter",
            body=expression,
            result={
                "expression": expression,
                "matched": len(matched),
                "total": len(events),
                "by_category": cats,
            },
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

    @classmethod
    def load(cls, path: str | Path) -> AnalysisNotebook:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        nb = cls(
            title=str(data.get("title") or "BotScope Analysis Notebook"),
            created_at=str(data.get("created_at") or datetime.now(timezone.utc).isoformat()),
        )
        nb.cells = [NotebookCell.from_dict(c) for c in data.get("cells") or []]
        return nb
