"""Dynamic variable dialog rejects names reserved by expression contexts."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication, QMessageBox

from lmgc90_gui import ProjectController
from lmgc90_gui.dialogs.dynamic_vars_dialog import create_dynamic_vars_dialog


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("name", ["e", "pi", "min", "max", "avatar", "group", "material", "model"])
def test_add_rejects_reserved_dynamic_variable_name(qt_app, monkeypatch, name):
    controller = ProjectController()
    controller.new_project("reserved-dynamic-var", dimension=2)
    dialog = create_dynamic_vars_dialog(controller)
    dialog.name_edit.setText(name)
    dialog.expr_edit.setText("1")
    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args: warnings.append(args[2]),
    )

    dialog._on_add()

    assert controller.project.dynamic_vars == {}
    assert warnings == [f"Nom réservé dans les expressions dynamiques : {name}"]
