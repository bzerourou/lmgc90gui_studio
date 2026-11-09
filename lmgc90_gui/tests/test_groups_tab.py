"""Group editing must retain population ids and support names containing spaces."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from lmgc90_core import pre
from lmgc90_gui import ProjectController
from lmgc90_gui.views.tabs.groups_tab import create_groups_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_edit_group_keeps_population_ids_and_full_group_name(qt_app):
    controller = ProjectController()
    controller.new_project("groups", dimension=2)
    controller.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    controller.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    first = controller.add(pre.rigidDisk(
        r=0.1, center=[0, 0], model="rigid", material="STEEL",
    ))
    replacement = controller.add(pre.rigidDisk(
        r=0.1, center=[1, 0], model="rigid", material="STEEL",
    ))
    population_id = "pop_soA123"
    controller.group("grains SoA", [population_id, first.avatar_id])

    tab = create_groups_tab()
    tab.bind_controller(controller)
    tab.on_state_changed()

    group_item = tab.group_list.item(0)
    tab.group_list.setCurrentItem(group_item)
    assert tab.name_edit.text() == "grains SoA"

    for index in range(tab.member_list.count()):
        item = tab.member_list.item(index)
        if item.data(Qt.ItemDataRole.UserRole) == first.avatar_id:
            item.setSelected(False)
        elif item.data(Qt.ItemDataRole.UserRole) == replacement.avatar_id:
            item.setSelected(True)

    tab._on_save()

    assert controller.project.avatar_groups["grains SoA"] == [
        population_id, replacement.avatar_id,
    ]
