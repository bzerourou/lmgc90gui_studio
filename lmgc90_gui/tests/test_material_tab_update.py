"""MaterialTab updates materials atomically, including referenced materials."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication, QMessageBox

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.material_tab import create_material_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _controller_with_referenced_material() -> ProjectController:
    controller = ProjectController()
    controller.new_project("material-update", dimension=2)
    controller.add(pre.material(
        name="STEEL", materialType="RIGID", density=7800,
    ))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    controller.add(pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL",
    ))
    return controller


def test_material_tab_updates_material_used_by_avatar(qt_app, monkeypatch):
    controller = _controller_with_referenced_material()
    tab = create_material_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab._load_selected("STEEL")
    tab.density_edit.setText("7850")
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)

    tab._on_update()

    assert len(controller.project.materials) == 1
    assert controller.project.materials[0].name == "STEEL"
    assert controller.project.materials[0].density == 7850
    assert controller.project.avatars[0].material_name == "STEEL"


def test_failed_material_rename_keeps_original_and_referenced_material(
    qt_app, monkeypatch,
):
    controller = _controller_with_referenced_material()
    controller.add(pre.material(
        name="OTHER", materialType="RIGID", density=1000,
    ))
    tab = create_material_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab._load_selected("STEEL")
    tab.name_edit.setText("OTHER")
    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args: warnings.append(args[-1]),
    )

    tab._on_update()

    materials = {material.name: material for material in controller.project.materials}
    assert set(materials) == {"STEEL", "OTHER"}
    assert materials["STEEL"].density == 7800
    assert controller.project.avatars[0].material_name == "STEEL"
    assert warnings
