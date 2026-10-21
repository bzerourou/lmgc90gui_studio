"""Model tab options follow the complete local LMGC90 element catalogue."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from lmgc90_core import Model
from lmgc90_core.types import (
    ELEMENTS_BY_PHYSICS,
    MODEL_COMMON_OPTIONS_BY_PHYSICS,
    MODEL_OPTION_CHOICES,
    MODEL_OPTIONS_BY_PHYSICS,
)
from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.model_tab import create_model_tab

_QT_APP = None

def _app():
    global _QT_APP
    _QT_APP = QApplication.instance() or QApplication([])
    return _QT_APP


def test_option_schema_covers_catalogued_finite_elements():
    rigid = {"Rxx2D", "Rxx3D"}
    for physics, dimensions in ELEMENTS_BY_PHYSICS.items():
        common = MODEL_COMMON_OPTIONS_BY_PHYSICS[physics]
        element_options = MODEL_OPTIONS_BY_PHYSICS[physics]
        for elements in dimensions.values():
            for element in elements:
                names = () if element in rigid else (
                    *element_options.get(element, ()), *common
                )
                if element in rigid:
                    assert not names, (physics, element, names)
                else:
                    assert names, (physics, element, names)
                assert all(name in MODEL_OPTION_CHOICES for name in names)


def test_model_tab_collects_element_options_and_keeps_unknown_options():
    _app()
    controller = ProjectController()
    controller.new_project("model-options", 2)
    tab = create_model_tab()
    tab.bind_controller(controller)
    tab.physics_combo.setCurrentText("MECAx")
    assert {
        tab.element_combo.itemText(index)
        for index in range(tab.element_combo.count())
    } == set(ELEMENTS_BY_PHYSICS["MECAx"][2])

    tab.name_edit.setText("FEMxx")
    tab.element_combo.setCurrentText("T3xxx")
    tab.option_widgets["kinematic"].setCurrentText("large")
    tab.advanced_options_edit.setText("custom_flag='enabled'")
    model = tab._build()
    assert model.options["kinematic"] == "large"
    assert model.options["custom_flag"] == "enabled"

    controller.add_model(model)
    script = controller.emit_pre_script()
    assert "kinematic='large'" in script
    assert "custom_flag='enabled'" in script
    tab._load_selected("FEMxx")
    assert tab.option_widgets["kinematic"].currentText() == "large"
    assert tab.advanced_options_edit.text() == "custom_flag='enabled'"


def test_discrete_elements_set_required_option_automatically():
    _app()
    controller = ProjectController()
    controller.new_project("spring-model", 2)
    tab = create_model_tab()
    tab.bind_controller(controller)
    tab.physics_combo.setCurrentText("MECAx")
    tab.element_combo.setCurrentText("SPRG2")
    tab.name_edit.setText("SPRNG")

    assert tab._build().options["discrete"] == "yes__"


def test_model_tab_shows_physics_specific_finite_element_parameters():
    _app()
    controller = ProjectController()
    controller.new_project("physics-model-options", 2)
    tab = create_model_tab()
    tab.bind_controller(controller)

    tab.physics_combo.setCurrentText("THERx")
    tab.element_combo.setCurrentText("T3xxx")
    assert set(tab.option_widgets) == {
        "capacity_storage", "formulation", "convection_type", "external_model",
    }
    assert [
        tab.option_widgets["formulation"].itemText(index)
        for index in range(tab.option_widgets["formulation"].count())
    ] == ["class"]

    tab.physics_combo.setCurrentText("POROx")
    tab.element_combo.setCurrentText("T33xx")
    assert set(tab.option_widgets) == {
        "kinematic", "mass_storage", "capacity_storage", "material",
        "anisotropy", "external_model", "physical_type", "convection_type",
    }

    tab.physics_combo.setCurrentText("MECAx")
    tab.element_combo.setCurrentText("Rxx2D")
    assert not tab.option_widgets
