from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PyQt6.QtWidgets")
from PyQt6.QtWidgets import QApplication

from lmgc90_core.types import AvatarType
from lmgc90_gui.views.tabs import contactors_tab
from lmgc90_gui.views.tabs.contactors_tab import create_contactors_tab


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_contactors_tab_builds_shape_fields_from_runtime_catalog(
    qt_app, monkeypatch,
):
    monkeypatch.setattr(
        contactors_tab,
        "contactor_schema_catalog",
        lambda: {
            "dimension_contactors": {
                "2": ("DISKx", "NEWxx", "POLYG"),
                "3": ("CSpxx", "ASpxx", "PT3Dx"),
            },
            "body_type_contactors": {
                "RBDY2": ("NEWxx", "DISKx"),
                "RBDY3": ("POLYR",),
                "MAILx": ("CSxxx", "ASpxx", "POLYR", "PT2DL"),
            },
            "options": {"NEWxx": ("nb_patch",)},
            "optional_options": {"NEWxx": ("mode",)},
        },
    )
    tab = create_contactors_tab()
    avatar = SimpleNamespace(avatar_type=AvatarType.EMPTY_AVATAR)

    assert tab._compatible_shapes(avatar, 2) == ("DISKx", "NEWxx")
    mesh_avatar = SimpleNamespace(avatar_type=AvatarType.MESH_DEFORMABLE)
    assert tab._compatible_shapes(mesh_avatar, 3) == ("CSxxx", "ASpxx")
    assert tab._compatible_shapes(mesh_avatar, 2) == ()
    assert "POLYR" not in tab._mesh_contactors

    tab._on_shape_changed("NEWxx")

    assert set(tab._param_fields) == {"shift", "nb_patch", "mode"}
    tab._on_shape_changed("POLYR")
    assert {"generation_type", "nb_vertices", "radius", "shift"} <= set(
        tab._param_fields
    )
