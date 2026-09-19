"""Subtle Observatory motion helpers (respect reduce-motion)."""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QAbstractAnimation,
    QObject,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

_REDUCE_MOTION = False


def set_reduce_motion(enabled: bool) -> None:
    global _REDUCE_MOTION
    _REDUCE_MOTION = bool(enabled)


def reduce_motion() -> bool:
    return _REDUCE_MOTION


def fade_in(widget: QWidget, *, duration_ms: int = 220) -> QPropertyAnimation | None:
    """Fade a widget from 0 → 1 opacity. No-op when reduce-motion is on."""
    if reduce_motion() or widget is None:
        if widget is not None:
            widget.setGraphicsEffect(None)
            widget.setWindowOpacity(1.0)
        return None
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    # Keep a reference so GC does not kill the animation mid-flight.
    widget._botscope_fade_anim = anim  # type: ignore[attr-defined]
    return anim


def pulse_opacity(
    widget: QWidget,
    *,
    duration_ms: int = 180,
    trough: float = 0.35,
) -> QPropertyAnimation | None:
    """Brief dim → bright pulse (metric updates, status flashes)."""
    if reduce_motion() or widget is None:
        return None
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration_ms)
    anim.setKeyValueAt(0.0, 1.0)
    anim.setKeyValueAt(0.4, trough)
    anim.setKeyValueAt(1.0, 1.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._botscope_pulse_anim = anim  # type: ignore[attr-defined]
    return anim


def stagger_fade(
    widgets: list[QWidget],
    *,
    per_item_ms: int = 160,
    stagger_ms: int = 40,
) -> QParallelAnimationGroup | None:
    """Fade several widgets in with a short stagger (empty-state CTAs, tiles)."""
    if reduce_motion() or not widgets:
        for w in widgets:
            if w is not None:
                w.setGraphicsEffect(None)
        return None
    group = QParallelAnimationGroup()
    for i, widget in enumerate(widgets):
        if widget is None:
            continue
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(per_item_ms + i * stagger_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(anim)
    group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    if widgets:
        widgets[0]._botscope_stagger_group = group  # type: ignore[attr-defined]
    return group


def animate_float(
    target: QObject,
    prop: bytes,
    end: float,
    *,
    start: float | None = None,
    duration_ms: int = 420,
) -> QPropertyAnimation | None:
    """Animate a float Qt property on ``target``. No-op when reduce-motion is on."""
    if reduce_motion() or target is None:
        if target is not None:
            target.setProperty(prop.decode(), end)
        return None
    anim = QPropertyAnimation(target, prop, target)
    anim.setDuration(duration_ms)
    if start is not None:
        anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    target._botscope_float_anim = anim  # type: ignore[attr-defined]
    return anim
