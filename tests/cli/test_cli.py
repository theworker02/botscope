"""CLI smoke tests."""

from __future__ import annotations

from click.testing import CliRunner

from botscope.cli.main import main


def test_cli_doctor_and_citation():
    runner = CliRunner()
    r = runner.invoke(main, ["doctor", "--json"])
    assert r.exit_code == 0, r.output
    assert "botscope_version" in r.output or "overall" in r.output
    r2 = runner.invoke(main, ["citation", "--format", "plain"])
    assert r2.exit_code == 0
    assert "BotScope" in r2.output


def test_cli_demo(tmp_path):
    runner = CliRunner()
    out = tmp_path / "demo.bscope"
    r = runner.invoke(main, ["demo", "--output", str(out), "--json"])
    assert r.exit_code == 0, r.output
    assert "DEMO" in r.output or "is_demo" in r.output


def test_cli_query_help():
    runner = CliRunner()
    r = runner.invoke(main, ["query", "--help"])
    assert r.exit_code == 0
    assert "expression" in r.output.lower() or "query" in r.output.lower()


def test_cli_quickstart():
    runner = CliRunner()
    r = runner.invoke(main, ["quickstart"])
    assert r.exit_code == 0, r.output
    assert "botscope hello" in r.output
    assert "botscope demo" in r.output
    assert "batch" in r.output.lower() or "analyze" in r.output.lower()
    assert "doctor" in r.output.lower()
    assert "privacy" in r.output.lower()


def test_cli_hello(tmp_path):
    runner = CliRunner()
    out = tmp_path / "hello.bscope"
    r = runner.invoke(main, ["hello", "--keep-session", str(out), "--json"])
    assert r.exit_code == 0, r.output
    assert "is_demo" in r.output
    assert "events" in r.output
    assert "top_categories" in r.output
    r2 = runner.invoke(main, ["hello"])
    assert r2.exit_code == 0, r2.output
    assert "BotScope hello" in r2.output or "Events analyzed" in r2.output


def test_cli_access():
    runner = CliRunner()
    r = runner.invoke(main, ["access"])
    assert r.exit_code == 0, r.output
    assert "ease of access" in r.output.lower() or "checklist" in r.output.lower()
    assert "botscope hello" in r.output
    r2 = runner.invoke(main, ["access", "--json"])
    assert r2.exit_code == 0, r2.output
    assert "checklist" in r2.output


def test_cli_batch(tmp_path):
    from botscope.demo import ensure_demo_log

    runner = CliRunner()
    log = ensure_demo_log()
    out = tmp_path / "batch_out"
    r = runner.invoke(
        main,
        ["batch", str(log), "--output-dir", str(out), "--json"],
    )
    assert r.exit_code == 0, r.output
    assert "results" in r.output
    assert out.exists()
    sessions = list(out.glob("*.bscope"))
    assert sessions
