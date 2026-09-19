"""Source health probing — never fake ONLINE."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from botscope.sources.base import AvailabilityReport, DataSource, SourceStatus


@dataclass
class SourceHealthBoard:
    checked_at: str
    reports: list[AvailabilityReport] = field(default_factory=list)
    mode: str = "ZERO-AUTH"
    zero_auth_available: int = 0
    zero_auth_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "checked_at": self.checked_at,
            "mode": self.mode,
            "zero_auth_available": self.zero_auth_available,
            "zero_auth_total": self.zero_auth_total,
            "reports": [r.to_dict() for r in self.reports],
        }

    def format_text(self) -> str:
        lines = [
            "REAL DATA SOURCES",
            f"Checked: {self.checked_at}",
            f"Mode: {self.mode}",
            f"Zero-auth available: {self.zero_auth_available}/{self.zero_auth_total}",
            "",
        ]
        for r in self.reports:
            mark = "●" if r.status in {
                SourceStatus.ACTIVE,
                SourceStatus.AVAILABLE,
                SourceStatus.CACHED,
                SourceStatus.OFFLINE_CACHED,
                SourceStatus.DEGRADED,
            } else "○"
            lines.append(f"{mark} {r.source_id}")
            lines.append(f"  status: {r.status.value}")
            lines.append(f"  auth: {r.authentication.value}")
            lines.append(f"  detail: {r.detail}")
            lines.append("")
        return "\n".join(lines)


def probe_sources(sources: Iterable[DataSource]) -> SourceHealthBoard:
    reports: list[AvailabilityReport] = []
    zero_total = 0
    zero_ok = 0
    for src in sources:
        report = src.availability()
        reports.append(report)
        from botscope.sources.base import AuthenticationMode

        if src.authentication == AuthenticationMode.NONE:
            zero_total += 1
            if report.status in {
                SourceStatus.ACTIVE,
                SourceStatus.AVAILABLE,
                SourceStatus.CACHED,
                SourceStatus.OFFLINE_CACHED,
                SourceStatus.DEGRADED,
            }:
                zero_ok += 1
    mode = "ZERO-AUTH"
    # If any REQUIRED_TOKEN source is ACTIVE, note mixed mode
    if any(
        r.status == SourceStatus.ACTIVE
        and r.authentication.value == "REQUIRED_TOKEN"
        for r in reports
    ):
        mode = "MIXED (zero-auth + optional authenticated)"
    return SourceHealthBoard(
        checked_at=datetime.now(timezone.utc).isoformat(),
        reports=reports,
        mode=mode,
        zero_auth_available=zero_ok,
        zero_auth_total=zero_total,
    )
