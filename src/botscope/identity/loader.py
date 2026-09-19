"""Load published crawler CIDR ranges for identity corroboration during analyze.

Cache-first via HttpSourceCache. Never invents prefixes. Fetch failures degrade
to an empty index so offline analysis still completes.
"""

from __future__ import annotations

import os
from typing import Any

from botscope.identity.ranges import PublishedRangeIndex
from botscope.sources.bot_identity import BingbotRangesSource, GoogleCrawlerRangesSource
from botscope.sources.bot_identity.cidr_util import parse_prefix_list
from botscope.sources.cache import HttpSourceCache


def index_from_prefix_documents(
    *,
    google_common: dict[str, Any] | None = None,
    google_special: dict[str, Any] | None = None,
    bing: dict[str, Any] | None = None,
) -> PublishedRangeIndex:
    """Build an index from already-parsed prefix JSON documents (tests / offline)."""
    index = PublishedRangeIndex()
    for doc in (google_common, google_special):
        if doc:
            index.add("google", parse_prefix_list(doc))
    if bing:
        index.add("microsoft", parse_prefix_list(bing))
        index.add("bing", parse_prefix_list(bing))
    return index


def load_published_range_index(
    *,
    cache: HttpSourceCache | None = None,
    enabled: bool = True,
) -> tuple[PublishedRangeIndex, dict[str, Any]]:
    """Fetch (or reuse cache for) Google + Bing crawler prefixes.

    Returns ``(index, status)`` where status is suitable for doctor / UI notes.
    Honors ``BOTSCOPE_NO_IDENTITY_RANGES=1`` when ``enabled`` is left True.
    """
    if enabled:
        flag = os.environ.get("BOTSCOPE_NO_IDENTITY_RANGES", "").strip().lower()
        if flag in {"1", "true", "yes", "on"}:
            enabled = False

    status: dict[str, Any] = {
        "enabled": enabled,
        "prefix_count": 0,
        "operators": [],
        "errors": {},
        "sources": {},
    }
    index = PublishedRangeIndex()
    if not enabled:
        status["detail"] = "Identity published ranges disabled"
        return index, status

    cache = cache or HttpSourceCache(min_refresh_seconds=3600.0)

    # Google common + special
    try:
        google = GoogleCrawlerRangesSource(cache=cache)
        raw = google.fetch()  # which=both by default
        common = raw.get("common", {}).get("payload") if isinstance(raw.get("common"), dict) else None
        special = raw.get("special", {}).get("payload") if isinstance(raw.get("special"), dict) else None
        if common:
            nets = parse_prefix_list(common)
            index.add("google", nets)
            status["sources"]["google_common"] = len(nets)
        if special:
            nets = parse_prefix_list(special)
            index.add("google", nets)
            status["sources"]["google_special"] = len(nets)
        if raw.get("special_error"):
            status["errors"]["google_special"] = str(raw["special_error"])
    except Exception as exc:  # noqa: BLE001
        status["errors"]["google"] = str(exc)

    # Bingbot
    try:
        bing = BingbotRangesSource(cache=cache)
        raw = bing.fetch()
        payload = raw.get("payload") if isinstance(raw, dict) else None
        if payload:
            nets = parse_prefix_list(payload)
            index.add("microsoft", nets)
            index.add("bing", nets)
            status["sources"]["bing"] = len(nets)
    except Exception as exc:  # noqa: BLE001
        status["errors"]["bing"] = str(exc)

    status["prefix_count"] = len(index)
    status["operators"] = sorted(index.networks_by_operator.keys())
    if status["prefix_count"] == 0:
        status["detail"] = "No published crawler prefixes loaded (offline or unavailable)"
    else:
        status["detail"] = (
            f"Loaded {status['prefix_count']} published prefixes "
            f"for {', '.join(status['operators'])}"
        )
    return index, status
