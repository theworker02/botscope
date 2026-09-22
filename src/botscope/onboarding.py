"""First-run onboarding and ease-of-access helpers.

Status: IMPLEMENTED — offline-first; no network, GUI, or API keys required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from botscope.demo import DEMO_NOTICE

# Friendly next steps shown after `botscope hello`.
HELLO_NEXT_STEPS: tuple[str, ...] = (
    "Open the desktop Observatory: botscope gui",
    "Re-run the labeled demo session: botscope demo --output demo_analysis.bscope",
    "Analyze an authorized log: botscope analyze path/to/access.log --output run.bscope",
    "Check the environment: botscope doctor",
    "Print the full access checklist: botscope access",
)


def format_fraction(value: float | None, *, digits: int = 1) -> str:
    """Render a 0–1 fraction as a percentage string, or 'n/a'."""
    if value is None:
        return "n/a"
    return f"{100.0 * value:.{digits}f}%"


def _escape_rich(text: str) -> str:
    """Escape square brackets so Rich does not treat pip extras as markup tags."""
    return text.replace("[", "\\[")


def top_categories(
    by_category: dict[str, int],
    *,
    limit: int = 5,
) -> list[tuple[str, int]]:
    """Return the top categories by event count (descending)."""
    items = sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[: max(0, limit)]


def data_locations() -> dict[str, str]:
    """Describe where BotScope keeps local state (no uploads by default)."""
    from platformdirs import user_cache_dir, user_config_dir

    from botscope.ux.recents import settings_path

    return {
        "config": str(Path(user_config_dir("botscope", "botscope"))),
        "cache": str(Path(user_cache_dir("botscope", "botscope"))),
        "ux_settings": str(settings_path()),
        "sessions": (
            "Wherever you choose — .bscope session folders are written to the "
            "--output / --keep-session path you pass (local disk only)."
        ),
    }


def run_hello_analysis(*, keep_session: Path | None = None) -> dict[str, Any]:
    """Run the bundled demo corpus end-to-end offline and return a summary dict.

    Uses ``use_identity_ranges=False`` so no network fetch is attempted.
    No GUI and no API keys are required.
    """
    from botscope.api.analyzer import Analyzer
    from botscope.demo import ensure_demo_log

    log_path = ensure_demo_log()
    result = Analyzer(use_identity_ranges=False).analyze(
        log_path,
        output=keep_session,
        is_demo=True,
    )
    by_category = dict(result.stats.by_category)
    tops = top_categories(by_category, limit=5)
    return {
        "notice": DEMO_NOTICE,
        "is_demo": True,
        "offline": True,
        "events": len(result.events),
        "automation_fraction": result.automation_fraction,
        "human_fraction": result.human_fraction,
        "unknown_fraction": result.unknown_fraction,
        "top_categories": [{"category": cat, "count": count} for cat, count in tops],
        "by_category": by_category,
        "session_path": str(result.session_path) if result.session_path else None,
        "next_steps": list(HELLO_NEXT_STEPS),
    }


def format_hello_summary(summary: dict[str, Any]) -> str:
    """Pretty multi-line summary for the terminal (Rich markup allowed)."""
    auto = format_fraction(summary.get("automation_fraction"))
    human = format_fraction(summary.get("human_fraction"))
    unknown = format_fraction(summary.get("unknown_fraction"))
    lines = [
        "[bold]BotScope hello[/bold] — offline demo analysis complete",
        "",
        f"[yellow]{summary.get('notice', DEMO_NOTICE)}[/yellow]",
        "",
        f"  Events analyzed:     [cyan]{summary.get('events', 0):,}[/cyan]",
        f"  Automation fraction: [cyan]{auto}[/cyan]",
        f"  Human-likely:        [cyan]{human}[/cyan]",
        f"  Unknown:             [cyan]{unknown}[/cyan]",
        "",
        "  Top categories:",
    ]
    tops = summary.get("top_categories") or []
    if not tops:
        lines.append("    (none)")
    else:
        for row in tops:
            cat = row.get("category", "?")
            count = row.get("count", 0)
            lines.append(f"    • {cat}: {count:,}")
    session = summary.get("session_path")
    if session:
        lines.extend(["", f"  Session saved: [green]{session}[/green]"])
    lines.extend(["", "  Next steps:"])
    for step in summary.get("next_steps") or HELLO_NEXT_STEPS:
        lines.append(f"    → {step}")
    lines.append("")
    lines.append(
        "[dim]Network contribution stays OFF by default. "
        "Demo shares are synthetic — not Internet-wide census metrics.[/dim]"
    )
    return "\n".join(lines)


def access_checklist() -> list[dict[str, str]]:
    """Structured ease-of-access checklist items."""
    locs = data_locations()
    return [
        {
            "id": "install_core",
            "title": "Install (CLI / library)",
            "detail": "pip install botscope",
        },
        {
            "id": "install_gui",
            "title": "Install with desktop Observatory",
            "detail": "pip install 'botscope[gui]'",
        },
        {
            "id": "install_all",
            "title": "Install all optional extras",
            "detail": "pip install 'botscope[all]'",
        },
        {
            "id": "zero_config",
            "title": "Zero-config local analysis",
            "detail": (
                "No account, no cloud profile, and no API key required to classify "
                "authorized logs offline."
            ),
        },
        {
            "id": "hello",
            "title": "First result in one command",
            "detail": "botscope hello   # offline demo; optional --json / --keep-session PATH",
        },
        {
            "id": "data_locations",
            "title": "Where data lives",
            "detail": (
                f"Config: {locs['config']} · Cache: {locs['cache']} · "
                f"UX settings: {locs['ux_settings']} · Sessions: {locs['sessions']}"
            ),
        },
        {
            "id": "open_gui",
            "title": "Open the GUI",
            "detail": "botscope gui   # or: botscope   (native Qt Observatory, not a website)",
        },
        {
            "id": "disable_network",
            "title": "Keep / force network off",
            "detail": (
                "Contribution defaults OFF (botscope/network.json enabled=false). "
                "Skip the [network] extra; set BOTSCOPE_NO_IDENTITY_RANGES=1 to skip "
                "published crawler-range fetches; leave Cloudflare Radar token empty."
            ),
        },
        {
            "id": "privacy_defaults",
            "title": "Privacy defaults",
            "detail": (
                "Query redaction ON; IP hashing/truncation OFF until you enable them "
                "in Settings. Analysis stays on your machine."
            ),
        },
        {
            "id": "doctor",
            "title": "Environment check",
            "detail": "botscope doctor   # optional: --json or --bundle PATH",
        },
        {
            "id": "docs",
            "title": "First-hour guide",
            "detail": "docs/guides/EASE_OF_ACCESS.md · botscope quickstart",
        },
    ]


def format_access_checklist() -> str:
    """Rich multi-line access checklist for the terminal."""
    lines = [
        "[bold]BotScope — ease of access checklist[/bold]",
        "",
        "Zero-friction path: install → [cyan]botscope hello[/cyan] → optional GUI.",
        "Network contribution is [green]OFF by default[/green]. No fabricated census metrics.",
        "",
    ]
    for i, item in enumerate(access_checklist(), start=1):
        lines.append(f"  [bold]{i}. {_escape_rich(item['title'])}[/bold]")
        lines.append(f"     {_escape_rich(item['detail'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def quickstart_guide() -> str:
    """Rich multi-line quickstart covering install through Global Observatory."""
    return """
[bold]BotScope quickstart[/bold]

  [bold]1. Install paths[/bold]
       Core CLI:     [cyan]pip install botscope[/cyan]
       With GUI:     [cyan]pip install 'botscope\\[gui]'[/cyan]
       All extras:   [cyan]pip install 'botscope\\[all]'[/cyan]
       From source:  [cyan]pip install -e '.\\[gui,dev]'[/cyan]

  [bold]2. Hello (fastest first result — offline)[/bold]
       [cyan]botscope hello[/cyan]
       [cyan]botscope hello --json[/cyan]
       [cyan]botscope hello --keep-session hello.bscope[/cyan]

  [bold]3. Demo session + report[/bold]
       [cyan]botscope demo --output demo_analysis.bscope[/cyan]
       [cyan]botscope open demo_analysis.bscope[/cyan]
       [cyan]botscope report demo_analysis.bscope --format markdown --output report.md[/cyan]

  [bold]4. Analyze your authorized log[/bold]
       [cyan]botscope analyze path/to/access.log --output run.bscope[/cyan]
       [cyan]botscope batch logs/*.log --output-dir batch_out[/cyan]

  [bold]5. Desktop Observatory (native Qt — not a website)[/bold]
       [cyan]botscope[/cyan]
       or [cyan]botscope gui[/cyan]
       Drag a log, PCAP, or .bscope folder onto the window.

  [bold]6. Doctor[/bold]
       [cyan]botscope doctor[/cyan]

  [bold]7. Global Observatory[/bold]
       In the GUI: open the [cyan]Global[/cyan] page (zero-auth public panels).
       CLI snapshot: [cyan]botscope federation[/cyan]
       Cloudflare Radar CDN estimates need an optional token in Settings — never required.

  [bold]8. Privacy defaults[/bold]
       Network contribution: OFF · analysis local · query redaction ON by default.
       Ease-of-access checklist: [cyan]botscope access[/cyan]
       Guide: docs/guides/EASE_OF_ACCESS.md

Tips: Settings → theme / privacy stay local. Demo shares are synthetic, not census metrics.
""".strip()
