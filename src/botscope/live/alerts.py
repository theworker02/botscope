"""Threshold alert rules over ObservatorySnapshot windows.

Status: IMPLEMENTED — local measurement alerts only (not Intrusion Detection).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from botscope.live.aggregator import ObservatorySnapshot


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Alert:
    rule_id: str
    name: str
    severity: AlertSeverity
    message: str
    triggered_at: str
    metric: str
    value: float | None
    threshold: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "triggered_at": self.triggered_at,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
        }


@dataclass
class AlertRule:
    """Declarative threshold over a snapshot metric.

    ``metric`` is one of: automated_share, human_share, unknown_share,
    events_per_second, total_events.
    """

    id: str
    name: str
    metric: str
    op: str = ">"  # >, >=, <, <=, ==
    threshold: float = 0.8
    window_s: float = 60.0
    severity: AlertSeverity = AlertSeverity.WARNING
    min_events: int = 20
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "metric": self.metric,
            "op": self.op,
            "threshold": self.threshold,
            "window_s": self.window_s,
            "severity": self.severity.value,
            "min_events": self.min_events,
            "enabled": self.enabled,
        }


def _metric_value(snap: ObservatorySnapshot, metric: str) -> float | None:
    mapping = {
        "automated_share": snap.automated_share,
        "human_share": snap.human_share,
        "unknown_share": snap.unknown_share,
        "events_per_second": snap.events_per_second,
        "total_events": float(snap.total_events),
    }
    return mapping.get(metric)


def _compare(value: float, op: str, threshold: float) -> bool:
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return abs(value - threshold) < 1e-9
    raise ValueError(f"Unsupported alert op: {op}")


@dataclass
class AlertEngine:
    """Evaluate rules against a rolling window of snapshots."""

    rules: list[AlertRule] = field(default_factory=list)
    _history: deque[tuple[float, ObservatorySnapshot]] = field(
        default_factory=deque, init=False
    )
    _fired: set[str] = field(default_factory=set, init=False)

    def add_rule(self, rule: AlertRule) -> None:
        self.rules.append(rule)

    def evaluate(
        self,
        snapshot: ObservatorySnapshot,
        *,
        now: float | None = None,
    ) -> list[Alert]:
        import time

        ts = now if now is not None else time.monotonic()
        self._history.append((ts, snapshot))
        # Trim by max window across rules
        max_window = max((r.window_s for r in self.rules), default=60.0)
        while self._history and (ts - self._history[0][0]) > max_window:
            self._history.popleft()

        alerts: list[Alert] = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            # Use latest snapshot in window for threshold metrics
            window = [s for t, s in self._history if (ts - t) <= rule.window_s]
            if not window:
                continue
            latest = window[-1]
            if latest.total_events < rule.min_events:
                continue
            value = _metric_value(latest, rule.metric)
            if value is None:
                continue
            if not _compare(value, rule.op, rule.threshold):
                self._fired.discard(rule.id)
                continue
            # Edge-trigger: fire once until condition clears
            if rule.id in self._fired:
                continue
            self._fired.add(rule.id)
            alerts.append(
                Alert(
                    rule_id=rule.id,
                    name=rule.name,
                    severity=rule.severity,
                    message=(
                        f"{rule.name}: {rule.metric}={value:.4g} "
                        f"{rule.op} {rule.threshold} "
                        f"(n={latest.total_events}, window={rule.window_s:.0f}s)"
                    ),
                    triggered_at=datetime.now(timezone.utc).isoformat(),
                    metric=rule.metric,
                    value=value,
                    threshold=rule.threshold,
                )
            )
        return alerts

    def evaluate_many(
        self, snapshots: Sequence[ObservatorySnapshot]
    ) -> list[Alert]:
        out: list[Alert] = []
        for i, snap in enumerate(snapshots):
            out.extend(self.evaluate(snap, now=float(i)))
        return out


def default_alert_rules() -> list[AlertRule]:
    """Sensible local-measurement defaults (not security IDS signatures)."""
    return [
        AlertRule(
            id="high_automated_share",
            name="High automated share",
            metric="automated_share",
            op=">",
            threshold=0.8,
            window_s=60.0,
            severity=AlertSeverity.WARNING,
            min_events=50,
        ),
        AlertRule(
            id="high_unknown_share",
            name="High unknown share",
            metric="unknown_share",
            op=">",
            threshold=0.5,
            window_s=120.0,
            severity=AlertSeverity.INFO,
            min_events=50,
        ),
        AlertRule(
            id="burst_eps",
            name="Event rate burst",
            metric="events_per_second",
            op=">",
            threshold=500.0,
            window_s=30.0,
            severity=AlertSeverity.CRITICAL,
            min_events=10,
        ),
    ]
