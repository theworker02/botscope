"""botscope_source_registry package."""

from botscope.sources.registry.catalog import (
    REGISTRY,
    SourceRegistryEntry,
    get_entry,
    registry_as_dicts,
    zero_auth_entries,
)

__all__ = [
    "REGISTRY",
    "SourceRegistryEntry",
    "get_entry",
    "registry_as_dicts",
    "zero_auth_entries",
]
