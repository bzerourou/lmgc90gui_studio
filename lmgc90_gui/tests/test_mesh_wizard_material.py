"""Mesh wizard material properties follow the MaterialTab anisotropy rules."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_gui import ProjectController
from lmgc90_gui.dialogs.mesh_wizard import create_mesh_wizard


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("dimension", "expected_orthotropic_fields"),
    [
        (2, {"young1", "young2", "nu12", "G12"}),
        (
            3,
            {
                "young1", "young2", "young3",
                "nu12", "nu13", "nu23",
                "G12", "G13", "G23",
            },
        ),
    ],
)
def test_mesh_wizard_material_fields_follow_anisotropy_and_dimension(
    qt_app, dimension, expected_orthotropic_fields,
):
    controller = ProjectController()
    controller.new_project("mesh-material", dimension=dimension)
    wizard = create_mesh_wizard(controller)
    dimension_page = wizard.page(wizard.PAGE_DIM)
    material_page = wizard.page(wizard.PAGE_MAT)

    if dimension == 3:
        dimension_page.dim_3d.setChecked(True)
    else:
        dimension_page.dim_2d.setChecked(True)
    material_page._apply_anisotropy_visibility()

    isotropic_props = material_page.collect_props()
    assert isotropic_props["anisotropy"] == "isotropic"
    assert {"young", "nu", "G"} <= isotropic_props.keys()
    assert not expected_orthotropic_fields & isotropic_props.keys()

    anisotropy = material_page._prop_widgets["anisotropy"]
    anisotropy.setCurrentText("orthotropic")
    orthotropic_props = material_page.collect_props()
    assert orthotropic_props["anisotropy"] == "orthotropic"
    assert expected_orthotropic_fields <= orthotropic_props.keys()
    assert not {"young", "nu", "G"} & orthotropic_props.keys()
