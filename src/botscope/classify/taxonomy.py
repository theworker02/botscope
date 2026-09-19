"""Bot traffic taxonomy. UNKNOWN is a first-class, valid result."""

from __future__ import annotations

from enum import Enum


class BotCategory(str, Enum):
    HUMAN_LIKELY = "HUMAN-LIKELY"
    VERIFIED_SEARCH_CRAWLER = "VERIFIED SEARCH CRAWLER"
    AI_CRAWLER = "AI CRAWLER"
    MONITORING_HEALTH_CHECK = "MONITORING / HEALTH CHECK"
    API_AUTOMATION = "API AUTOMATION"
    SOCIAL_PREVIEW_BOT = "SOCIAL / PREVIEW BOT"
    SECURITY_SCANNER = "SECURITY SCANNER"
    SCRAPER = "SCRAPER"
    MALICIOUS_AUTOMATION = "MALICIOUS AUTOMATION"
    UNKNOWN_AUTOMATION = "UNKNOWN AUTOMATION"
    UNKNOWN = "UNKNOWN"

    @property
    def is_automated(self) -> bool:
        return self not in {BotCategory.HUMAN_LIKELY, BotCategory.UNKNOWN}

    @property
    def is_human_likely(self) -> bool:
        return self is BotCategory.HUMAN_LIKELY


AUTOMATION_CATEGORIES = frozenset(
    {
        BotCategory.VERIFIED_SEARCH_CRAWLER,
        BotCategory.AI_CRAWLER,
        BotCategory.MONITORING_HEALTH_CHECK,
        BotCategory.API_AUTOMATION,
        BotCategory.SOCIAL_PREVIEW_BOT,
        BotCategory.SECURITY_SCANNER,
        BotCategory.SCRAPER,
        BotCategory.MALICIOUS_AUTOMATION,
        BotCategory.UNKNOWN_AUTOMATION,
    }
)
