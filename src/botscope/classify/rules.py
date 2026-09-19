"""Deterministic, versioned classification rules."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from botscope.classify.result import EvidenceItem
from botscope.classify.taxonomy import BotCategory
from botscope.normalize.event import NormalizedEvent


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    category: BotCategory
    confidence: float
    evidence: EvidenceItem


RuleFn = Callable[[NormalizedEvent], RuleMatch | None]


def _ua(event: NormalizedEvent) -> str:
    return (event.user_agent or "").lower()


def _path(event: NormalizedEvent) -> str:
    return (event.path or "").lower()


def rule_search_applebot(event: NormalizedEvent) -> RuleMatch | None:
    if "applebot" not in _ua(event):
        return None
    return RuleMatch(
        rule_id="BS-RULE-SEARCH-003",
        category=BotCategory.VERIFIED_SEARCH_CRAWLER,
        confidence=0.55,
        evidence=EvidenceItem(
            statement="User-Agent claims Applebot",
            polarity="for",
            rule_id="BS-RULE-SEARCH-003",
            weight=0.55,
        ),
    )


def rule_search_duckduckbot(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if "duckduckbot" not in ua and "duckduckgo-favicons-bot" not in ua:
        return None
    return RuleMatch(
        rule_id="BS-RULE-SEARCH-004",
        category=BotCategory.VERIFIED_SEARCH_CRAWLER,
        confidence=0.55,
        evidence=EvidenceItem(
            statement="User-Agent claims DuckDuckBot",
            polarity="for",
            rule_id="BS-RULE-SEARCH-004",
            weight=0.55,
        ),
    )


def rule_search_yandex(event: NormalizedEvent) -> RuleMatch | None:
    if "yandexbot" not in _ua(event) and "yandex.com/bots" not in _ua(event):
        return None
    return RuleMatch(
        rule_id="BS-RULE-SEARCH-005",
        category=BotCategory.VERIFIED_SEARCH_CRAWLER,
        confidence=0.55,
        evidence=EvidenceItem(
            statement="User-Agent claims YandexBot",
            polarity="for",
            rule_id="BS-RULE-SEARCH-005",
            weight=0.55,
        ),
    )


def rule_ai_amazonbot(event: NormalizedEvent) -> RuleMatch | None:
    if "amazonbot" not in _ua(event):
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-005",
        category=BotCategory.AI_CRAWLER,
        confidence=0.58,
        evidence=EvidenceItem(
            statement="User-Agent matches Amazonbot",
            polarity="for",
            rule_id="BS-RULE-AI-005",
            weight=0.58,
        ),
    )


def rule_ai_meta_external(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if "meta-externalagent" not in ua and "facebookbot" not in ua:
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-006",
        category=BotCategory.AI_CRAWLER,
        confidence=0.58,
        evidence=EvidenceItem(
            statement="User-Agent matches Meta external / AI fetcher token",
            polarity="for",
            rule_id="BS-RULE-AI-006",
            weight=0.58,
        ),
    )


def rule_ai_perplexity(event: NormalizedEvent) -> RuleMatch | None:
    if "perplexitybot" not in _ua(event):
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-007",
        category=BotCategory.AI_CRAWLER,
        confidence=0.58,
        evidence=EvidenceItem(
            statement="User-Agent matches PerplexityBot",
            polarity="for",
            rule_id="BS-RULE-AI-007",
            weight=0.58,
        ),
    )


def rule_scraper(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    scrapers = (
        "semrushbot",
        "ahrefsbot",
        "mj12bot",
        "dotbot",
        "petalbot",
        "scrapy",
        "dataforseobot",
    )
    hit = next((t for t in scrapers if t in ua), None)
    if not hit:
        return None
    return RuleMatch(
        rule_id="BS-RULE-SCRAPER-001",
        category=BotCategory.SCRAPER,
        confidence=0.72,
        evidence=EvidenceItem(
            statement=f"User-Agent matches known SEO/scraper bot ({hit})",
            polarity="for",
            rule_id="BS-RULE-SCRAPER-001",
            weight=0.72,
        ),
    )


def rule_api_automation(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    path = _path(event)
    clients = ("python-requests", "go-http-client", "okhttp", "apache-httpclient", "java/")
    client_hit = next((t for t in clients if t in ua), None)
    api_path = path.startswith("/api/") or path.startswith("/v1/") or path.startswith("/v2/")
    if client_hit and api_path:
        return RuleMatch(
            rule_id="BS-RULE-API-001",
            category=BotCategory.API_AUTOMATION,
            confidence=0.72,
            evidence=EvidenceItem(
                statement=f"HTTP client library ({client_hit}) targeting API path",
                polarity="for",
                rule_id="BS-RULE-API-001",
                weight=0.72,
            ),
        )
    return None


def rule_search_googlebot(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if "googlebot" not in ua:
        return None
    return RuleMatch(
        rule_id="BS-RULE-SEARCH-001",
        category=BotCategory.VERIFIED_SEARCH_CRAWLER,
        confidence=0.55,  # UA claim alone — identity engine may upgrade
        evidence=EvidenceItem(
            statement="User-Agent claims Googlebot",
            polarity="for",
            rule_id="BS-RULE-SEARCH-001",
            weight=0.55,
        ),
    )


def rule_search_bingbot(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if "bingbot" not in ua and "adidxbot" not in ua:
        return None
    return RuleMatch(
        rule_id="BS-RULE-SEARCH-002",
        category=BotCategory.VERIFIED_SEARCH_CRAWLER,
        confidence=0.55,
        evidence=EvidenceItem(
            statement="User-Agent claims Bingbot",
            polarity="for",
            rule_id="BS-RULE-SEARCH-002",
            weight=0.55,
        ),
    )


def rule_ai_gptbot(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if "gptbot" not in ua and "chatgpt-user" not in ua:
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-001",
        category=BotCategory.AI_CRAWLER,
        confidence=0.6,
        evidence=EvidenceItem(
            statement="User-Agent matches known OpenAI crawler token",
            polarity="for",
            rule_id="BS-RULE-AI-001",
            weight=0.6,
        ),
    )


def rule_ai_claudebot(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if "claudebot" not in ua and "anthropic-ai" not in ua:
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-002",
        category=BotCategory.AI_CRAWLER,
        confidence=0.6,
        evidence=EvidenceItem(
            statement="User-Agent matches known Anthropic crawler token",
            polarity="for",
            rule_id="BS-RULE-AI-002",
            weight=0.6,
        ),
    )


def rule_ai_bytespider(event: NormalizedEvent) -> RuleMatch | None:
    if "bytespider" not in _ua(event):
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-003",
        category=BotCategory.AI_CRAWLER,
        confidence=0.55,
        evidence=EvidenceItem(
            statement="User-Agent matches Bytespider",
            polarity="for",
            rule_id="BS-RULE-AI-003",
            weight=0.55,
        ),
    )


def rule_ai_ccbot(event: NormalizedEvent) -> RuleMatch | None:
    if "ccbot" not in _ua(event):
        return None
    return RuleMatch(
        rule_id="BS-RULE-AI-004",
        category=BotCategory.AI_CRAWLER,
        confidence=0.55,
        evidence=EvidenceItem(
            statement="User-Agent matches Common Crawl CCBot",
            polarity="for",
            rule_id="BS-RULE-AI-004",
            weight=0.55,
        ),
    )


def rule_social_preview(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    tokens = (
        "facebookexternalhit",
        "twitterbot",
        "linkedinbot",
        "slackbot",
        "discordbot",
        "whatsapp",
    )
    hit = next((t for t in tokens if t in ua), None)
    if not hit:
        return None
    return RuleMatch(
        rule_id="BS-RULE-SOCIAL-001",
        category=BotCategory.SOCIAL_PREVIEW_BOT,
        confidence=0.65,
        evidence=EvidenceItem(
            statement=f"User-Agent matches social/preview bot token ({hit})",
            polarity="for",
            rule_id="BS-RULE-SOCIAL-001",
            weight=0.65,
        ),
    )


def rule_monitoring(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    path = _path(event)
    tokens = (
        "pingdom",
        "uptimerobot",
        "statuscake",
        "datadog",
        "newrelic",
        "prometheus",
        "node_exporter",
        "blackbox_exporter",
    )
    hit = next((t for t in tokens if t in ua), None)
    if hit:
        return RuleMatch(
            rule_id="BS-RULE-MON-001",
            category=BotCategory.MONITORING_HEALTH_CHECK,
            confidence=0.75,
            evidence=EvidenceItem(
                statement=f"User-Agent matches monitoring service ({hit})",
                polarity="for",
                rule_id="BS-RULE-MON-001",
                weight=0.75,
            ),
        )
    health_paths = {"/health", "/healthz", "/ready", "/readyz", "/livez", "/status", "/api/health"}
    if path in health_paths or path.rstrip("/") in health_paths:
        conf = 0.72 if any(t in ua for t in ("curl/", "wget/", "httpie/")) else 0.48
        return RuleMatch(
            rule_id="BS-RULE-MON-002",
            category=BotCategory.MONITORING_HEALTH_CHECK,
            confidence=conf,
            evidence=EvidenceItem(
                statement="Request targets common health-check path",
                polarity="for",
                rule_id="BS-RULE-MON-002",
                weight=conf,
            ),
        )
    return None


def rule_scanner(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    path = _path(event)
    scanners = ("nikto", "nmap", "masscan", "sqlmap", "zgrab", "nuclei", "nessus")
    hit = next((t for t in scanners if t in ua), None)
    if hit:
        return RuleMatch(
            rule_id="BS-RULE-SCANNER-001",
            category=BotCategory.SECURITY_SCANNER,
            confidence=0.75,
            evidence=EvidenceItem(
                statement=f"User-Agent matches security scanner ({hit})",
                polarity="for",
                rule_id="BS-RULE-SCANNER-001",
                weight=0.75,
            ),
        )
    suspicious = (
        "/wp-admin",
        "/wp-login",
        "/.env",
        "/phpmyadmin",
        "/actuator",
        "/.git",
    )
    if any(path.startswith(p) for p in suspicious):
        return RuleMatch(
            rule_id="BS-RULE-SCANNER-013",
            category=BotCategory.SECURITY_SCANNER,
            confidence=0.65,
            evidence=EvidenceItem(
                statement="Path matches common probe/scanner target",
                polarity="for",
                rule_id="BS-RULE-SCANNER-013",
                weight=0.65,
            ),
        )
    return None


def rule_generic_bot_ua(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    if not ua:
        return RuleMatch(
            rule_id="BS-RULE-AUTO-001",
            category=BotCategory.UNKNOWN_AUTOMATION,
            confidence=0.35,
            evidence=EvidenceItem(
                statement="Missing User-Agent (common in automation)",
                polarity="for",
                rule_id="BS-RULE-AUTO-001",
                weight=0.35,
            ),
        )
    if re.search(r"\b(bot|crawler|spider|http-client|python-requests|curl|wget)\b", ua):
        return RuleMatch(
            rule_id="BS-RULE-AUTO-002",
            category=BotCategory.UNKNOWN_AUTOMATION,
            confidence=0.5,
            evidence=EvidenceItem(
                statement="User-Agent contains generic automation tokens",
                polarity="for",
                rule_id="BS-RULE-AUTO-002",
                weight=0.5,
            ),
        )
    # Go's default client often appears without "bot" tokens.
    if "go-http-client" in ua:
        return RuleMatch(
            rule_id="BS-RULE-AUTO-003",
            category=BotCategory.UNKNOWN_AUTOMATION,
            confidence=0.52,
            evidence=EvidenceItem(
                statement="User-Agent matches Go net/http default client",
                polarity="for",
                rule_id="BS-RULE-AUTO-003",
                weight=0.52,
            ),
        )
    return None


def rule_human_browser(event: NormalizedEvent) -> RuleMatch | None:
    ua = _ua(event)
    browsers = ("mozilla/", "chrome/", "safari/", "firefox/", "edg/")
    if not any(b in ua for b in browsers):
        return None
    # Avoid matching bot UAs that embed Mozilla compatibility tokens.
    if re.search(r"\b(bot|crawler|spider)\b", ua):
        return None
    return RuleMatch(
        rule_id="BS-RULE-HUMAN-001",
        category=BotCategory.HUMAN_LIKELY,
        confidence=0.45,
        evidence=EvidenceItem(
            statement="User-Agent resembles interactive browser without bot tokens",
            polarity="for",
            rule_id="BS-RULE-HUMAN-001",
            weight=0.45,
        ),
    )


DEFAULT_RULES: list[RuleFn] = [
    rule_search_googlebot,
    rule_search_bingbot,
    rule_search_applebot,
    rule_search_duckduckbot,
    rule_search_yandex,
    rule_ai_gptbot,
    rule_ai_claudebot,
    rule_ai_bytespider,
    rule_ai_ccbot,
    rule_ai_amazonbot,
    rule_ai_meta_external,
    rule_ai_perplexity,
    rule_scraper,
    rule_api_automation,
    rule_social_preview,
    rule_monitoring,
    rule_scanner,
    rule_generic_bot_ua,
    rule_human_browser,
]


class RuleEngine:
    """Apply versioned deterministic rules to a normalized event."""

    def __init__(self, rules: list[RuleFn] | None = None) -> None:
        self.rules = list(rules or DEFAULT_RULES)

    def evaluate(self, event: NormalizedEvent) -> list[RuleMatch]:
        matches: list[RuleMatch] = []
        for rule in self.rules:
            match = rule(event)
            if match is not None:
                matches.append(match)
        return matches
