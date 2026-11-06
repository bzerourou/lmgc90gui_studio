from types import SimpleNamespace

import pytest

from lmgc90_core import Project, pre
from lmgc90_core.chipy_rules import select_detectors
from lmgc90_core.chipy_script import emit_chipy


def test_explicit_false_does_not_disable_detector_required_by_visibility():
    visibility = [
        SimpleNamespace(
            candidate_contactor="SPHER",
            antagonist_contactor="SPHER",
        )
    ]

    selected = select_detectors(
        3,
        {"use_SPSPx": False, "use_SPPLx": False},
        visibility,
    )

    assert "SPSPx" in selected
    assert "SPPLx" not in selected


def test_explicit_true_can_add_detector_not_required_by_visibility():
    visibility = [
        SimpleNamespace(
            candidate_contactor="SPHER",
            antagonist_contactor="SPHER",
        )
    ]

    selected = select_detectors(
        3,
        {"use_SPPLx": True},
        visibility,
    )

    assert selected == ["SPPLx", "SPSPx"]


def test_inferred_detector_is_not_disabled_by_stale_explicit_false():
    selected = select_detectors(
        3,
        {"use_SPSPx": False},
        inferred={"use_SPSPx": True},
    )

    assert selected == ["SPSPx"]


def test_new_spheres_enable_inferred_detector_with_stale_dialog_params():
    project = Project(name="spheres", dimension=3)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx3D", dimension=3,
    ))
    project.add(pre.rigidSphere(
        r=0.1, center=[0, 0, 0], model="rigid", material="STEEL",
    ))

    script = emit_chipy(project, use_SPSPx=False)

    assert "chipy.SPSPx_SelectProxTactors()" in script


def test_empty_detector_selection_warns_and_marks_generated_script():
    project = Project(name="empty", dimension=3)

    with pytest.warns(UserWarning, match="No contact detector"):
        script = emit_chipy(project)

    assert "chipy.SelectProxTactors()" in script
    assert "# WARNING: no individual contact detector selected or inferred" in script
