"""PostProTab stores stable IDs rather than display labels for targets."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.postpro_tab import create_postpro_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_postpro_avatar_target_stores_avatar_id(qt_app):
    controller = ProjectController()
    controller.new_project("postpro-avatar", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    avatar = controller.add(pre.smoothWall(
        l=1.0, h=0.1, center=[0.0, 0.0],
        model="rigid", material="STEEL",
    ))
    tab = create_postpro_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()

    tab.target_type.setCurrentText("avatar")

    target_index = tab.target_value.findData(avatar.avatar_id)
    assert target_index >= 0
    assert tab.target_value.itemText(target_index).startswith(
        f"{avatar.avatar_id[:12]}…"
    )
    tab.target_value.setCurrentIndex(target_index)
    assert tab.target_value.currentData() == avatar.avatar_id

    tab.name_combo.setCurrentText("BODY TRACKING")
    tab._on_add()

    assert controller.project.postpro[-1].target_type == "avatar"
    assert controller.project.postpro[-1].target_value == avatar.avatar_id


def test_postpro_group_target_stores_group_name(qt_app):
    controller = ProjectController()
    controller.new_project("postpro-group", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    avatar = controller.add(pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL",
    ))
    controller.project.group("walls", [avatar.avatar_id])
    tab = create_postpro_tab()
    tab.bind_controller(controller)

    tab.target_type.setCurrentText("group")
    index = tab.target_value.findData("walls")
    assert index >= 0
    tab.target_value.setCurrentIndex(index)
    assert tab.target_value.currentData() == "walls"
