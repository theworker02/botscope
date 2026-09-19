"""CLI coverage for new research / live wrappers."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from botscope.cli.main import main


def test_cli_flows_behavior_geo(tmp_path: Path) -> None:
    from botscope.demo import ensure_demo_log

    runner = CliRunner()
    log = ensure_demo_log()
    out = tmp_path / "s.bscope"
    r = runner.invoke(main, ["analyze", str(log), "--output", str(out), "--json"])
    assert r.exit_code == 0, r.output

    for cmd in ("flows", "behavior", "geo", "estimate-local", "quality", "provenance"):
        rr = runner.invoke(main, [cmd, str(out), "--json"])
        assert rr.exit_code == 0, f"{cmd}: {rr.output}"


def test_cli_asn_lookup() -> None:
    runner = CliRunner()
    table = Path("datasets/fixtures/asn_sample.json")
    r = runner.invoke(main, ["asn-lookup", "8.8.8.8", "--table", str(table), "--json"])
    assert r.exit_code == 0, r.output
    assert "15169" in r.output or "GOOGLE" in r.output


def test_cli_eval_and_datasets() -> None:
    runner = CliRunner()
    labels = Path("datasets/fixtures/labeled_mini.jsonl")
    r = runner.invoke(main, ["eval", str(labels), "--json"])
    assert r.exit_code == 0, r.output
    assert "accuracy" in r.output
    r2 = runner.invoke(main, ["datasets", "--json"])
    assert r2.exit_code == 0
    r3 = runner.invoke(main, ["enrich-status", "--json"])
    assert r3.exit_code == 0
    assert "PARTIAL" in r3.output


def test_cli_notebook(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "nb.json"
    r = runner.invoke(main, ["notebook", str(out)])
    assert r.exit_code == 0, r.output
    assert out.exists()


def test_cli_live_tail(tmp_path: Path) -> None:
    from botscope.demo import ensure_demo_log

    runner = CliRunner()
    log = ensure_demo_log()
    out = tmp_path / "live.bscope"
    r = runner.invoke(
        main,
        ["live-tail", str(log), "--authorize", "--max-lines", "5", "--output", str(out), "--json"],
    )
    assert r.exit_code == 0, r.output
    assert "events" in r.output
