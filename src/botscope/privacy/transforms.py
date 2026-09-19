"""Privacy transforms — minimize sensitive data by design."""

from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

from botscope.normalize.event import NormalizedEvent


@dataclass
class PrivacyConfig:
    hash_ips: bool = False
    truncate_ips: bool = False
    ip_hash_salt: str = "botscope-local-salt-change-me"
    redact_query: bool = True
    path_redaction_patterns: list[str] = field(
        default_factory=lambda: [r"(?i)(token|key|password|secret|auth)="]
    )
    header_allowlist: list[str] | None = None
    exclude_payloads: bool = True
    retention_days: int | None = None


class PrivacyTransform:
    """Apply configurable privacy transforms to normalized events."""

    def __init__(self, config: PrivacyConfig | None = None) -> None:
        self.config = config or PrivacyConfig()
        self._path_res = [re.compile(p) for p in self.config.path_redaction_patterns]

    def apply(self, event: NormalizedEvent) -> NormalizedEvent:
        updates: dict = {}
        transforms: list[str] = list(event.privacy_transform)

        if event.src_address:
            updates["src_address"] = self._transform_ip(event.src_address, transforms)
        if event.dst_address:
            updates["dst_address"] = self._transform_ip(event.dst_address, transforms)

        if event.path and self.config.redact_query:
            updates["path"] = self._redact_path(event.path, transforms)

        if self.config.exclude_payloads and event.extras.get("payload") is not None:
            extras = dict(event.extras)
            extras.pop("payload", None)
            updates["extras"] = extras
            transforms.append("payload_excluded")

        updates["privacy_transform"] = transforms
        return event.model_copy(update=updates) if updates else event

    def _transform_ip(self, value: str, transforms: list[str]) -> str:
        if self.config.hash_ips:
            digest = hashlib.sha256(
                f"{self.config.ip_hash_salt}:{value}".encode()
            ).hexdigest()[:16]
            transforms.append("ip_hashed")
            return f"hash:{digest}"
        if self.config.truncate_ips:
            try:
                ip = ipaddress.ip_address(value)
            except ValueError:
                return value
            if isinstance(ip, ipaddress.IPv4Address):
                parts = value.split(".")
                transforms.append("ip_truncated")
                return ".".join([*parts[:3], "0"])
            # IPv6: zero lower 80 bits roughly via /48 keep
            exploded = ip.exploded.split(":")
            transforms.append("ip_truncated")
            return ":".join(exploded[:3] + ["0000"] * 5)
        return value

    def _redact_path(self, path: str, transforms: list[str]) -> str:
        parts = urlsplit(path if "://" in path else f"http://x{path}")
        query = parts.query
        changed = False
        if query:
            redacted = query
            for pattern in self._path_res:
                redacted2 = pattern.sub(r"\1=REDACTED", redacted)
                if redacted2 != redacted:
                    changed = True
                    redacted = redacted2
            # Always strip query for default privacy unless empty after redaction preference
            # Default: redact sensitive keys but keep structure; also drop raw query if configured.
            new_path = urlunsplit(("", "", parts.path or path.split("?", 1)[0], redacted, ""))
            # urlsplit on synthetic URL — rebuild relative
            if path.startswith("/"):
                result = parts.path + (("?" + redacted) if redacted else "")
            else:
                result = new_path
            if changed or "?" in path:
                transforms.append("query_redacted")
            return result if path.startswith("http") else (
                (parts.path or path.split("?", 1)[0]) + (("?" + redacted) if redacted else "")
            )
        return path
