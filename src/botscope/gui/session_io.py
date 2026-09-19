"""Save / load ``.bscope`` sessions from the Observatory GUI.

Status: IMPLEMENTED

Wraps SessionStore + workspace + history without breaking Agent 1 schema.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from botscope.api.analyzer import AnalysisResult
from botscope.classify.result import MODEL_VERSION, RULESET_VERSION
from botscope.__version__ import __version__
from botscope.history import SessionHistory
from botscope.native import native_status
from botscope.normalize.event import NormalizedEvent
from botscope.reports.generator import build_report
from botscope.signatures.store import SignatureStore
from botscope.statistics.aggregate import aggregate_events
from botscope.storage.session import SessionMeta, SessionStore
from botscope.workspace import AnalysisWorkspace, load_workspace, save_workspace


@dataclass
class LoadedSession:
    path: Path
    result: AnalysisResult
    meta: SessionMeta | None
    workspace: AnalysisWorkspace
    session_id: str | None


def _file_hash(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_analysis_session(
    target: str | Path,
    events: list[NormalizedEvent],
    *,
    source_path: Path | None = None,
    is_demo: bool = False,
    workspace: AnalysisWorkspace | None = None,
    classifier_version: str | None = None,
    ruleset_version: str | None = None,
    signature_version: str | None = None,
    remember: bool = True,
) -> LoadedSession:
    """Persist events + aggregates + workspace into a ``.bscope`` directory."""
    target = Path(target)
    if target.suffix.lower() != ".bscope":
        # Allow bare folder names; normalize to .bscope suffix convention.
        if not target.name.endswith(".bscope"):
            target = target.with_name(target.name + ".bscope")

    stats = aggregate_events(events, is_demo=is_demo)
    report = build_report(stats, events=events, is_demo=is_demo)
    sig_ver = signature_version
    if sig_ver is None:
        try:
            sig_ver = SignatureStore.load_bundled().VERSION
        except Exception:  # noqa: BLE001
            sig_ver = None

    store = SessionStore(target)
    try:
        backend = native_status()
        session_id = store.create_session(
            source_path=str(source_path) if source_path else None,
            source_hash=_file_hash(source_path) if source_path and source_path.is_file() else None,
            classifier_version=classifier_version or MODEL_VERSION,
            ruleset_version=ruleset_version or RULESET_VERSION,
            signature_version=sig_ver,
            native_backend=backend.get("backend"),
            is_demo=is_demo,
            config={
                "botscope_version": __version__,
                "saved_from": "observatory_gui",
            },
        )
        store.replace_events(events)
        for key, value in stats.to_dict().items():
            store.set_aggregate(session_id, key, value, stats.provenance.value)
        store.write_report(report)

        ws = workspace or AnalysisWorkspace()
        save_workspace(store.root, ws)
        store.merge_session_config(session_id, {"workspace_schema": ws.schema_version})
        meta = store.get_session(session_id)
    finally:
        store.close()

    result = AnalysisResult(
        events=list(events),
        stats=stats,
        session_path=target,
        session_id=session_id,
        report=report,
        is_demo=is_demo,
    )
    if remember:
        SessionHistory().load().remember(
            target,
            label=target.name,
            event_count=len(events),
            is_demo=is_demo,
            classifier_version=classifier_version or MODEL_VERSION,
            source_path=str(source_path) if source_path else None,
        )
    return LoadedSession(
        path=target,
        result=result,
        meta=meta,
        workspace=ws,
        session_id=session_id,
    )


def load_analysis_session(path: str | Path, *, remember: bool = True) -> LoadedSession:
    """Load events + metadata + workspace from a ``.bscope`` directory."""
    path = Path(path)
    store = SessionStore(path)
    try:
        events = list(store.iter_events())
        sid = store.latest_session_id()
        meta = store.get_session(sid) if sid else None
        is_demo = bool(meta.is_demo) if meta else False
        stats = aggregate_events(events, is_demo=is_demo)
        report = {}
        if store.report_path.exists():
            import json

            report = json.loads(store.report_path.read_text(encoding="utf-8"))
        else:
            report = build_report(stats, events=events, is_demo=is_demo)
        workspace = load_workspace(store.root)
    finally:
        store.close()

    if not events:
        raise ValueError("No events found in session.")

    result = AnalysisResult(
        events=events,
        stats=stats,
        session_path=path,
        session_id=sid,
        report=report,
        is_demo=is_demo,
    )
    if remember:
        SessionHistory().load().remember(
            path,
            label=path.name,
            event_count=len(events),
            is_demo=is_demo,
            classifier_version=meta.classifier_version if meta else None,
            source_path=meta.source_path if meta else None,
        )
    return LoadedSession(
        path=path,
        result=result,
        meta=meta,
        workspace=workspace,
        session_id=sid,
    )


def suggest_session_name(source_path: Path | None, *, is_demo: bool) -> str:
    if is_demo:
        return "demo_analysis.bscope"
    if source_path is None:
        return "analysis.bscope"
    stem = source_path.stem or "analysis"
    return f"{stem}.bscope"
