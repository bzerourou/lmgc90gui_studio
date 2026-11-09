"""Qt signals when PyQt6 is available; no-op stubs otherwise (headless tests)."""
from __future__ import annotations

from typing import Any, Callable, List


class _NoopSignal:
    """Minimal stand-in for pyqtSignal so the controller imports without Qt."""

    def __init__(self, *args: Any):
        self._signal_args = args
        self._signal_name: str | None = None
        self._slots: List[Callable] = []

    def __set_name__(self, owner: type, name: str) -> None:
        self._signal_name = f"{owner.__module__}.{owner.__qualname__}.{name}"

    def __get__(self, instance: Any, owner: type | None = None) -> "_NoopSignal":
        if instance is None:
            return self
        if self._signal_name is None:
            raise RuntimeError("no-op signal descriptor was not initialized")
        instance_signals = instance.__dict__.setdefault("_noop_signals", {})
        signal = instance_signals.get(self._signal_name)
        if signal is None:
            signal = _NoopSignal(*self._signal_args)
            instance_signals[self._signal_name] = signal
        return signal

    def connect(self, slot: Callable) -> None:
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot: Callable | None = None) -> None:
        if slot is None:
            self._slots.clear()
        elif slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args: Any) -> None:
        for slot in list(self._slots):
            slot(*args)

    def __call__(self, *args: Any) -> "_NoopSignal":
        # class-body usage: state_changed = Signal()  →  returns a new instance
        return _NoopSignal(*args)


def _try_qt_signal():
    try:
        from PyQt6.QtCore import pyqtSignal
        return pyqtSignal
    except ImportError:
        return _NoopSignal


Signal = _try_qt_signal()


def qt_available() -> bool:
    try:
        import PyQt6  # noqa: F401
        return True
    except ImportError:
        return False


def make_qobject_base():
    """Return QObject if Qt is present, else a plain object base."""
    try:
        from PyQt6.QtCore import QObject
        return QObject
    except ImportError:

        class _Plain:
            def __init__(self, parent=None):
                pass

        return _Plain
