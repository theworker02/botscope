"""In-memory analysis session held by the Observatory GUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from botscope.api.analyzer import AnalysisResult
from botscope.classify.taxonomy import AUTOMATION_CATEGORIES, BotCategory
from botscope.normalize.event import NormalizedEvent
from botscope.query import Predicate, QueryError, filter_events, parse_simple_query
from botscope.statistics.aggregate import ObservatoryStats
from botscope.workspace import AnalysisWorkspace, ChartOverlay, ColumnPref, TimeRange

# KPI / ring click-through family keys → classification sets
_FAMILY_FILTERS: dict[str, frozenset[str]] = {
    "automated": frozenset(c.value for c in AUTOMATION_CATEGORIES),
    "human_likely": frozenset({BotCategory.HUMAN_LIKELY.value}),
    "unknown": frozenset({BotCategory.UNKNOWN.value}),
}


@dataclass
class GuiSession:
    """Active Observatory workspace state (desktop process memory)."""

    source_path: Path | None = None
    session_path: Path | None = None
    session_id: str | None = None
    result: AnalysisResult | None = None
    is_demo: bool = False
    denominator: str = "requests"
    filter_category: str | None = None
    filter_text: str = ""
    query: str = ""
    selected_event_id: str | None = None
    notes: list[str] = field(default_factory=list)
    chart_overlays: list[ChartOverlay] = field(default_factory=list)
    columns: list[ColumnPref] = field(default_factory=list)
    time_range: TimeRange = field(default_factory=TimeRange)
    live_mode: bool = False

    @property
    def events(self) -> list[NormalizedEvent]:
        if self.result is None:
            return []
        return self.result.events

    @property
    def stats(self) -> ObservatoryStats | None:
        if self.result is None:
            return None
        return self.result.stats

    @property
    def loaded(self) -> bool:
        return self.result is not None

    def query_predicates(self) -> list[Predicate]:
        """Parse the structured query language (raises QueryError on bad input)."""
        return parse_simple_query(self.query)

    def filtered_events(self) -> list[NormalizedEvent]:
        """Apply category + query engine + convenience text search.

        Structured ``query`` uses ``botscope.query`` (field op value AND …).
        Plain ``filter_text`` maps to an OR of icontains-style convenience matches
        across path / UA / IP / category when it does not look like a structured query.
        """
        events: list[NormalizedEvent] = list(self.events)
        if self.filter_category:
            family = _FAMILY_FILTERS.get(self.filter_category)
            if family is not None:
                events = [e for e in events if (e.classification or "") in family]
            else:
                events = [e for e in events if e.classification == self.filter_category]

        q = self.query.strip()
        if q:
            try:
                preds = parse_simple_query(q)
            except QueryError:
                # Leave events unfiltered by query; GUI surfaces the error separately.
                preds = []
            if preds:
                events = list(filter_events(events, preds))

        needle = self.filter_text.strip().lower()
        if needle:
            # Convenience search — equivalent to multi-field icontains OR.
            events = [
                e
                for e in events
                if needle in (e.user_agent or "").lower()
                or needle in (e.path or "").lower()
                or needle in (e.src_address or "").lower()
                or needle in (e.classification or "").lower()
            ]

        tr = self.time_range
        if tr.start or tr.end:
            filtered: list[NormalizedEvent] = []
            for e in events:
                if not e.timestamp:
                    continue
                iso = e.timestamp.isoformat()
                if tr.start and iso < tr.start:
                    continue
                if tr.end and iso > tr.end:
                    continue
                filtered.append(e)
            events = filtered
        return events

    def selected_event(self) -> NormalizedEvent | None:
        if not self.selected_event_id:
            return None
        for event in self.events:
            if event.event_id == self.selected_event_id:
                return event
        return None

    def share_payload(self) -> dict[str, Any]:
        stats = self.stats
        if stats is None:
            return {}
        den = self.denominator if self.denominator in {"requests", "bytes"} else "requests"
        return {
            "automated": stats.automation_fraction(den),  # type: ignore[arg-type]
            "human_likely": stats.human_fraction(den),  # type: ignore[arg-type]
            "unknown": stats.unknown_fraction(den),  # type: ignore[arg-type]
            "denominator": den,
            "provenance": "CLASSIFIED",
            "is_demo": self.is_demo or stats.is_demo,
        }

    def to_workspace(self) -> AnalysisWorkspace:
        return AnalysisWorkspace(
            denominator=self.denominator,
            query=self.query,
            filter_category=self.filter_category,
            filter_text=self.filter_text,
            selected_event_id=self.selected_event_id,
            time_range=self.time_range,
            chart_overlays=list(self.chart_overlays),
            columns=list(self.columns),
            notes=list(self.notes),
        )

    def apply_workspace(self, workspace: AnalysisWorkspace) -> None:
        self.denominator = workspace.denominator or "requests"
        self.query = workspace.query or ""
        self.filter_category = workspace.filter_category
        self.filter_text = workspace.filter_text or ""
        self.selected_event_id = workspace.selected_event_id
        self.time_range = workspace.time_range
        self.chart_overlays = list(workspace.chart_overlays)
        self.columns = list(workspace.columns)
        self.notes = list(workspace.notes)
