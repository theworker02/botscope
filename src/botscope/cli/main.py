"""BotScope CLI — Click entrypoint.

Status: IMPLEMENTED (core + live/capture + research wrappers)

Thin dispatcher over Analyzer, Observatory helpers, and research modules.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from botscope.__version__ import __version__

console = Console()


@click.group(invoke_without_command=True)
@click.option(
    "--no-gui",
    is_flag=True,
    help="Do not launch the Observatory when no subcommand is given.",
)
@click.version_option(__version__, prog_name="botscope")
@click.pass_context
def main(ctx: click.Context, no_gui: bool) -> None:
    """BotScope — measure and understand automated Internet traffic.

    Running `botscope` with no subcommand launches the native desktop
    Observatory (Qt). Use a subcommand for CLI workflows, or --no-gui
    to print help without opening a window.
    """
    if ctx.invoked_subcommand is None:
        if no_gui:
            click.echo(ctx.get_help())
            return
        from botscope.gui.app import launch_gui

        launch_gui()


@main.command("doctor")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
@click.option(
    "--bundle",
    type=click.Path(path_type=Path),
    default=None,
    help="Write a sanitized diagnostic zip.",
)
def doctor_cmd(as_json: bool, bundle: Path | None) -> None:
    """Run environment and policy diagnostics."""
    from botscope.diagnostics import doctor_report, write_doctor_bundle

    report = doctor_report()
    if bundle is not None:
        path = write_doctor_bundle(bundle)
        console.print(f"[green]Wrote sanitized bundle:[/green] {path}")
    if as_json:
        console.print_json(data=report)
        return
    table = Table(title=f"BotScope doctor ({report['overall']})")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in report["checks"]:
        table.add_row(check["name"], check["status"], check["detail"])
    console.print(table)


@main.command("demo")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("demo_analysis.bscope"),
    help="Session output directory.",
)
@click.option("--json", "as_json", is_flag=True)
def demo_cmd(output: Path, as_json: bool) -> None:
    """Analyze the bundled synthetic demo corpus (always labeled DEMO)."""
    from botscope.api.analyzer import Analyzer
    from botscope.demo import DEMO_NOTICE, ensure_demo_log

    console.print(f"[yellow]{DEMO_NOTICE}[/yellow]")
    log_path = ensure_demo_log()
    result = Analyzer().analyze(log_path, output=output, is_demo=True)
    payload = {
        "notice": DEMO_NOTICE,
        "events": len(result.events),
        "session_path": str(result.session_path) if result.session_path else None,
        "automation_fraction": result.automation_fraction,
        "human_fraction": result.human_fraction,
        "unknown_fraction": result.unknown_fraction,
        "is_demo": True,
    }
    if as_json:
        console.print_json(data=payload)
    else:
        console.print(payload)


@main.command("analyze")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional .bscope session directory.",
)
@click.option("--demo", is_flag=True, help="Mark analysis as DEMO DATA.")
@click.option("--max-events", type=int, default=None)
@click.option(
    "--query",
    "query_expr",
    default=None,
    help='Filter with shared query language, e.g. classification eq "AI CRAWLER".',
)
@click.option("--json", "as_json", is_flag=True)
@click.option(
    "--no-identity-ranges",
    is_flag=True,
    help="Skip loading published Google/Bing crawler IP ranges for identity checks.",
)
def analyze_cmd(
    source: Path,
    output: Path | None,
    demo: bool,
    max_events: int | None,
    query_expr: str | None,
    as_json: bool,
    no_identity_ranges: bool,
) -> None:
    """Analyze an authorized log file or session input."""
    from botscope.api.analyzer import AnalysisResult, Analyzer
    from botscope.query import QueryError, filter_events, parse_simple_query
    from botscope.statistics.aggregate import aggregate_events

    result = Analyzer(use_identity_ranges=not no_identity_ranges).analyze(
        source, output=output, is_demo=demo, max_events=max_events
    )
    events = result.events
    if query_expr:
        try:
            preds = parse_simple_query(query_expr)
        except QueryError as exc:
            raise click.ClickException(str(exc)) from exc
        events = list(filter_events(events, preds))
        stats = aggregate_events(events, is_demo=result.is_demo)
        result = AnalysisResult(
            events=events,
            stats=stats,
            session_path=result.session_path,
            session_id=result.session_id,
            report=result.report,
            is_demo=result.is_demo,
            identity_ranges=result.identity_ranges,
        )
    payload = {
        "events": len(result.events),
        "session_path": str(result.session_path) if result.session_path else None,
        "automation_fraction": result.automation_fraction,
        "human_fraction": result.human_fraction,
        "unknown_fraction": result.unknown_fraction,
        "is_demo": result.is_demo,
        "query": query_expr,
        "identity_ranges": result.identity_ranges,
    }
    if as_json:
        console.print_json(data=payload)
    else:
        console.print(payload)


@main.command("query")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("expression")
@click.option("--json", "as_json", is_flag=True)
@click.option("--limit", type=int, default=20, show_default=True)
def query_cmd(source: Path, expression: str, as_json: bool, limit: int) -> None:
    """Filter events with the shared safe query language (GUI/CLI/Python)."""
    from botscope.api.analyzer import Analyzer
    from botscope.query import QueryError, filter_events, parse_simple_query
    from botscope.storage.session import SessionStore

    try:
        preds = parse_simple_query(expression)
    except QueryError as exc:
        raise click.ClickException(str(exc)) from exc

    if source.suffix.lower() == ".bscope" or (source / "events.jsonl").exists():
        store = SessionStore(source)
        try:
            events = list(store.iter_events())
        finally:
            store.close()
    else:
        events = Analyzer().analyze(source).events

    matched = list(filter_events(events, preds))
    sample = [
        {
            "event_id": e.event_id,
            "classification": e.classification,
            "confidence": e.confidence,
            "path": e.path,
            "user_agent": e.user_agent,
        }
        for e in matched[: max(limit, 0)]
    ]
    payload = {
        "expression": expression,
        "predicates": [p.to_dict() for p in preds],
        "matched": len(matched),
        "total": len(events),
        "sample": sample,
    }
    if as_json:
        console.print_json(data=payload)
    else:
        console.print(payload)


@main.command("report")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "markdown", "html", "csv"]),
    default="markdown",
)
@click.option("--output", type=click.Path(path_type=Path), required=True)
def report_cmd(session: Path, fmt: str, output: Path) -> None:
    """Export a report from an existing .bscope session."""
    from botscope.reports.generator import (
        export_csv_categories,
        export_html,
        export_json,
        export_markdown,
    )
    from botscope.storage.session import SessionStore

    store = SessionStore(session)
    try:
        report_path = store.report_path
        if not report_path.exists():
            raise click.ClickException("Session has no report.json — run analyze first.")
        report = json.loads(report_path.read_text(encoding="utf-8"))
    finally:
        store.close()
    writers = {
        "json": export_json,
        "markdown": export_markdown,
        "html": export_html,
        "csv": export_csv_categories,
    }
    path = writers[fmt](report, output)
    console.print(f"[green]Wrote report:[/green] {path}")


@main.command("open")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def open_cmd(session: Path, as_json: bool) -> None:
    """Summarize an existing analysis session."""
    from botscope.storage.session import SessionStore

    store = SessionStore(session)
    try:
        sid = store.latest_session_id()
        meta = store.get_session(sid) if sid else None
        events = list(store.iter_events())
        payload = {
            "session_id": sid,
            "events": len(events),
            "classifier_version": meta.classifier_version if meta else None,
            "is_demo": meta.is_demo if meta else None,
            "source_path": meta.source_path if meta else None,
        }
    finally:
        store.close()
    if as_json:
        console.print_json(data=payload)
    else:
        console.print(payload)


@main.command("compare")
@click.argument("left", type=click.Path(exists=True, path_type=Path))
@click.argument("right", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def compare_cmd(left: Path, right: Path, as_json: bool) -> None:
    """Compare two analysis sessions."""
    from botscope.compare import compare_sessions

    result = compare_sessions(left, right)
    data = result.to_dict()
    if as_json:
        console.print_json(data=data)
    else:
        console.print(data)


@main.command("compare-classifiers")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def compare_classifiers_cmd(source: Path, as_json: bool) -> None:
    """Re-classify events and compare against stored labels (or self-agreement)."""
    from botscope.api.analyzer import Analyzer
    from botscope.compare import compare_classifiers
    from botscope.storage.session import SessionStore

    if source.suffix.lower() == ".bscope" or (source / "events.jsonl").exists():
        store = SessionStore(source)
        try:
            events = list(store.iter_events())
        finally:
            store.close()
        result = compare_classifiers(events)
    else:
        analyzed = Analyzer().analyze(source)
        # Compare classifier against itself on freshly labeled events — agreement ~1.0
        result = compare_classifiers(analyzed.events)
    data = result.to_dict()
    if as_json:
        console.print_json(data=data)
    else:
        console.print(data)


@main.command("citation")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["plain", "bibtex", "cff"]),
    default="plain",
)
def citation_cmd(fmt: str) -> None:
    """Print software citation helpers (no invented DOI)."""
    from botscope.research import citation_bibtex, citation_cff_snippet, citation_plain

    if fmt == "plain":
        console.print(citation_plain())
    elif fmt == "bibtex":
        console.print(citation_bibtex())
    else:
        console.print(citation_cff_snippet())


@main.group("plugin")
def plugin_group() -> None:
    """Plugin scaffold and validation."""


@plugin_group.command("create")
@click.argument("dest", type=click.Path(path_type=Path))
@click.option("--name", default="example")
def plugin_create(dest: Path, name: str) -> None:
    from botscope.plugins.sdk import create_plugin_scaffold

    path = create_plugin_scaffold(dest, name=name)
    console.print(f"[green]Created plugin scaffold:[/green] {path}")


@plugin_group.command("validate")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def plugin_validate(path: Path) -> None:
    from botscope.plugins.sdk import validate_plugin_dir

    for issue in validate_plugin_dir(path):
        console.print(f"{issue.severity}: {issue.message}")


@main.command("capture")
@click.option("--json", "as_json", is_flag=True)
@click.option("--list-interfaces", "list_ifaces", is_flag=True)
@click.option("--iface", "interface", default=None, help="Local interface to sniff.")
@click.option("--bpf", default=None, help="Optional BPF filter.")
@click.option("--max-packets", type=int, default=None)
@click.option("--authorize", is_flag=True, help="Required to start live sniff.")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional .bscope to append live events.",
)
def capture_cmd(
    as_json: bool,
    list_ifaces: bool,
    interface: str | None,
    bpf: str | None,
    max_packets: int | None,
    authorize: bool,
    output: Path | None,
) -> None:
    """Capture status, or authorized local-interface sniff."""
    from botscope.capture import live_capture_status
    from botscope.capture.live import LiveCaptureConfig, iter_live_packets
    from botscope.live import LiveSessionWriter, classify_live_event

    status = live_capture_status()
    if interface is None:
        if as_json:
            console.print_json(data=status)
            return
        console.print(f"scapy_available: {status.get('scapy_available')}")
        console.print(f"live_capture: {status.get('live_capture')}")
        console.print(status.get("policy"))
        if list_ifaces or status.get("interfaces"):
            console.print("interfaces:")
            for item in status.get("interfaces") or []:
                console.print(f"  - {item.get('name')}")
        return

    if not authorize:
        raise click.ClickException("Pass --authorize to start local interface capture.")
    config = LiveCaptureConfig(
        interface=interface,
        bpf_filter=bpf,
        max_packets=max_packets,
        authorized=True,
    )
    writer = LiveSessionWriter(output, source_label=f"live:{interface}") if output else None
    if writer:
        writer.open(config={"cli": True, "iface": interface})
    count = 0
    for event in iter_live_packets(config):
        classified = classify_live_event(event, sensor_id=f"iface:{interface}")
        count += 1
        if writer:
            writer.append([classified])
        if not as_json:
            console.print(
                f"{classified.src_address} → {classified.dst_address}:{classified.dst_port} "
                f"[{classified.classification}]"
            )
    if writer:
        writer.close()
    payload = {"events": count, "interface": interface, "output": str(output) if output else None}
    if as_json:
        console.print_json(data=payload)
    else:
        console.print(f"[green]Captured {count} packets[/green]")


@main.command("live-tail")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--authorize", is_flag=True, required=True)
@click.option("--max-lines", type=int, default=100)
@click.option("--output", type=click.Path(path_type=Path), default=None)
@click.option("--json", "as_json", is_flag=True)
def live_tail_cmd(
    path: Path,
    authorize: bool,
    max_lines: int,
    output: Path | None,
    as_json: bool,
) -> None:
    """Authorized headless log tail (finite sample for CLI)."""
    from botscope.ingest.parsers import CombinedLogParser, JsonLogParser, detect_parser
    from botscope.live import LiveSessionWriter, LogTailConfig, classify_live_event, tail_new_lines

    if not authorize:
        raise click.ClickException("--authorize is required")
    parser = detect_parser(path) or CombinedLogParser()
    writer = LiveSessionWriter(output, source_label=str(path)) if output else None
    if writer:
        writer.open(config={"cli": True})
    config = LogTailConfig(path=path, poll_interval_s=0.05, start_at_end=False)
    events = []
    for i, line in enumerate(tail_new_lines(config, stop_after=2.0)):
        if i >= max_lines:
            break
        if line.strip().startswith("{"):
            event = JsonLogParser().parse_line(line, line_no=i + 1)
        else:
            event = parser.parse_line(line, line_no=i + 1)
        if event is None:
            continue
        classified = classify_live_event(event, sensor_id=f"log:{path.name}")
        events.append(classified)
        if writer:
            writer.append([classified])
    if writer:
        writer.close()
    payload = {
        "events": len(events),
        "path": str(path),
        "output": str(output) if output else None,
        "categories": {},
    }
    for e in events:
        key = e.classification or "UNCLASSIFIED"
        payload["categories"][key] = payload["categories"].get(key, 0) + 1
    if as_json:
        console.print_json(data=payload)
    else:
        console.print(f"[green]Tailed {len(events)} events[/green] from {path}")


def _load_session_events(session: Path):
    from botscope.storage.session import SessionStore

    store = SessionStore(session)
    events = list(store.iter_events())
    store.close()
    return events


@main.command("geo")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def geo_cmd(session: Path, as_json: bool) -> None:
    """Aggregate coarse geo tags from a .bscope session."""
    from botscope.geo import aggregate_geo

    agg = aggregate_geo(_load_session_events(session))
    if as_json:
        console.print_json(data=agg.to_dict())
        return
    console.print(agg.caveat)
    for cc, n in agg.by_country.items():
        console.print(f"{cc}: {n}")
    console.print(f"tagged={agg.tagged_events} untagged={agg.untagged_events}")


@main.command("asn-lookup")
@click.argument("address")
@click.option(
    "--table",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Offline ASN table (CSV/JSON). Defaults to BOTSCOPE_ASN_TABLE.",
)
@click.option("--json", "as_json", is_flag=True)
def asn_lookup_cmd(address: str, table: Path | None, as_json: bool) -> None:
    """Lookup an IP in an offline ASN table."""
    import os

    from botscope.asn import load_asn_table

    path = table or os.environ.get("BOTSCOPE_ASN_TABLE")
    asn_table = load_asn_table(path)
    record = asn_table.lookup_ip(address)
    payload = record.to_dict() if record else {"match": None, "address": address}
    if as_json:
        console.print_json(data=payload)
        return
    if record is None:
        console.print(f"No match for {address} (table size={len(asn_table)})")
    else:
        console.print(f"AS{record.asn} {record.name} {record.prefix} {record.country}")


@main.command("flows")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
@click.option("--limit", type=int, default=20)
def flows_cmd(source: Path, as_json: bool, limit: int) -> None:
    """Aggregate flows from a log/PCAP or .bscope."""
    from botscope.api.analyzer import Analyzer
    from botscope.flows import aggregate_flows

    if source.suffix.lower() == ".bscope" or (source.is_dir() and (source / "events.jsonl").exists()):
        events = _load_session_events(source)
    else:
        events = Analyzer(use_identity_ranges=False).analyze(source).events
    flows = [f.to_dict() for f in aggregate_flows(events)[:limit]]
    if as_json:
        console.print_json(data={"flows": flows})
        return
    for row in flows:
        console.print(
            f"{row['src_address']} → {row['dst_address']}:{row['dst_port']} "
            f"n={row['events']} class={row.get('majority_classification')}"
        )


@main.command("behavior")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
@click.option("--limit", type=int, default=20)
def behavior_cmd(source: Path, as_json: bool, limit: int) -> None:
    """Per-source behavior profiles."""
    from botscope.api.analyzer import Analyzer
    from botscope.behavior import profile_by_source

    if source.suffix.lower() == ".bscope" or (source.is_dir() and (source / "events.jsonl").exists()):
        events = _load_session_events(source)
    else:
        events = Analyzer(use_identity_ranges=False).analyze(source).events
    profiles = [p.to_dict() for p in profile_by_source(events)[:limit]]
    if as_json:
        console.print_json(data={"behavior": profiles, "status": "IMPLEMENTED"})
        return
    for row in profiles:
        console.print(
            f"{row['src_address']}: events={row['event_count']} "
            f"burst={row['burstiness']} bot_like={row.get('bot_like_score')} "
            f"class={row.get('majority_classification')}"
        )


@main.command("estimate-local")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def estimate_local_cmd(session: Path, as_json: bool) -> None:
    """Local share estimate for a session (refuses Internet-wide claims)."""
    from botscope.estimation import local_share_estimate
    from botscope.statistics.aggregate import aggregate_events

    events = _load_session_events(session)
    stats = aggregate_events(events)
    est = local_share_estimate(
        stats.automation_fraction("requests"),
        stats.human_fraction("requests"),
        stats.unknown_fraction("requests"),
        population=f"session:{session}",
    )
    if as_json:
        console.print_json(data=est.to_dict())
        return
    console.print(est.caveat)
    console.print(f"automated={est.automated} human={est.human_likely} unknown={est.unknown}")


@main.command("federation")
@click.option("--json", "as_json", is_flag=True)
def federation_cmd(as_json: bool) -> None:
    """Collect Global Observatory federation snapshot (zero-auth sources)."""
    from botscope.estimation.internet import estimate_from_federation
    from botscope.sources.federation import SourceFederation

    fed = SourceFederation()
    snap = fed.collect()
    est = estimate_from_federation(snap)
    payload = {
        "observations": len(snap.observations),
        "errors": snap.errors,
        "estimate": est.to_dict(),
        "raw": snap.raw_source_table(),
    }
    if as_json:
        console.print_json(data=payload)
        return
    console.print(f"release_gate: {est.release_gate}")
    console.print(f"sources: {', '.join(est.sources) or '(none)'}")
    console.print(est.methodology)


@main.command("eval")
@click.argument("labels", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def eval_cmd(labels: Path, as_json: bool) -> None:
    """Evaluate classifier against a labeled JSONL fixture."""
    import json as json_mod

    from botscope.api.analyzer import Analyzer
    from botscope.eval import evaluate_labels
    from botscope.normalize.event import NormalizedEvent, SourceType

    y_true: list[str] = []
    y_pred: list[str] = []
    analyzer = Analyzer(use_identity_ranges=False)
    for line in labels.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json_mod.loads(line)
        label = row.get("label") or row.get("classification")
        event = NormalizedEvent(
            event_id=str(row.get("event_id") or "fx"),
            source_type=SourceType(row.get("source_type") or SourceType.WEB_LOG.value),
            user_agent=row.get("user_agent"),
            path=row.get("path"),
            status=row.get("status"),
            src_address=row.get("src_address"),
        )
        result = analyzer.classify_event(event)
        y_true.append(str(label))
        y_pred.append(result.category.value)
    report = evaluate_labels(y_true, y_pred)
    if as_json:
        console.print_json(data=report.to_dict())
        return
    console.print(
        f"n={report.n} accuracy={report.accuracy:.3f} "
        f"macro_f1={report.macro_f1:.3f} micro_f1={report.micro_f1:.3f}"
    )


@main.command("export")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("export_out"),
)
@click.option("--formats", default="json,markdown,html,csv")
def export_cmd(session: Path, output_dir: Path, formats: str) -> None:
    """Export a .bscope session via ExportJob."""
    import json as json_mod

    from botscope.export import ExportJob
    from botscope.reports.generator import build_report
    from botscope.statistics.aggregate import aggregate_events
    from botscope.storage.session import SessionStore

    store = SessionStore(session)
    events = list(store.iter_events())
    report_path = store.report_path
    if report_path.exists():
        report = json_mod.loads(report_path.read_text(encoding="utf-8"))
    else:
        report = build_report(aggregate_events(events), events=events)
    store.close()
    job = ExportJob(
        output_dir=output_dir,
        formats=[f.strip() for f in formats.split(",") if f.strip()],
    )
    arts = job.run(report)
    for a in arts:
        console.print(f"[green]{a.format}[/green] → {a.path}")


@main.command("quality")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def quality_cmd(session: Path, as_json: bool) -> None:
    """Quality scorecard for a session."""
    from botscope.quality import build_scorecard

    card = build_scorecard(_load_session_events(session))
    payload = card.to_dict()
    if as_json:
        console.print_json(data=payload)
        return
    console.print_json(data=payload)


@main.command("provenance")
@click.argument("session", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True)
def provenance_cmd(session: Path, as_json: bool) -> None:
    """Provenance summary for a session."""
    from botscope.provenance import summarize_corpus

    summary = summarize_corpus(_load_session_events(session))
    payload = summary.to_dict()
    if as_json:
        console.print_json(data=payload)
        return
    console.print_json(data=payload)


@main.command("notebook")
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--from-session", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--filter", "filt", default=None, help="Optional query expression.")
def notebook_cmd(output: Path, from_session: Path | None, filt: str | None) -> None:
    """Create an experimental analysis notebook JSON."""
    from botscope.notebook import AnalysisNotebook

    nb = AnalysisNotebook(title="BotScope CLI Notebook")
    if from_session:
        events = _load_session_events(from_session)
        nb.add_markdown("Source", f"Session: {from_session}")
        nb.add_event_stats("Event stats", events)
        if filt:
            nb.add_filter("Filter", events, filt)
    else:
        nb.add_markdown("Empty", "No session provided — scaffold only.")
    path = nb.save(output)
    console.print(f"[green]Wrote notebook:[/green] {path}")


@main.command("datasets")
@click.option("--json", "as_json", is_flag=True)
def datasets_cmd(as_json: bool) -> None:
    """List bundled demo/fixture datasets."""
    from botscope.datasets import fixtures_root, list_demo_datasets, load_labeled_mini

    payload = {
        "demo": list_demo_datasets(),
        "fixtures_root": str(fixtures_root()),
        "labeled_mini_rows": len(load_labeled_mini()),
    }
    if as_json:
        console.print_json(data=payload)
        return
    console.print_json(data=payload)


@main.command("history")
@click.option("--json", "as_json", is_flag=True)
def history_cmd(as_json: bool) -> None:
    """List local session history MRU."""
    from botscope.history import SessionHistory

    hist = SessionHistory().load()
    items = [e.to_dict() for e in hist.entries]
    if as_json:
        console.print_json(data={"history": items})
        return
    if not items:
        console.print("No recent sessions.")
        return
    for item in items:
        console.print(f"{item.get('opened_at')}  {item.get('path')}")


@main.command("enrich-status")
@click.option("--json", "as_json", is_flag=True)
def enrich_status_cmd(as_json: bool) -> None:
    """Show enrichment capability status."""
    from botscope.enrich import enrichment_status

    st = enrichment_status()
    if as_json:
        console.print_json(data=st)
        return
    console.print_json(data=st)


@main.command("gui")
@click.option("--no-welcome", is_flag=True, help="Skip the first-run welcome dialog.")
def gui_cmd(no_welcome: bool) -> None:
    """Launch the native desktop Observatory (Qt/PySide6 — not a website)."""
    from botscope.gui.app import launch_gui

    launch_gui(show_welcome=not no_welcome)


@main.command("quickstart")
def quickstart_cmd() -> None:
    """Print the fastest path from install to a first measurement."""
    console.print(
        """
[bold]BotScope quickstart[/bold]

  1. Install GUI extras:
       [cyan]pip install 'botscope[gui]'[/cyan]

  2. Launch Observatory (native desktop):
       [cyan]botscope[/cyan]
       or [cyan]botscope gui --no-welcome[/cyan]

  3. Or analyze from the CLI:
       [cyan]botscope demo[/cyan]
       [cyan]botscope analyze path/to/access.log --output run.bscope[/cyan]
       [cyan]botscope batch logs/*.log --output-dir batch_out[/cyan]

  4. Drag a log, PCAP, or .bscope folder onto the Observatory window.

Tips: Settings → theme / privacy stay local. Network contribution defaults OFF.
""".strip()
    )


@main.command("batch")
@click.argument("sources", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("batch_out"),
    show_default=True,
    help="Directory for per-source .bscope sessions.",
)
@click.option("--max-events", type=int, default=None)
@click.option("--json", "as_json", is_flag=True)
@click.option(
    "--no-identity-ranges",
    is_flag=True,
    help="Skip loading published Google/Bing crawler IP ranges.",
)
def batch_cmd(
    sources: tuple[Path, ...],
    output_dir: Path,
    max_events: int | None,
    as_json: bool,
    no_identity_ranges: bool,
) -> None:
    """Analyze multiple logs/PCAPs into separate .bscope sessions."""
    from botscope.api.analyzer import Analyzer

    output_dir.mkdir(parents=True, exist_ok=True)
    analyzer = Analyzer(use_identity_ranges=not no_identity_ranges)
    results: list[dict] = []
    for source in sources:
        stem = source.stem if source.is_file() else source.name
        out = output_dir / f"{stem}.bscope"
        try:
            result = analyzer.analyze(source, output=out, max_events=max_events)
            row = {
                "source": str(source),
                "session_path": str(result.session_path) if result.session_path else str(out),
                "events": len(result.events),
                "automation_fraction": result.automation_fraction,
                "identity_ranges_prefixes": result.identity_ranges.get("prefix_count"),
                "ok": True,
            }
        except Exception as exc:
            row = {"source": str(source), "ok": False, "error": str(exc)}
        results.append(row)
        if not as_json:
            if row.get("ok"):
                console.print(
                    f"[green]OK[/green] {source.name}: {row['events']:,} events → {row['session_path']}"
                )
            else:
                console.print(f"[red]FAIL[/red] {source}: {row.get('error')}")
    if as_json:
        console.print_json(data={"results": results})
    failed = sum(1 for r in results if not r.get("ok"))
    if failed:
        raise SystemExit(1)


@main.command("features")
@click.option("--json", "as_json", is_flag=True)
def features_cmd(as_json: bool) -> None:
    """List the capability registry."""
    from botscope.capabilities import features_matrix

    matrix = features_matrix()
    if as_json:
        console.print_json(data=matrix)
        return
    table = Table(title="BotScope features")
    table.add_column("id")
    table.add_column("status")
    table.add_column("module")
    table.add_column("summary")
    for row in matrix:
        table.add_row(row["id"], row["status"], row["module"], row["summary"])
    console.print(table)


if __name__ == "__main__":
    main()
