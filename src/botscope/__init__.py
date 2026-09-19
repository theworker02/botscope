"""BotScope — Python-first Internet bot-traffic measurement & observatory."""

from __future__ import annotations

from botscope.__version__ import __version__
from botscope.api.analyzer import AnalysisResult, Analyzer
from botscope.classify.engine import ClassificationResult
from botscope.normalize.event import NormalizedEvent, ProvenanceLevel

__all__ = [
    "AnalysisResult",
    "Analyzer",
    "ClassificationResult",
    "NormalizedEvent",
    "ProvenanceLevel",
    "__version__",
]
