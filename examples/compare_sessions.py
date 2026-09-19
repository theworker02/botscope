#!/usr/bin/env python3
"""Compare two demo analysis sessions (same input, separate outputs)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from botscope.api import Analyzer
from botscope.compare import compare_sessions
from botscope.demo import DEMO_NOTICE, ensure_demo_log


def main() -> None:
    print(DEMO_NOTICE)
    log = ensure_demo_log()
    with tempfile.TemporaryDirectory() as tmp:
        left = Path(tmp) / "left.bscope"
        right = Path(tmp) / "right.bscope"
        Analyzer().analyze(log, output=left, is_demo=True)
        Analyzer().analyze(log, output=right, is_demo=True)
        cmp = compare_sessions(left, right)
        print(json.dumps(cmp.to_dict(), indent=2))


if __name__ == "__main__":
    main()
