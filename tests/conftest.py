"""Pytest defaults — keep unit tests offline-fast."""

from __future__ import annotations

import os

import pytest

# Analyzer loads Google/Bing ranges by default; skip network in the unit suite.
# Tests that need ranges inject PublishedRangeIndex explicitly.
os.environ.setdefault("BOTSCOPE_NO_IDENTITY_RANGES", "1")


@pytest.fixture(autouse=True)
def _clear_botscope_tamper_state():
    """Isolate in-process vault fingerprints across UX security tests."""
    try:
        from botscope.ux.tamper import clear_trusted_vault
    except Exception:
        yield
        return
    clear_trusted_vault()
    yield
    clear_trusted_vault()
