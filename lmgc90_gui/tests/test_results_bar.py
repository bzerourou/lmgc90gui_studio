from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pyvista")

from lmgc90_gui.views.results_bar import ResultsBar


class _Slider:
    def __init__(self, value: int, maximum: int, on_change):
        self._value = value
        self._maximum = maximum
        self._on_change = on_change

    def value(self) -> int:
        return self._value

    def maximum(self) -> int:
        return self._maximum

    def setMaximum(self, value: int) -> None:
        self._maximum = value
        self.setValue(min(self._value, value))

    def setValue(self, value: int) -> None:
        changed = value != self._value
        self._value = value
        if changed:
            self._on_change(value)


def _bar(current: int, maximum: int, new_count: int):
    rendered = []
    bar = SimpleNamespace(
        series=SimpleNamespace(reload=lambda: new_count),
        show_frame=rendered.append,
    )
    bar.slider = _Slider(current, maximum, bar.show_frame)
    return bar, rendered


def test_refresh_follows_new_frames_when_cursor_was_at_latest():
    bar, rendered = _bar(current=3, maximum=3, new_count=5)

    ResultsBar._refresh_series(bar)

    assert bar.slider.maximum() == 4
    assert bar.slider.value() == 4
    assert rendered == [4]


def test_refresh_redraws_selected_frame_when_step_count_is_unchanged():
    bar, rendered = _bar(current=2, maximum=4, new_count=5)

    ResultsBar._refresh_series(bar)

    assert bar.slider.value() == 2
    assert rendered == [2]
