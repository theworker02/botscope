"""Machine-readable BotScope source registry entries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from botscope.sources.base import AuthenticationMode, Cadence, MeasurementType, SourceStatus


@dataclass
class SourceRegistryEntry:
    source_id: str
    name: str
    operator: str
    homepage: str
    documentation: str
    measurement_type: MeasurementType
    authentication_required: bool
    authentication_mode: AuthenticationMode
    license: str
    update_frequency: Cadence
    geographic_scope: str
    temporal_scope: str
    bot_visibility: str
    human_visibility: str
    network_visibility: str
    methodology: str
    known_biases: list[str]
    last_verified: str
    status: SourceStatus
    endpoints: list[str] = field(default_factory=list)
    optional_auth: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["measurement_type"] = self.measurement_type.value
        data["authentication_mode"] = self.authentication_mode.value
        data["update_frequency"] = self.update_frequency.value
        data["status"] = self.status.value
        return data


# Entries verified against live public documentation / retrieval on 2026-09-18.
REGISTRY: list[SourceRegistryEntry] = [
    SourceRegistryEntry(
        source_id="commoncrawl.collinfo",
        name="Common Crawl Index Catalog",
        operator="Common Crawl Foundation",
        homepage="https://commoncrawl.org/",
        documentation="https://index.commoncrawl.org/ https://commoncrawl.org/get-started",
        measurement_type=MeasurementType.WEB_CRAWL_DATASET,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Common Crawl data is publicly available; review Common Crawl terms for reuse",
        update_frequency=Cadence.MONTHLY,
        geographic_scope="Global web crawl sample (not a traffic census)",
        temporal_scope="Per-crawl windows published in collinfo.json",
        bot_visibility="Crawler-centric corpus — does not measure live Internet traffic share",
        human_visibility="Indirect (pages humans publish); not interactive HTTP traffic",
        network_visibility="Web URL/content captures via WARC/WAT/WET + CDX indexes",
        methodology=(
            "BotScope retrieves https://index.commoncrawl.org/collinfo.json over HTTPS "
            "with no credentials. Observations describe the crawl catalog (ids, windows, "
            "CDX endpoints), not bot/human traffic percentages."
        ),
        known_biases=[
            "Crawl schedule and politeness bias which sites appear",
            "Not representative of all Internet traffic",
            "English/web-centric skew possible",
            "Must never be used as Internet bot-traffic prevalence",
        ],
        last_verified="2026-09-18",
        status=SourceStatus.ACTIVE,
        endpoints=["https://index.commoncrawl.org/collinfo.json"],
        notes="ZERO-AUTH. Measurement perspective: WEB CRAWL DATASET.",
    ),
    SourceRegistryEntry(
        source_id="google.crawler_ip_ranges",
        name="Google Crawler IP Ranges",
        operator="Google",
        homepage="https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests",
        documentation=(
            "https://developers.google.com/static/crawling/ipranges/common-crawlers.json"
        ),
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Google for crawler verification; follow Google documentation terms",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global Google crawler egress prefixes",
        temporal_scope="Snapshot as of creationTime in JSON",
        bot_visibility="Strong for Google crawlers when combined with FCrDNS",
        human_visibility="N/A — identity ranges, not traffic share",
        network_visibility="IPv4/IPv6 CIDR prefixes (common + special)",
        methodology=(
            "BotScope fetches Google's published common-crawlers.json and "
            "special-crawlers.json. User-Agent alone remains insufficient for VERIFIED identity."
        ),
        known_biases=[
            "Covers Google-published crawler ranges only",
            "IP match without DNS corroboration is incomplete verification",
        ],
        last_verified="2026-09-18",
        status=SourceStatus.ACTIVE,
        endpoints=[
            "https://developers.google.com/static/crawling/ipranges/common-crawlers.json",
            "https://developers.google.com/static/crawling/ipranges/special-crawlers.json",
        ],
        notes="ZERO-AUTH identity evidence (common + special).",
    ),
    SourceRegistryEntry(
        source_id="bing.bingbot_ip_ranges",
        name="Bingbot Published IP Ranges",
        operator="Microsoft",
        homepage="https://www.bing.com/webmasters/help/how-to-verify-bingbot-3905dc26",
        documentation="https://www.bing.com/toolbox/bingbot.json",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Microsoft for Bingbot verification; follow Bing documentation terms",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global Bingbot egress prefixes",
        temporal_scope="Snapshot as of creationTime in JSON",
        bot_visibility="Strong for Bingbot when combined with FCrDNS under search.msn.com",
        human_visibility="N/A — identity ranges, not traffic share",
        network_visibility="IPv4/IPv6 CIDR prefixes",
        methodology=(
            "BotScope fetches https://www.bing.com/toolbox/bingbot.json with no credentials. "
            "Range membership corroborates Bingbot claims; it is not sole verification."
        ),
        known_biases=[
            "Covers Bingbot published ranges only",
            "IP match without DNS corroboration is incomplete verification",
        ],
        last_verified="2026-09-18",
        status=SourceStatus.ACTIVE,
        endpoints=["https://www.bing.com/toolbox/bingbot.json"],
        notes="ZERO-AUTH identity evidence.",
    ),
    SourceRegistryEntry(
        source_id="cloudflare.radar",
        name="Cloudflare Radar",
        operator="Cloudflare",
        homepage="https://radar.cloudflare.com/",
        documentation="https://developers.cloudflare.com/radar/",
        measurement_type=MeasurementType.PROVIDER_HTTP_TRAFFIC,
        authentication_required=True,
        authentication_mode=AuthenticationMode.REQUIRED_TOKEN,
        license="Cloudflare API / Radar terms; user-provided token required",
        update_frequency=Cadence.NEAR_REAL_TIME,
        geographic_scope="Traffic through Cloudflare's network (large but non-random)",
        temporal_scope="API dateRange parameters (e.g. 7d)",
        bot_visibility="LIKELY_AUTOMATED / LIKELY_HUMAN botClass dimensions",
        human_visibility="LIKELY_HUMAN class from Cloudflare classification",
        network_visibility="HTTP(S) requests reaching Cloudflare CDN edge",
        methodology=(
            "OPTIONAL_AUTH_SOURCE. Requires user Cloudflare API token with Radar Read. "
            "BotScope never ships tokens and never bypasses auth. Values describe "
            "Cloudflare-observed HTTP traffic — not the entire Internet."
        ),
        known_biases=[
            "Cloudflare customer / edge bias",
            "Classification is Cloudflare's methodology, not BotScope's",
            "Not a random sample of all Internet traffic",
        ],
        last_verified="2026-09-18",
        status=SourceStatus.AUTH_REQUIRED,
        endpoints=["https://api.cloudflare.com/client/v4/radar/"],
        optional_auth=True,
        notes="AUTH_REQUIRED until user supplies Radar Read token. Optional.",
    ),
    SourceRegistryEntry(
        source_id="openai.gptbot",
        name="OpenAI GPTBot IP Ranges",
        operator="OpenAI",
        homepage="https://openai.com/gptbot.json",
        documentation="https://platform.openai.com/docs/bots",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by OpenAI for crawler verification",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global GPTBot egress prefixes",
        temporal_scope="Snapshot as published",
        bot_visibility="Strong for GPTBot when combined with UA + reverse DNS where applicable",
        human_visibility="N/A — identity ranges",
        network_visibility="IPv4/IPv6 CIDR prefixes",
        methodology="ZERO-AUTH fetch of openai.com/gptbot.json",
        known_biases=["Covers published GPTBot ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://openai.com/gptbot.json"],
        notes="Tier A identity evidence.",
    ),
    SourceRegistryEntry(
        source_id="openai.searchbot",
        name="OpenAI OAI-SearchBot Ranges",
        operator="OpenAI",
        homepage="https://openai.com/searchbot.json",
        documentation="https://platform.openai.com/docs/bots",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by OpenAI",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global",
        temporal_scope="Snapshot as published",
        bot_visibility="SearchBot identity ranges",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of openai.com/searchbot.json",
        known_biases=["Published ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://openai.com/searchbot.json"],
    ),
    SourceRegistryEntry(
        source_id="openai.chatgpt_user",
        name="OpenAI ChatGPT-User Ranges",
        operator="OpenAI",
        homepage="https://openai.com/chatgpt-user.json",
        documentation="https://platform.openai.com/docs/bots",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by OpenAI",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global",
        temporal_scope="Snapshot as published",
        bot_visibility="ChatGPT-User browsing agent ranges",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of openai.com/chatgpt-user.json",
        known_biases=["Published ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://openai.com/chatgpt-user.json"],
    ),
    SourceRegistryEntry(
        source_id="anthropic.claude_bots",
        name="Anthropic Claude Bot Ranges",
        operator="Anthropic",
        homepage="https://claude.com/crawling/bots.json",
        documentation="https://support.anthropic.com/",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Anthropic",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global",
        temporal_scope="Snapshot as published",
        bot_visibility="Claude crawler ranges",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of claude.com/crawling/bots.json",
        known_biases=["Published ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://claude.com/crawling/bots.json"],
    ),
    SourceRegistryEntry(
        source_id="perplexity.bot",
        name="PerplexityBot IP Ranges",
        operator="Perplexity",
        homepage="https://www.perplexity.com/perplexitybot.json",
        documentation="https://docs.perplexity.ai/",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Perplexity",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global",
        temporal_scope="Snapshot as published",
        bot_visibility="PerplexityBot ranges",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of perplexitybot.json",
        known_biases=["Published ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://www.perplexity.com/perplexitybot.json"],
    ),
    SourceRegistryEntry(
        source_id="perplexity.user",
        name="Perplexity-User IP Ranges",
        operator="Perplexity",
        homepage="https://www.perplexity.com/perplexity-user.json",
        documentation="https://docs.perplexity.ai/",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Perplexity",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global",
        temporal_scope="Snapshot as published",
        bot_visibility="Perplexity-User agent ranges",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of perplexity-user.json",
        known_biases=["Published ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://www.perplexity.com/perplexity-user.json"],
    ),
    SourceRegistryEntry(
        source_id="apple.applebot",
        name="Applebot IP Ranges",
        operator="Apple",
        homepage="https://search.developer.apple.com/applebot.json",
        documentation="https://support.apple.com/en-us/119829",
        measurement_type=MeasurementType.BOT_IDENTITY_RANGES,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Apple",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global",
        temporal_scope="Snapshot as published",
        bot_visibility="Applebot ranges",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of applebot.json",
        known_biases=["Published ranges only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://search.developer.apple.com/applebot.json"],
    ),
    SourceRegistryEntry(
        source_id="google.cloud_ip_ranges",
        name="Google Cloud / Product IP Ranges",
        operator="Google",
        homepage="https://www.gstatic.com/ipranges/goog.json",
        documentation="https://support.google.com/a/answer/10026322",
        measurement_type=MeasurementType.ROUTING,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Google",
        update_frequency=Cadence.DAILY,
        geographic_scope="Global Google product/cloud egress",
        temporal_scope="creationTime in JSON",
        bot_visibility="Indirect — product ranges, not crawler-only",
        human_visibility="N/A",
        network_visibility="CIDR prefixes",
        methodology="ZERO-AUTH fetch of goog.json (distinct from crawler feeds)",
        known_biases=[
            "Not a substitute for google.crawler_ip_ranges",
            "Not a traffic-share source",
        ],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://www.gstatic.com/ipranges/goog.json"],
        notes="Tier B contextual / validation.",
    ),
    SourceRegistryEntry(
        source_id="cloudflare.edge_ips",
        name="Cloudflare Edge IPv4 Ranges",
        operator="Cloudflare",
        homepage="https://www.cloudflare.com/ips/",
        documentation="https://www.cloudflare.com/ips-v4",
        measurement_type=MeasurementType.ROUTING,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by Cloudflare",
        update_frequency=Cadence.WEEKLY,
        geographic_scope="Cloudflare edge network",
        temporal_scope="As published",
        bot_visibility="N/A — infrastructure",
        human_visibility="N/A",
        network_visibility="IPv4 prefixes",
        methodology="ZERO-AUTH plaintext list at cloudflare.com/ips-v4",
        known_biases=["Infra context only — never a bot-share"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://www.cloudflare.com/ips-v4"],
        notes="Tier C contextual.",
    ),
    SourceRegistryEntry(
        source_id="aws.ip_ranges",
        name="AWS IP Ranges",
        operator="Amazon Web Services",
        homepage="https://ip-ranges.amazonaws.com/ip-ranges.json",
        documentation="https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html",
        measurement_type=MeasurementType.ROUTING,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="Published by AWS",
        update_frequency=Cadence.DAILY,
        geographic_scope="AWS global regions",
        temporal_scope="syncToken / createDate in JSON",
        bot_visibility="Indirect — cloud hosting context",
        human_visibility="N/A",
        network_visibility="IPv4/IPv6 prefixes by service",
        methodology="ZERO-AUTH fetch of ip-ranges.amazonaws.com/ip-ranges.json",
        known_biases=["Cloud infra — not bot identity", "Not a traffic-share source"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://ip-ranges.amazonaws.com/ip-ranges.json"],
        notes="Tier C contextual.",
    ),
    SourceRegistryEntry(
        source_id="github.meta",
        name="GitHub Meta IP Hints",
        operator="GitHub",
        homepage="https://api.github.com/meta",
        documentation="https://docs.github.com/en/rest/meta",
        measurement_type=MeasurementType.ROUTING,
        authentication_required=False,
        authentication_mode=AuthenticationMode.NONE,
        license="GitHub API terms",
        update_frequency=Cadence.WEEKLY,
        geographic_scope="GitHub service prefixes",
        temporal_scope="As published",
        bot_visibility="N/A — infrastructure",
        human_visibility="N/A",
        network_visibility="Service CIDR hints",
        methodology="ZERO-AUTH GET api.github.com/meta",
        known_biases=["Infra context only"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        endpoints=["https://api.github.com/meta"],
        notes="Tier C contextual.",
    ),
    SourceRegistryEntry(
        source_id="botscope.local_sensor",
        name="Local BotScope Sensor",
        operator="User",
        homepage="",
        documentation="docs/GUI.md",
        measurement_type=MeasurementType.LOCAL_SENSOR,
        authentication_required=False,
        authentication_mode=AuthenticationMode.USER_PROVIDED,
        license="User-controlled data",
        update_frequency=Cadence.ON_DEMAND,
        geographic_scope="Whatever the local sensor observes",
        temporal_scope="Analysis session window",
        bot_visibility="BotScope classification of authorized local traffic",
        human_visibility="HUMAN-LIKELY classifications where evidence supports",
        network_visibility="Depends on log/capture source",
        methodology="Local Observatory pipeline (ingest → classify → aggregate).",
        known_biases=["Single-sensor / site bias", "Log format incompleteness"],
        last_verified="2026-09-18",
        status=SourceStatus.AVAILABLE,
        notes="Always available when user loads data. No connection wizard.",
    ),
]


def get_entry(source_id: str) -> SourceRegistryEntry | None:
    for entry in REGISTRY:
        if entry.source_id == source_id:
            return entry
    return None


def registry_as_dicts() -> list[dict[str, Any]]:
    return [e.to_dict() for e in REGISTRY]


def zero_auth_entries() -> list[SourceRegistryEntry]:
    return [
        e
        for e in REGISTRY
        if not e.authentication_required and e.authentication_mode == AuthenticationMode.NONE
    ]
