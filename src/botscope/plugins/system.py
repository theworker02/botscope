"""Plugin system — stable entry-point based extension interface."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Any, Callable, Protocol

from botscope.normalize.event import NormalizedEvent


class EventParserPlugin(Protocol):
    name: str

    def can_parse(self, path: str) -> bool: ...

    def parse(self, path: str) -> list[NormalizedEvent]: ...


class ClassifierPlugin(Protocol):
    name: str

    def classify(self, event: NormalizedEvent) -> dict[str, Any] | None: ...


@dataclass
class PluginInfo:
    name: str
    group: str
    obj: Any


def discover_plugins(group: str = "botscope.plugins") -> list[PluginInfo]:
    try:
        eps = entry_points()
        selected = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
    except Exception:
        return []
    plugins: list[PluginInfo] = []
    for ep in selected:
        try:
            plugins.append(PluginInfo(name=ep.name, group=group, obj=ep.load()))
        except Exception:
            continue
    return plugins


def register_local(name: str, factory: Callable[[], Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    reg = registry if registry is not None else {}
    reg[name] = factory
    return reg
