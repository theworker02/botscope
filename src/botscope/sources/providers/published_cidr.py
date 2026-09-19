"""Generic published CIDR JSON provider — zero-auth identity evidence."""

from __future__ import annotations

import ipaddress
import json
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from botscope.sources.base import (
    AuthenticationMode,
    AvailabilityReport,
    DataSource,
    MeasurementType,
    NormalizedSourceObservation,
    ObservationKind,
    SourceQuery,
    SourceStatus,
)
from botscope.sources.bot_identity.cidr_util import (
    ip_in_networks,
    parse_prefix_list,
    validate_prefix_document,
)
from botscope.sources.cache import HttpSourceCache


class PublishedCidrSource(DataSource):
    """Fetch an operator-published prefixes JSON document (Google/Bing-shaped)."""

    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.BOT_IDENTITY_RANGES

    def __init__(
        self,
        *,
        source_id: str,
        name: str,
        url: str,
        operator: str,
        population: str,
        tier: str = "A",
        cache: HttpSourceCache | None = None,
        min_refresh_seconds: float = 3600.0,
    ) -> None:
        self.source_id = source_id
        self.name = name
        self.url = url
        self.operator = operator
        self.population = population
        self.tier = tier
        self.cache = cache or HttpSourceCache(min_refresh_seconds=min_refresh_seconds)
        self._last_receipt = None
        self._networks: list[ipaddress._BaseNetwork] = []
        self._parser = f"{source_id}.v1"

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                self.url,
                source_id=self.source_id,
                parser=self._parser,
                authentication="NONE",
                timeout=20.0,
            )
            self._last_receipt = receipt
            data = json.loads(body)
            prefixes = data.get("prefixes") or (data.get("creationTime") and data.get("prefixes")) or []
            if isinstance(data, dict) and "prefixes" not in data:
                # Some feeds nest differently — still report reachable
                n = len(data) if isinstance(data, dict) else 0
                detail = f"reachable; schema keys={list(data)[:6]}"
            else:
                n = len(prefixes) if isinstance(prefixes, list) else 0
                detail = f"{n} prefixes; creationTime={data.get('creationTime')}"
            status = SourceStatus.OFFLINE_CACHED if receipt.from_cache else SourceStatus.ACTIVE
            # ACTIVE here means "available/fresh"; GUI maps to AVAILABLE when not contributing
            return AvailabilityReport(
                source_id=self.source_id,
                status=status,
                detail=detail,
                http_status=receipt.http_status,
                latency_ms=(time.perf_counter() - started) * 1000,
                authentication=self.authentication,
                cached=receipt.from_cache,
            )
        except Exception as exc:
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.UNAVAILABLE,
                detail=str(exc),
                authentication=self.authentication,
            )

    def metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "authentication": "NONE",
            "urls": [self.url],
            "operator": self.operator,
            "tier": self.tier,
            "capabilities": ["BOT_IDENTITY", "IP_RANGE", "VALIDATION"],
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        force = bool(query and query.extras.get("force"))
        body, receipt = self.cache.get(
            self.url,
            source_id=self.source_id,
            parser=self._parser,
            authentication="NONE",
            force=force,
        )
        self._last_receipt = receipt
        data = json.loads(body)
        # Accept Google-style prefixes; also accept list-of-cidr strings
        if isinstance(data, list):
            data = {
                "prefixes": [
                    {"ipv4Prefix": x} if isinstance(x, str) and ":" not in x else {"ipv6Prefix": x}
                    if isinstance(x, str)
                    else x
                    for x in data
                ]
            }
        issues = validate_prefix_document(data)
        if issues:
            # Soft-fail: try alternate shapes used by some vendors
            if isinstance(data, dict):
                for key in ("prefixes", "ips", "ip_ranges", "ranges"):
                    if key in data and isinstance(data[key], list):
                        issues = []
                        break
            if issues:
                receipt.validation = "FAIL"
                receipt.validation_notes = issues
                raise ValueError(f"{self.source_id} schema validation failed: {issues}")
        self._networks = parse_prefix_list(data) if "prefixes" in data else []
        return {"payload": data, "receipt": receipt, "url": self.url}

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "payload" in data:
            data = data["payload"]
        return validate_prefix_document(data)

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        payload = response["payload"] if isinstance(response, dict) and "payload" in response else response
        receipt = response.get("receipt") if isinstance(response, dict) else self._last_receipt
        now = datetime.now(timezone.utc).isoformat()
        prefixes = payload.get("prefixes") if isinstance(payload, dict) else []
        if not isinstance(prefixes, list):
            prefixes = []
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=now,
                measurement_type=self.measurement_type,
                kind=ObservationKind.SOURCE_REPORTED,
                metric_name="published_prefix_count",
                metric_value=len(prefixes),
                unit="cidrs",
                population=self.population,
                denominator="CIDR prefixes in published feed",
                temporal_start=payload.get("creationTime") if isinstance(payload, dict) else None,
                temporal_end=payload.get("creationTime") if isinstance(payload, dict) else None,
                geographic_scope="Operator-published crawler egress",
                methodology_note=f"Official/public feed: {self.url}",
                limitations=[
                    "Does not alone verify a User-Agent claim",
                    "IP match without DNS corroboration is incomplete verification",
                ],
                extras={
                    "operator": self.operator,
                    "tier": self.tier,
                    "creationTime": payload.get("creationTime") if isinstance(payload, dict) else None,
                },
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]

    def contains_ip(self, address: str) -> bool:
        if not self._networks:
            try:
                fetched = self.fetch()
                self._networks = parse_prefix_list(fetched["payload"])
            except Exception:
                return False
        return ip_in_networks(address, self._networks)


def builtin_published_cidr_sources(
    cache: HttpSourceCache | None = None,
) -> list[PublishedCidrSource]:
    """Zero-auth crawler IP / infrastructure feeds (real endpoints)."""
    specs = [
        ("openai.gptbot", "OpenAI GPTBot IP Ranges", "https://openai.com/gptbot.json", "openai", "OpenAI GPTBot published ranges"),
        ("openai.searchbot", "OpenAI OAI-SearchBot Ranges", "https://openai.com/searchbot.json", "openai", "OpenAI SearchBot published ranges"),
        ("openai.chatgpt_user", "OpenAI ChatGPT-User Ranges", "https://openai.com/chatgpt-user.json", "openai", "OpenAI ChatGPT-User published ranges"),
        ("anthropic.claude_bots", "Anthropic Claude Bot Ranges", "https://claude.com/crawling/bots.json", "anthropic", "Anthropic published crawler ranges"),
        ("perplexity.bot", "PerplexityBot IP Ranges", "https://www.perplexity.com/perplexitybot.json", "perplexity", "PerplexityBot published ranges"),
        ("perplexity.user", "Perplexity-User IP Ranges", "https://www.perplexity.com/perplexity-user.json", "perplexity", "Perplexity-User published ranges"),
        ("apple.applebot", "Applebot IP Ranges", "https://search.developer.apple.com/applebot.json", "apple", "Applebot published ranges"),
    ]
    return [
        PublishedCidrSource(
            source_id=sid,
            name=name,
            url=url,
            operator=op,
            population=pop,
            cache=cache,
        )
        for sid, name, url, op, pop in specs
    ]
