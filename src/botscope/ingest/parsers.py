"""Ingest parsers for authorized traffic sources."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from botscope.normalize.event import NormalizedEvent, SourceType

# Combined / common log format (NGINX/Apache-compatible)
COMBINED_RE = re.compile(
    r'^(?P<remote>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)(?:\s+(?P<proto>[^"]+))?"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

TIME_FORMATS = (
    "%d/%b/%Y:%H:%M:%S %z",
    "%d/%b/%Y:%H:%M:%S",
)


def parse_log_time(value: str) -> datetime:
    for fmt in TIME_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return datetime.now(timezone.utc)


class BaseParser(ABC):
    source_type: SourceType = SourceType.UNKNOWN

    @abstractmethod
    def parse_line(self, line: str, *, line_no: int = 0) -> NormalizedEvent | None:
        raise NotImplementedError

    def parse_file(self, path: str | Path, *, max_bytes: int = 512 * 1024 * 1024) -> Iterator[NormalizedEvent]:
        path = Path(path)
        size = path.stat().st_size
        if size > max_bytes:
            raise ValueError(
                f"File exceeds safety limit ({size} > {max_bytes} bytes). "
                "Raise max_bytes deliberately if you authorize larger imports."
            )
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                event = self.parse_line(line.rstrip("\n"), line_no=line_no)
                if event is not None:
                    yield event


class CombinedLogParser(BaseParser):
    """NGINX/Apache combined / common access log parser."""

    source_type = SourceType.WEB_LOG

    def parse_line(self, line: str, *, line_no: int = 0) -> NormalizedEvent | None:
        if not line or line.startswith("#"):
            return None
        match = COMBINED_RE.match(line)
        if not match:
            return None
        groups = match.groupdict()
        size_raw = groups.get("size") or "-"
        bytes_out = None if size_raw == "-" else int(size_raw)
        return NormalizedEvent(
            timestamp=parse_log_time(groups["time"]),
            source_type=self.source_type,
            protocol=(groups.get("proto") or "HTTP").split("/")[0],
            src_address=groups["remote"],
            http_method=groups.get("method"),
            path=groups.get("path"),
            status=int(groups["status"]),
            user_agent=groups.get("ua") or None,
            bytes_out=bytes_out,
            transport="tcp",
            raw_ref=f"line:{line_no}",
            extras={"referer": groups.get("referer")} if groups.get("referer") else {},
        )


class JsonLogParser(BaseParser):
    """Structured JSON access logs (one object per line)."""

    source_type = SourceType.WEB_LOG

    FIELD_MAP = {
        "remote_addr": "src_address",
        "client_ip": "src_address",
        "ip": "src_address",
        "request_method": "http_method",
        "method": "http_method",
        "request_uri": "path",
        "uri": "path",
        "path": "path",
        "status": "status",
        "http_user_agent": "user_agent",
        "user_agent": "user_agent",
        "ua": "user_agent",
        "host": "host",
        "http_host": "host",
        "bytes_sent": "bytes_out",
        "body_bytes_sent": "bytes_out",
        "request_time": "duration",
        "asn": "asn",
        "network_owner": "network_owner",
        "reverse_dns": "reverse_dns",
        "forward_dns": "forward_dns",
    }

    def parse_line(self, line: str, *, line_no: int = 0) -> NormalizedEvent | None:
        line = line.strip()
        if not line:
            return None
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        kwargs: dict = {
            "source_type": self.source_type,
            "raw_ref": f"line:{line_no}",
            "protocol": "HTTP",
            "transport": "tcp",
        }
        for src, dest in self.FIELD_MAP.items():
            if src in payload and payload[src] is not None:
                kwargs[dest] = payload[src]

        ts = payload.get("time") or payload.get("timestamp") or payload.get("@timestamp")
        if isinstance(ts, str):
            try:
                kwargs["timestamp"] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Coerce numerics carefully
        for key in ("status", "bytes_out", "bytes_in", "asn", "src_port", "dst_port"):
            if key in kwargs and kwargs[key] is not None:
                try:
                    kwargs[key] = int(kwargs[key])
                except (TypeError, ValueError):
                    kwargs.pop(key, None)
        if "duration" in kwargs and kwargs["duration"] is not None:
            try:
                kwargs["duration"] = float(kwargs["duration"])
            except (TypeError, ValueError):
                kwargs.pop("duration", None)

        return NormalizedEvent(**kwargs)


def detect_parser(path: str | Path) -> BaseParser:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return JsonLogParser()
    # Peek first non-empty line
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            sample = line.strip()
            if not sample:
                continue
            if sample.startswith("{"):
                return JsonLogParser()
            return CombinedLogParser()
    return CombinedLogParser()


def iter_events(path: str | Path, *, max_bytes: int = 512 * 1024 * 1024) -> Iterator[NormalizedEvent]:
    path = Path(path)
    from botscope.ingest.pcap import is_pcap_path, iter_pcap_events

    if is_pcap_path(path):
        yield from iter_pcap_events(path, max_bytes=max_bytes)
        return
    parser = detect_parser(path)
    yield from parser.parse_file(path, max_bytes=max_bytes)
