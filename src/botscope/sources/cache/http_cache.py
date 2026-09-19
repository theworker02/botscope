"""HTTP cache + Source Receipts for federated public data."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from platformdirs import user_cache_dir


@dataclass
class SourceReceipt:
    receipt_id: str
    source_id: str
    url: str
    retrieved_at: str
    transport: str = "HTTPS"
    authentication: str = "NONE"
    http_status: int | None = None
    content_type: str | None = None
    size_bytes: int = 0
    sha256: str = ""
    etag: str | None = None
    last_modified: str | None = None
    parser: str = ""
    validation: str = "PASS"
    validation_notes: list[str] = field(default_factory=list)
    from_cache: bool = False
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def format_text(self) -> str:
        lines = [
            "BOTSCOPE SOURCE RECEIPT",
            f"Receipt ID: {self.receipt_id}",
            f"Source: {self.source_id}",
            f"Retrieved: {self.retrieved_at}",
            f"URL: {self.url}",
            f"Transport: {self.transport}",
            f"Authentication: {self.authentication}",
            f"Status: {self.http_status}",
            f"Content-Type: {self.content_type}",
            f"Size: {self.size_bytes}",
            f"SHA-256: {self.sha256}",
            f"Parser: {self.parser}",
            f"Validation: {self.validation}",
            f"From cache: {self.from_cache}",
        ]
        for note in self.validation_notes:
            lines.append(f"Note: {note}")
        return "\n".join(lines)


def cache_root() -> Path:
    root = Path(user_cache_dir("botscope", "botscope")) / "sources"
    root.mkdir(parents=True, exist_ok=True)
    return root


def receipts_dir() -> Path:
    path = cache_root() / "receipts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


class HttpSourceCache:
    """Local cache with ETag / Last-Modified and Source Receipts.

    Uses stdlib urllib so zero-auth Global Mode works without optional httpx.
    """

    def __init__(self, *, min_refresh_seconds: float = 300.0) -> None:
        self.min_refresh_seconds = min_refresh_seconds
        self.root = cache_root()

    def get(
        self,
        url: str,
        *,
        source_id: str,
        parser: str,
        authentication: str = "NONE",
        headers: dict[str, str] | None = None,
        force: bool = False,
        timeout: float = 30.0,
    ) -> tuple[bytes, SourceReceipt]:
        key = _url_key(url)
        meta_path = self.root / f"{key}.meta.json"
        body_path = self.root / f"{key}.body"
        now = time.time()

        cached_meta: dict[str, Any] | None = None
        if meta_path.exists() and body_path.exists():
            cached_meta = json.loads(meta_path.read_text(encoding="utf-8"))
            age = now - float(cached_meta.get("fetched_at_epoch", 0))
            if not force and age < self.min_refresh_seconds:
                body = body_path.read_bytes()
                receipt = self._receipt_from_meta(
                    cached_meta,
                    source_id=source_id,
                    parser=parser,
                    authentication=authentication,
                    body=body,
                    from_cache=True,
                )
                self._store_receipt(receipt)
                return body, receipt

        req_headers = {
            "User-Agent": "BotScope/0.1 (+https://github.com/theworker02/botscope; research)",
            "Accept": "application/json,text/plain,*/*",
        }
        if headers:
            req_headers.update(headers)
        if cached_meta and not force:
            if cached_meta.get("etag"):
                req_headers["If-None-Match"] = cached_meta["etag"]
            if cached_meta.get("last_modified"):
                req_headers["If-Modified-Since"] = cached_meta["last_modified"]

        request = urllib.request.Request(url, headers=req_headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                body = resp.read()
                status = getattr(resp, "status", 200)
                content_type = resp.headers.get("Content-Type")
                etag = resp.headers.get("ETag")
                last_modified = resp.headers.get("Last-Modified")
        except urllib.error.HTTPError as exc:
            if exc.code == 304 and body_path.exists() and cached_meta:
                body = body_path.read_bytes()
                receipt = self._receipt_from_meta(
                    cached_meta,
                    source_id=source_id,
                    parser=parser,
                    authentication=authentication,
                    body=body,
                    from_cache=True,
                )
                receipt.http_status = 304
                receipt.extras["revalidated"] = True
                self._store_receipt(receipt)
                return body, receipt
            raise

        digest = hashlib.sha256(body).hexdigest()
        meta = {
            "url": url,
            "fetched_at_epoch": now,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "http_status": status,
            "content_type": content_type,
            "etag": etag,
            "last_modified": last_modified,
            "sha256": digest,
            "size_bytes": len(body),
        }
        body_path.write_bytes(body)
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        receipt = SourceReceipt(
            receipt_id=str(uuid4()),
            source_id=source_id,
            url=url,
            retrieved_at=meta["retrieved_at"],
            authentication=authentication,
            http_status=status,
            content_type=content_type,
            size_bytes=len(body),
            sha256=digest,
            etag=etag,
            last_modified=last_modified,
            parser=parser,
            validation="PASS",
            from_cache=False,
        )
        self._store_receipt(receipt)
        return body, receipt

    def _receipt_from_meta(
        self,
        meta: dict[str, Any],
        *,
        source_id: str,
        parser: str,
        authentication: str,
        body: bytes,
        from_cache: bool,
    ) -> SourceReceipt:
        return SourceReceipt(
            receipt_id=str(uuid4()),
            source_id=source_id,
            url=meta["url"],
            retrieved_at=meta.get("retrieved_at")
            or datetime.now(timezone.utc).isoformat(),
            authentication=authentication,
            http_status=meta.get("http_status"),
            content_type=meta.get("content_type"),
            size_bytes=int(meta.get("size_bytes") or len(body)),
            sha256=meta.get("sha256") or hashlib.sha256(body).hexdigest(),
            etag=meta.get("etag"),
            last_modified=meta.get("last_modified"),
            parser=parser,
            validation="PASS",
            from_cache=from_cache,
        )

    def _store_receipt(self, receipt: SourceReceipt) -> None:
        path = receipts_dir() / f"{receipt.receipt_id}.json"
        path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
