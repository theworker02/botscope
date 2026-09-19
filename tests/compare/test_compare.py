"""Compare module tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from botscope.api import Analyzer
from botscope.compare import compare_classifiers, compare_event_sets, compare_sessions
from botscope.demo import ensure_demo_log


def test_compare_sessions_and_classifiers():
    log = ensure_demo_log()
    with tempfile.TemporaryDirectory() as tmp:
        left = Path(tmp) / "a.bscope"
        right = Path(tmp) / "b.bscope"
        a = Analyzer().analyze(log, output=left, is_demo=True)
        Analyzer().analyze(log, output=right, is_demo=True)
        cmp = compare_sessions(left, right)
        assert cmp.left_events == cmp.right_events
        assert cmp.left_events > 0
        self_cmp = compare_event_sets(a.events, a.events)
        assert self_cmp.only_left_ids == 0
        clf = compare_classifiers(a.events)
        assert 0.0 <= clf.agreement_rate <= 1.0
