"""Granulometry tab selection and distribution removal behavior."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_core import GranuloConfig, pre
from lmgc90_core.types import AvatarType
from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.granulo_tab import create_granulo_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_state_refresh_preserves_valid_selections_and_parameter_values(qt_app):
    controller = ProjectController()
    controller.new_project("granulo-state-refresh", dimension=2)
    controller.add(pre.material(name="MAT1", materialType="RIGID", density=7800))
    controller.add(pre.material(name="MAT2", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="MOD1", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    controller.add(pre.model(
        name="MOD2", physics="MECAx", element="Rxx2D", dimension=2,
    ))

    tab = create_granulo_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab.mat_combo.setCurrentText("MAT2")
    tab.mod_combo.setCurrentText("MOD2")
    tab.type_combo.setCurrentIndex(
        tab.type_combo.findData(AvatarType.RIGID_POLYGON),
    )
    tab.container.setCurrentIndex(tab.container.findData("Disk2D"))
    tab._param_widgets["r"].setText("1.75")
    tab.distribution.setCurrentIndex(
        tab.distribution.findData("granulo_TwoSizesNumber"),
    )
    tab.distribution_widgets["p_min"].setText("0.3")

    tab.on_state_changed()

    assert tab.mat_combo.currentText() == "MAT2"
    assert tab.mod_combo.currentText() == "MOD2"
    assert tab.type_combo.currentData() == AvatarType.RIGID_POLYGON
    assert tab.container.currentData() == "Disk2D"
    assert tab._param_widgets["r"].text() == "1.75"
    assert tab.distribution_widgets["p_min"].text() == "0.3"


def test_remove_distribution_only_entry_by_selected_item(qt_app):
    controller = ProjectController()
    controller.new_project("granulo-remove-distribution", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    config = GranuloConfig(
        nb_particles=4,
        radius_min=0.01,
        radius_max=0.02,
        container_type="Box2D",
        container_params={"lx": 1.0, "ly": 1.0},
        material_name="STEEL",
        model_name="rigid",
        create_avatars=False,
    )
    controller.deposit(config)

    tab = create_granulo_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    assert tab.list.count() == 1
    tab.list.setCurrentRow(0)
    tab._on_remove()

    assert controller.project.granulo == []
    controller.project.undo()
    assert controller.project.granulo[0].generation_id == config.generation_id
