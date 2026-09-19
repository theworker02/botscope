"""Canonical data-source adapter interface for BotScope federation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AuthenticationMode(str, Enum):
    NONE = "NONE"
    OPTIONAL_TOKEN = "OPTIONAL_TOKEN"
    REQUIRED_TOKEN = "REQUIRED_TOKEN"
    USER_PROVIDED = "USER_PROVIDED"


class MeasurementType(str, Enum):
    WEB_CRAWL_DATASET = "WEB_CRAWL_DATASET"
    PROVIDER_HTTP_TRAFFIC = "PROVIDER_HTTP_TRAFFIC"
    BOT_IDENTITY_RANGES = "BOT_IDENTITY_RANGES"
    LOCAL_SENSOR = "LOCAL_SENSOR"
    COMMUNITY_SENSOR = "COMMUNITY_SENSOR"
    ROUTING = "ROUTING"
    DNS = "DNS"
    OTHER = "OTHER"


class SourceStatus(str, Enum):
    """Operational provider state — prefer AVAILABLE/AUTH_REQUIRED over vague labels."""

    INITIALIZING = "INITIALIZING"
    AVAILABLE = "AVAILABLE"
    ACTIVE = "ACTIVE"
    CACHED = "CACHED"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    DEPRECATED = "DEPRECATED"
    EXPERIMENTAL = "EXPERIMENTAL"
    OFFLINE_CACHED = "OFFLINE_CACHED"  # synonym of CACHED used by adapters
    # Deprecated — do not use for public no-auth providers
    NOT_CONNECTED = "NOT_CONNECTED"


class Cadence(str, Enum):
    LIVE = "LIVE"
    NEAR_REAL_TIME = "NEAR-REAL-TIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    HISTORICAL = "HISTORICAL"
    ON_DEMAND = "ON_DEMAND"


class ObservationKind(str, Enum):
    """How a numeric claim relates to evidence — never hide this."""

    DIRECTLY_OBSERVED = "DIRECTLY OBSERVED"
    SOURCE_REPORTED = "SOURCE-REPORTED"
    BOTSCOPE_CLASSIFIED = "BOTSCOPE CLASSIFIED"
    BOTSCOPE_INFERRED = "BOTSCOPE INFERRED"
    BOTSCOPE_ESTIMATED = "BOTSCOPE ESTIMATED"


@dataclass
class SourceQuery:
    """Adapter fetch parameters (never used to invent endpoints)."""

    limit: int = 50
    crawl_id: str | None = None
    url_pattern: str | None = None
    date_range: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedSourceObservation:
    """One federated observation with explicit population + provenance."""

    source_id: str
    observation_id: str
    retrieved_at: str
    measurement_type: MeasurementType
    kind: ObservationKind
    metric_name: str
    metric_value: float | int | str | None
    unit: str | None
    population: str
    denominator: str
    temporal_start: str | None = None
    temporal_end: str | None = None
    geographic_scope: str | None = None
    methodology_note: str = ""
    limitations: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)
    receipt_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "observation_id": self.observation_id,
            "retrieved_at": self.retrieved_at,
            "measurement_type": self.measurement_type.value,
            "kind": self.kind.value,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "population": self.population,
            "denominator": self.denominator,
            "temporal_start": self.temporal_start,
            "temporal_end": self.temporal_end,
            "geographic_scope": self.geographic_scope,
            "methodology_note": self.methodology_note,
            "limitations": list(self.limitations),
            "extras": dict(self.extras),
            "receipt_id": self.receipt_id,
        }


@dataclass
class AvailabilityReport:
    source_id: str
    status: SourceStatus
    detail: str
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    http_status: int | None = None
    latency_ms: float | None = None
    authentication: AuthenticationMode = AuthenticationMode.NONE
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status.value,
            "detail": self.detail,
            "checked_at": self.checked_at,
            "http_status": self.http_status,
            "latency_ms": self.latency_ms,
            "authentication": self.authentication.value,
            "cached": self.cached,
        }


class DataSource(ABC):
    """Standardized public/user data source adapter."""

    source_id: str
    name: str
    authentication: AuthenticationMode
    measurement_type: MeasurementType

    @abstractmethod
    def availability(self) -> AvailabilityReport:
        raise NotImplementedError

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, query: SourceQuery | None = None) -> Any:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        raise NotImplementedError

    def validate(self, data: Any) -> list[str]:
        """Return human-readable validation issues (empty = PASS)."""
        if data is None:
            return ["empty response"]
        return []
