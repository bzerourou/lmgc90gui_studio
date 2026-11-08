"""Avatar form switches between regular and custom polygon parameters."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_core import pre
from lmgc90_core.types import AvatarOrigin, AvatarType
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
    assert avatar.generation_type == (
        "full" if avatar_type == AvatarType.RIGID_POLYGON else "vertices"
    )
    assert avatar.vertices is not None

    tab._generation_checkbox.setChecked(True)
    assert set(tab._param_widgets) == {"nb_vertices", "radius"}
    assert tab._param_widgets["nb_vertices"][0].value() == regular_vertices
    assert tab._param_widgets["radius"][0].text() == "0.4"


def test_wall_forms_take_user_height_and_derive_constructor_radii(qt_app):
    controller = ProjectController()
    controller.new_project("wall-height", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    tab = create_avatar_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()

    tab.type_combo.setCurrentIndex(tab.type_combo.findData(AvatarType.FINE_WALL))
    assert set(tab._param_widgets) == {"l", "h", "nb_vertex"}
    tab._param_widgets["h"][0].setText("0.08")
    fine_wall = tab._build(
        pre, AvatarType.FINE_WALL, [0.0, 0.0], "STEEL", "rigid", "BLUEx",
        tab._read_params(),
    )
    controller.add(fine_wall)
    assert fine_wall.wall_params["h"] == 0.08
    assert fine_wall.wall_params["r"] == 0.04

    tab.type_combo.setCurrentIndex(tab.type_combo.findData(AvatarType.GRANULO_WALL))
    assert set(tab._param_widgets) == {"l", "h", "rmin", "nb_vertex"}
    tab._param_widgets["h"][0].setText("0.06")
    granulo_wall = tab._build(
        pre, AvatarType.GRANULO_WALL, [0.0, 0.0], "STEEL", "rigid", "BLUEx",
        tab._read_params(),
    )
    controller.add(granulo_wall)
    assert granulo_wall.wall_params["h"] == 0.06
    assert granulo_wall.wall_params["rmax"] == 0.03


def test_update_avatar_preserves_origin_contactors_and_brick_wall_params(qt_app):
    controller = ProjectController()
    controller.new_project("avatar-update-brick", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    brick = pre.emptyAvatar(
        center=[0.0, 0.0], model="rigid", material="STEEL", color="BLUEx",
    )
    brick.origin = AvatarOrigin.LOOP
    brick.wall_params = {"brick_name": "jointed", "l": 0.2, "h": 0.1}
    brick.contactors.append({
        "shape": "DISKx", "color": "BLUEx", "params": {"byrd": 0.05},
    })
    controller.add_avatar(brick)

    tab = create_avatar_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab._load_selected(brick.avatar_id)
    tab._on_update()

    updated = controller.project.avatar(brick.avatar_id)
    assert updated.origin == AvatarOrigin.LOOP
    assert updated.contactors == brick.contactors
    assert updated.wall_params == brick.wall_params


def test_update_mesh_avatar_preserves_contactors_and_unrepresented_mesh_params(qt_app):
    controller = ProjectController()
    controller.new_project("avatar-update-mesh", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="ELAS", density=7800, young=1e6, nu=0.25))
    controller.add(pre.model(
        name="mesh", physics="MECAx", element="T3xxx", dimension=2,
    ))
    mesh = pre.meshed_rectangle(
        lx=1.0, ly=0.5, nx=2, ny=2, center=[0.0, 0.0],
        model="mesh", material="STEEL",
        contactors=[{"shape": "CLxxx", "color": "CYANx"}],
    )
    mesh.origin = AvatarOrigin.FACTORY
    mesh.mesh_params["source_mesh_tag"] = "preserve-me"
    controller.add_avatar(mesh)

    tab = create_avatar_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab._load_selected(mesh.avatar_id)
    tab._on_update()

    updated = controller.project.avatar(mesh.avatar_id)
    assert updated.origin == AvatarOrigin.FACTORY
    assert updated.contactors == mesh.contactors
    assert updated.mesh_params["source_mesh_tag"] == "preserve-me"


@pytest.mark.parametrize(
    "mesh_params",
    [
        {"geom": "Disque", "r": 0.5},
        {"geom": "Sphère", "r": 0.5},
        {"geom": "Fichier externe", "filepath": "mesh.msh"},
        {"geom": "Boîte (H8)", "lx": 1.0, "ly": 1.0, "lz": 1.0},
    ],
)
def test_update_nonrectangular_mesh_is_rejected(
    qt_app, monkeypatch, mesh_params,
):
    from PyQt6.QtWidgets import QMessageBox

    controller = ProjectController()
    controller.new_project("avatar-update-nonrectangle", dimension=2)
    controller.add(pre.material(
        name="STEEL", materialType="ELAS", density=7800,
        young=1e6, nu=0.25,
    ))
    controller.add(pre.model(
        name="mesh", physics="MECAx", element="T3xxx", dimension=2,
    ))
    mesh = pre.meshed_rectangle(
        lx=1.0, ly=0.5, nx=2, ny=2, center=[0.0, 0.0],
        model="mesh", material="STEEL",
        contactors=[{"shape": "CLxxx", "color": "CYANx"}],
    )
    mesh.mesh_params.update(mesh_params)
    controller.add_avatar(mesh)
    original = mesh.to_dict()
    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args: warnings.append(args[2]),
    )

    tab = create_avatar_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab._load_selected(mesh.avatar_id)
    tab._on_update()

    assert controller.project.avatar(mesh.avatar_id).to_dict() == original
    assert warnings == ["Update is only supported for rectangular meshes."]


@pytest.mark.parametrize(
    ("dimension", "element", "avatar_factory", "avatar_type"),
    [
        (
            2, "Rxx2D", pre.rigidDisk, AvatarType.RIGID_DISK,
        ),
        (
            3, "Rxx3D", pre.rigidCylinder, AvatarType.RIGID_CYLINDER,
        ),
    ],
)
def test_update_preserves_hollow_rigid_avatar(
    qt_app, dimension, element, avatar_factory, avatar_type,
):
    controller = ProjectController()
    controller.new_project("hollow-avatar-update", dimension=dimension)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element=element, dimension=dimension,
    ))
    kwargs = {
        "r": 0.2,
        "center": [0.0] * dimension,
        "model": "rigid",
        "material": "STEEL",
        "is_Hollow": True,
    }
    if avatar_type == AvatarType.RIGID_CYLINDER:
        kwargs["h"] = 0.4
    avatar = avatar_factory(**kwargs)
    controller.add_avatar(avatar)

    tab = create_avatar_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()
    tab._load_selected(avatar.avatar_id)

    assert tab._param_widgets["is_Hollow"][0].isChecked()
    tab._on_update()

    updated = controller.project.avatar(avatar.avatar_id)
    assert updated.is_hollow is True
