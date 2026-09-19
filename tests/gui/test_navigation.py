"""Phase 5 navigation registry tests."""

from __future__ import annotations

from botscope.gui.navigation import (
    PAGE_BY_ID,
    PRIMARY_PAGES,
    page_index,
    resolve_page_id,
)


def test_primary_pages_unique_ids() -> None:
    ids = [p.id for p in PRIMARY_PAGES]
    assert len(ids) == len(set(ids))
    assert "observatory" in ids
    assert "sources" in ids
    assert "settings" in ids


def test_page_index_and_resolve() -> None:
    assert page_index("observatory") == 0
    assert resolve_page_id("Health") == "dataset_health"
    assert resolve_page_id("Export") == "exports"
    assert resolve_page_id("observatory") == "observatory"
    assert resolve_page_id("nope") is None
    assert PAGE_BY_ID["sources"].label == "Sources"


def test_tab_order_matches_groups() -> None:
    # Ensure Compare sits under ANALYZE after Bot Library in registry order
    labels = [p.label for p in PRIMARY_PAGES]
    assert labels.index("Events") < labels.index("Compare")
    assert labels.index("Observatory") == 0
