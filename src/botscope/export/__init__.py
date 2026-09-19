"""Richer multi-format export pipeline.

Status: IMPLEMENTED

Wraps report generators and adds a unified ExportJob that can emit
multiple artifacts (JSON/MD/HTML/CSV) from one AnalysisResult / session.
"""

from __future__ import annotations

from botscope.export.pipeline import ExportArtifact, ExportJob, export_analysis

__all__ = [
    "ExportArtifact",
    "ExportJob",
    "export_analysis",
]
