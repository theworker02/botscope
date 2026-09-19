"""Authoritative Observatory page registry — single navigation system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavPage:
    id: str
    label: str
    group: str
    tooltip: str = ""


# Order MUST match QTabWidget tab indices in ObservatoryWindow.
PRIMARY_PAGES: list[NavPage] = [
    NavPage("observatory", "Observatory", "OVERVIEW", "Traffic composition dashboard"),
    NavPage("global", "Global", "OVERVIEW", "Federated public sources"),
    NavPage("events", "Events", "ANALYZE", "Virtualized event browser"),
    NavPage("dataset_health", "Dataset Health", "INTELLIGENCE", "Multi-dimension quality"),
    NavPage("provenance", "Provenance", "INTELLIGENCE", "Where numbers come from"),
    NavPage("bot_library", "Bot Library", "INTELLIGENCE", "Known signatures vs observed"),
    NavPage("compare", "Compare", "ANALYZE", "Session and classifier compare"),
    NavPage("workspace", "Workspace", "TOOLS", "Analysis workspace JSON"),
    NavPage("annotations", "Annotations", "TOOLS", "Researcher notes"),
    NavPage("exports", "Exports", "TOOLS", "Report builder"),
    NavPage("history", "History", "TOOLS", "Recent .bscope sessions"),
    NavPage("live", "Live", "TOOLS", "Authorized live ingest"),
    NavPage("settings", "Settings", "SYSTEM", "Local preferences"),
    NavPage("sources", "Sources", "INTELLIGENCE", "Source Fabric health"),
]

PAGE_BY_ID = {p.id: p for p in PRIMARY_PAGES}
PAGE_BY_LABEL = {p.label: p for p in PRIMARY_PAGES}

# Legacy nav labels from pre–Phase 5
_LABEL_ALIASES = {
    "Health": "dataset_health",
    "Export": "exports",
    "Bot Library": "bot_library",
    "Dataset Health": "dataset_health",
    "Exports": "exports",
}


def page_index(page_id: str) -> int:
    for i, p in enumerate(PRIMARY_PAGES):
        if p.id == page_id:
            return i
    raise KeyError(page_id)


def resolve_page_id(name: str) -> str | None:
    if name in PAGE_BY_ID:
        return name
    if name in _LABEL_ALIASES:
        return _LABEL_ALIASES[name]
    page = PAGE_BY_LABEL.get(name)
    return page.id if page else None
