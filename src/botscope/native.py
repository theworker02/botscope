"""Optional native acceleration layer status and graceful fallback."""

from __future__ import annotations

from typing import Any


def native_available() -> bool:
    """Return True when botscope_native extension is importable."""
    try:
        import botscope_native  # noqa: F401
    except ImportError:
        return False
    return True


def native_status() -> dict[str, Any]:
    """Report acceleration backend — never hide missing native as required."""
    if native_available():
        try:
            import botscope_native

            version = getattr(botscope_native, "__version__", "unknown")
        except Exception:  # pragma: no cover
            version = "unknown"
        return {
            "native_parser_available": True,
            "backend": "Rust",
            "version": version,
            "functionality": "AVAILABLE",
            "performance": "ACCELERATED",
        }
    return {
        "native_parser_available": False,
        "backend": "Python",
        "version": None,
        "functionality": "AVAILABLE",
        "performance": "REDUCED",
    }
