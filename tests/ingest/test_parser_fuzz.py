"""Fuzz-ish robustness tests for access-log parsers.

Feeds malformed / adversarial lines; parsers must not crash and must not
invent events from garbage.
"""

from __future__ import annotations

from botscope.ingest.parsers import CombinedLogParser, JsonLogParser


def test_combined_parser_rejects_garbage() -> None:
    parser = CombinedLogParser()
    garbage = [
        "",
        "# comment",
        "not a log line",
        "1.2.3.4 - - [bad] \"GET / HTTP/1.1\" 200",
        "\x00\x01\x02",
        "A" * 10000,
        '{"looks":"like json but combined parser"}',
    ]
    for line in garbage:
        assert parser.parse_line(line) is None


def test_json_parser_rejects_garbage() -> None:
    parser = JsonLogParser()
    garbage = [
        "",
        "not-json",
        "{",
        "[]",
        "null",
        '"string"',
        "{" + ("x" * 5000),
    ]
    for line in garbage:
        assert parser.parse_line(line) is None


def test_json_parser_accepts_minimal_object() -> None:
    parser = JsonLogParser()
    event = parser.parse_line('{"remote_addr":"1.2.3.4","status":200,"path":"/"}')
    assert event is not None
    assert event.src_address == "1.2.3.4"
    assert event.status == 200
