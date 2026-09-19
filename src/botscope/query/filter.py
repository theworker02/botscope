"""Safe event filtering — no arbitrary code execution.

Status: IMPLEMENTED

Supports a small declarative predicate language only.
"""

from __future__ import annotations

import operator
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator

from botscope.normalize.event import NormalizedEvent


OPS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "contains": lambda a, b: b in a if a is not None else False,
    "icontains": lambda a, b: (str(b).lower() in str(a).lower()) if a is not None else False,
    "in": lambda a, b: a in b,
    "regex": lambda a, b: bool(re.search(str(b), str(a or ""))),
    "exists": lambda a, b: (a is not None and a != "" and a != []) if b else (a is None or a == "" or a == []),
}

ALLOWED_FIELDS = frozenset(
    {
        "event_id",
        "sensor_id",
        "source_type",
        "protocol",
        "src_address",
        "dst_address",
        "src_port",
        "dst_port",
        "transport",
        "http_method",
        "host",
        "path",
        "status",
        "user_agent",
        "bytes_in",
        "bytes_out",
        "asn",
        "network_owner",
        "classification",
        "confidence",
        "provenance",
    }
)


@dataclass(frozen=True)
class Predicate:
    field: str
    op: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "op": self.op, "value": self.value}


class QueryError(ValueError):
    """Raised for invalid or unsafe query definitions."""


def _get_field(event: NormalizedEvent, name: str) -> Any:
    if name not in ALLOWED_FIELDS:
        raise QueryError(f"Field not allowed: {name}")
    value = getattr(event, name, None)
    if hasattr(value, "value"):
        return value.value
    return value


def match_event(event: NormalizedEvent, predicates: Iterable[Predicate]) -> bool:
    for pred in predicates:
        if pred.op not in OPS:
            raise QueryError(f"Operator not allowed: {pred.op}")
        left = _get_field(event, pred.field)
        if not OPS[pred.op](left, pred.value):
            return False
    return True


def filter_events(
    events: Iterable[NormalizedEvent],
    predicates: Iterable[Predicate],
) -> Iterator[NormalizedEvent]:
    preds = list(predicates)
    for event in events:
        if match_event(event, preds):
            yield event


def parse_simple_query(expr: str) -> list[Predicate]:
    """Parse ``field op value`` clauses joined by ``AND`` (case-insensitive).

    Examples:
      classification eq "AI CRAWLER"
      confidence gte 0.8 AND user_agent icontains bot
    """
    if not expr or not expr.strip():
        return []
    # Refuse anything that looks like code execution.
    banned = ("__", "import", "eval", "exec", "open(", "os.", "sys.", ";", "`")
    lowered = expr.lower()
    for token in banned:
        if token in lowered:
            raise QueryError(f"Disallowed token in query: {token}")

    parts = re.split(r"\s+AND\s+", expr.strip(), flags=re.IGNORECASE)
    predicates: list[Predicate] = []
    clause_re = re.compile(
        r'^(?P<field>[a-zA-Z_][a-zA-Z0-9_]*)\s+(?P<op>[a-zA-Z_]+)\s+(?P<value>.+)$'
    )
    for part in parts:
        m = clause_re.match(part.strip())
        if not m:
            raise QueryError(f"Cannot parse clause: {part!r}")
        field = m.group("field")
        op = m.group("op").lower()
        raw = m.group("value").strip()
        if field not in ALLOWED_FIELDS:
            raise QueryError(f"Field not allowed: {field}")
        if op not in OPS:
            raise QueryError(f"Operator not allowed: {op}")
        value: Any
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            value = raw[1:-1]
        elif raw.lower() in {"true", "false"}:
            value = raw.lower() == "true"
        elif raw.lower() == "null":
            value = None
        else:
            try:
                if "." in raw:
                    value = float(raw)
                else:
                    value = int(raw)
            except ValueError:
                value = raw
        predicates.append(Predicate(field=field, op=op, value=value))
    return predicates
