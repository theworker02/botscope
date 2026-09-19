"""One-shot generator for BotScope thickness (Agent 2). Run then delete if desired."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n") if content.startswith("\n") else content, encoding="utf-8")
    print("wrote", rel)


def main() -> None:
    # ---------- GitHub ----------
    w(
        ".github/FUNDING.yml",
        "github: [theworker02]\nthanks_dev: u/gh/theworker02\n",
    )
    w(
        ".github/CODEOWNERS",
        "# Default owners for BotScope\n*       @theworker02\n\n/.github/           @theworker02\n/docs/              @theworker02\n/src/botscope/      @theworker02\n",
    )
    w(
        ".github/dependabot.yml",
        """version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
""",
    )
    w(
        ".github/PULL_REQUEST_TEMPLATE.md",
        """## Summary
<!-- What does this PR change and why? -->

## Type of change
- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Tests / CI
- [ ] Refactor (no behavior change)

## Checklist
- [ ] I re-read touched files and avoided blind overwrites of parallel work
- [ ] Tests added or updated where appropriate
- [ ] Docs status labels match reality (IMPLEMENTED / PARTIAL / PLANNED / …)
- [ ] No fabricated benchmarks or Internet-wide claims
- [ ] Network contribution remains OFF by default
- [ ] No secrets committed

## Test plan
- [ ] `pytest` (or scoped module tests)
- [ ] Manual CLI check if UX changed (`botscope doctor`, `botscope demo`, …)
""",
    )
    w(
        ".github/ISSUE_TEMPLATE/config.yml",
        """blank_issues_enabled: false
contact_links:
  - name: Security vulnerability
    url: https://github.com/theworker02/botscope/security/advisories/new
    about: Please report security issues privately via GitHub Security Advisories or SECURITY.md.
  - name: Discussions / questions
    url: https://github.com/theworker02/botscope/discussions
    about: General questions and research discussion (if Discussions are enabled).
""",
    )
    w(
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        """name: Bug report
description: Report unexpected behavior in BotScope
title: "[bug] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for helping improve BotScope. Please do **not** paste secrets, full raw logs with PII, or unauthorized capture data.
  - type: input
    id: version
    attributes:
      label: BotScope version
      placeholder: "0.1.0"
    validations:
      required: true
  - type: dropdown
    id: os
    attributes:
      label: Operating system
      options: [Windows, Linux, macOS, Other]
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual behavior
    validations:
      required: true
  - type: textarea
    id: doctor
    attributes:
      label: Output of `botscope doctor` (sanitized)
      description: Prefer `botscope doctor --bundle` then attach only the sanitized summary.
""",
    )
    w(
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        """name: Feature request
description: Propose a new capability for BotScope
title: "[feat] "
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem / research need
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: Proposed solution
    validations:
      required: true
  - type: dropdown
    id: area
    attributes:
      label: Area
      options:
        - Classification / identity
        - Ingest / parsers
        - Provenance / quality
        - Compare / research export
        - CLI / GUI
        - Plugins
        - Docs
        - Other
    validations:
      required: true
  - type: checkboxes
    id: constraints
    attributes:
      label: Constraints acknowledged
      options:
        - label: I am not asking for unauthorized network scanning or surveillance features
          required: true
        - label: UNKNOWN remains a valid scientific outcome (no forced certainty)
          required: true
""",
    )
    w(
        ".github/ISSUE_TEMPLATE/documentation.yml",
        """name: Documentation issue
description: Report incorrect, incomplete, or misleading docs
title: "[docs] "
labels: ["documentation"]
body:
  - type: input
    id: path
    attributes:
      label: Document path or URL
      placeholder: docs/research/METHODOLOGY.md
    validations:
      required: true
  - type: dropdown
    id: severity
    attributes:
      label: Issue type
      options:
        - Incorrect status label (claims IMPLEMENTED but code missing)
        - Missing guide / tutorial
        - Unclear wording
        - Broken link
        - Privacy / security wording concern
    validations:
      required: true
  - type: textarea
    id: details
    attributes:
      label: Details
    validations:
      required: true
""",
    )
    w(
        ".github/workflows/ci.yml",
        """name: CI

on:
  push:
    branches: [main, master, "agent2/**", "agent1/**"]
  pull_request:
    branches: [main, master]

jobs:
  test:
    name: lint + pytest (${{ matrix.os }}, py${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install package (dev extras)
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Ruff check
        run: ruff check src tests scripts

      - name: Pytest
        run: pytest --tb=short
""",
    )

    print("github done")


if __name__ == "__main__":
    main()
