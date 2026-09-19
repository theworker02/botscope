"""Classification package."""

from botscope.classify.engine import Classifier
from botscope.classify.result import ClassificationResult
from botscope.classify.taxonomy import AUTOMATION_CATEGORIES, BotCategory

__all__ = [
    "AUTOMATION_CATEGORIES",
    "BotCategory",
    "ClassificationResult",
    "Classifier",
]
