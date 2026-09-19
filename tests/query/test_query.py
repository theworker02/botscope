"""Safe query tests."""

from __future__ import annotations

import pytest

from botscope.demo import iter_demo_events
from botscope.query import QueryError, filter_events, parse_simple_query


def test_parse_and_filter():
    preds = parse_simple_query('user_agent icontains bot AND status eq 200')
    assert len(preds) == 2
    matched = list(filter_events(iter_demo_events(), preds))
    assert matched
    for e in matched:
        assert e.status == 200
        assert "bot" in (e.user_agent or "").lower()


def test_rejects_code_execution_tokens():
    with pytest.raises(QueryError):
        parse_simple_query("classification eq __import__('os')")
