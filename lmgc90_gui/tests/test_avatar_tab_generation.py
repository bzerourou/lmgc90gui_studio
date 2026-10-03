"""Avatar form switches between regular and custom polygon parameters."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_core import pre
from lmgc90_core.types import AvatarType
from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.avatar_tab import create_avatar_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("dimension", "avatar_type", "custom_vertices", "regular_vertices"),
    [
        (2, AvatarType.RIGID_POLYGON, "0,0; 1,0; 0,1", 6),
        (
            3,
            AvatarType.RIGID_POLYHEDRON,
            "1,1,1; -1,-1,1; -1,1,-1; 1,-1,-1; 0,0,1",
            8,
        ),
    ],
)
def test_generation_checkbox_switches_parameter_fields(
    qt_app, dimension, avatar_type, custom_vertices, regular_vertices,
):
    controller = ProjectController()
    controller.new_project("avatar-generation", dimension=dimension)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid",
        physics="MECAx",
        element="Rxx2D" if dimension == 2 else "Rxx3D",
        dimension=dimension,
    ))
    tab = create_avatar_tab()
    tab.bind_controller(controller)
    if tab.type_combo.findData(avatar_type) < 0:
        tab.type_combo.addItem(avatar_type.value, avatar_type)
    tab.type_combo.setCurrentIndex(tab.type_combo.findData(avatar_type))

    assert tab._generation_checkbox.isChecked()
    assert set(tab._param_widgets) == {"nb_vertices", "radius"}
    tab._param_widgets["nb_vertices"][0].setValue(regular_vertices)
    tab._param_widgets["radius"][0].setText("0.4")

    tab._generation_checkbox.setChecked(False)
    assert set(tab._param_widgets) == {"vertices"}
    tab._param_widgets["vertices"][0].setText(custom_vertices)
    params = tab._read_params()
    avatar = tab._build(
        pre, avatar_type, [0.0] * dimension, "STEEL", "rigid", "BLUEx", params,
    )
    assert params["generation_type"] == "full"
    assert avatar.generation_type == "full"
    assert avatar.vertices is not None

    tab._generation_checkbox.setChecked(True)
    assert set(tab._param_widgets) == {"nb_vertices", "radius"}
    assert tab._param_widgets["nb_vertices"][0].value() == regular_vertices
    assert tab._param_widgets["radius"][0].text() == "0.4"
