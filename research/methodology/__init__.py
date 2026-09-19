"""Research methodology companion package."""

from botscope.datasets import labeled_mini_eval, load_labeled_mini

eval_fixture_self_agreement = labeled_mini_eval

__all__ = ["eval_fixture_self_agreement", "load_labeled_mini", "labeled_mini_eval"]
