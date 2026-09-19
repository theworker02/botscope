"""Companion helpers for research methodology docs.

Delegates to ``botscope.datasets`` so imports work from the installed package.
"""

from __future__ import annotations

from botscope.datasets import labeled_mini_eval, load_labeled_mini

# Back-compat names used in docs
eval_fixture_self_agreement = labeled_mini_eval

__all__ = [
    "eval_fixture_self_agreement",
    "load_labeled_mini",
    "labeled_mini_eval",
]
