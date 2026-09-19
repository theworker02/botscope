"""Capability registry package.

Status: IMPLEMENTED
"""

from __future__ import annotations

from botscope.capabilities.registry import (
    REGISTRY,
    FeatureCapability,
    FeatureStatus,
    features_matrix,
    get_feature,
    list_features,
)

__all__ = [
    "REGISTRY",
    "FeatureCapability",
    "FeatureStatus",
    "features_matrix",
    "get_feature",
    "list_features",
]
