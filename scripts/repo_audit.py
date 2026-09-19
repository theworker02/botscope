#!/usr/bin/env python3
"""Repository consistency audit for BotScope.

Checks empty package dirs, status-doc presence, and basic importability.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "botscope"

REQUIRED_DOCS = [
    "README.md",
    "FEATURES.md",
    "PROJECT_STATUS.md",
    "PHASE_II_PROGRESS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "docs/development/PARALLEL_WORK_LEDGER.md",
    "docs/development/FILE_OWNERSHIP.md",
    ".github/FUNDING.yml",
    ".github/workflows/ci.yml",
]

REQUIRED_MODULES = [
    "botscope",
    "botscope.api",
    "botscope.cli",
    "botscope.demo",
    "botscope.provenance",
    "botscope.quality",
    "botscope.compare",
    "botscope.research",
    "botscope.diagnostics",
    "botscope.plugins.sdk",
]


def empty_packages() -> list[str]:
    bad: list[str] = []
    for p in sorted(PKG.iterdir()):
        if p.is_dir() and p.name != "__pycache__":
            files = [x for x in p.rglob("*") if x.is_file() and x.suffix == ".py"]
            if not files:
                bad.append(str(p.relative_to(ROOT)))
    return bad


def main() -> int:
    errors = 0
    print("== required docs ==")
    for rel in REQUIRED_DOCS:
        ok = (ROOT / rel).exists()
        print(("OK " if ok else "MISSING "), rel)
        errors += 0 if ok else 1

    print("\n== empty src packages ==")
    empties = empty_packages()
    if empties:
        for e in empties:
            print("EMPTY", e)
            errors += 1
    else:
        print("OK none")

    print("\n== imports ==")
    sys.path.insert(0, str(ROOT / "src"))
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
            print("OK", mod)
        except Exception as exc:
            print("FAIL", mod, exc)
            errors += 1

    print("\n== examples ==")
    for name in (
        "analyze_nginx.py",
        "classify_events.py",
        "inspect_provenance.py",
        "compare_sessions.py",
        "custom_classifier.py",
        "build_report.py",
    ):
        path = ROOT / "examples" / name
        ok = path.exists()
        print(("OK " if ok else "MISSING "), name)
        errors += 0 if ok else 1

    print(f"\nResult: {'PASS' if errors == 0 else 'FAIL'} ({errors} issue(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
