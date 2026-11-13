"""Loop tab parameter visibility follows the selected loop type."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_gui.views.tabs.loop_tab import create_loop_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("kind", "visible_fields"),
    [
        ("circle", {"count", "radius", "offset_x", "offset_y", "offset_z"}),
        ("grid", {"count", "step", "offset_x", "offset_y", "offset_z"}),
        ("line", {
            "count", "step", "offset_x", "offset_y", "offset_z", "invert",
        }),
        ("spiral", {
            "count", "radius", "offset_x", "offset_y", "offset_z",
            "spiral_factor",
        }),
    ],
)
def test_parameter_rows_follow_selected_loop_type(qt_app, kind, visible_fields):
    tab = create_loop_tab()

    tab.kind_combo.setCurrentText(kind)

    for key, (label, widget) in tab._parameter_rows.items():
        assert widget.isHidden() is (key not in visible_fields)
        assert label.isHidden() is (key not in visible_fields)
