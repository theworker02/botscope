"""Plugin SDK — templates, validation, scaffold.

Status: IMPLEMENTED
"""

from botscope.plugins.sdk.scaffold import create_plugin_scaffold
from botscope.plugins.sdk.validate import ValidationIssue, validate_plugin_dir

__all__ = ["ValidationIssue", "create_plugin_scaffold", "validate_plugin_dir"]
