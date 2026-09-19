"""Progressive traffic breakdown helpers (Phase 6)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from botscope.classify.taxonomy import AUTOMATION_CATEGORIES
from botscope.normalize.event import NormalizedEvent
from botscope.signatures.store import SignatureStore

SUPPORTED_DIMENSIONS = (
    "classification",
    "bot_family",
    "host",
    "path_prefix",
    "status",
    "identity",
)


@dataclass(frozen=True)
class BreakdownRow:
    key: str
    count: int
    share: float
    bytes_out: int = 0


def available_dimensions(events: Iterable[NormalizedEvent]) -> list[str]:
    events = list(events)
    if not events:
        return []
    dims: list[str] = ["classification"]
    if any(e.user_agent for e in events):
        dims.append("bot_family")
        dims.append("identity")
    if any(e.host for e in events if hasattr(e, "host") and e.host):
        dims.append("host")
    if any(getattr(e, "path", None) for e in events):
        dims.append("path_prefix")
    if any(getattr(e, "status", None) is not None for e in events):
        dims.append("status")
    return dims


def _dim_key(event: NormalizedEvent, dimension: str, store: SignatureStore) -> str:
    if dimension == "classification":
        return event.classification or "UNKNOWN"
    if dimension == "bot_family":
        sig = store.match_user_agent(event.user_agent or "")
        return (sig.category if sig else None) or event.classification or "unattributed"
    if dimension == "identity":
        sig = store.match_user_agent(event.user_agent or "")
        if sig:
            return sig.name
        attr = (event.extras or {}).get("attribution")
        return str(attr) if attr else "Unattributed"
    if dimension == "host":
        return getattr(event, "host", None) or "(no host)"
    if dimension == "path_prefix":
        path = event.path or "/"
        parts = path.strip("/").split("/")
        return "/" + (parts[0] if parts and parts[0] else "")
    if dimension == "status":
        return str(event.status) if event.status is not None else "(none)"
    return "(unknown)"


def breakdown(
    events: Iterable[NormalizedEvent],
    *,
    dimension: str,
    family: str | None = None,
    limit: int = 25,
) -> list[BreakdownRow]:
    """Group events by dimension; optional family pre-filter (automated/human/unknown)."""
    store = SignatureStore.load_bundled()
    auto = {c.value for c in AUTOMATION_CATEGORIES}
    rows_events: list[NormalizedEvent] = []
    for e in events:
        cat = e.classification or ""
        if family == "automated" and cat not in auto:
            continue
        if family == "human_likely" and cat != "HUMAN-LIKELY":
            continue
        if family == "unknown" and cat != "UNKNOWN":
            continue
        rows_events.append(e)

    if not rows_events:
        return []
    counts: Counter[str] = Counter()
    bytes_c: Counter[str] = Counter()
    for e in rows_events:
        key = _dim_key(e, dimension, store)
        counts[key] += 1
        bytes_c[key] += int(e.bytes_out or 0)
    total = sum(counts.values()) or 1
    out: list[BreakdownRow] = []
    for key, n in counts.most_common(limit):
        out.append(BreakdownRow(key=key, count=n, share=n / total, bytes_out=bytes_c[key]))
    return out
