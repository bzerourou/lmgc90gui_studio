from types import SimpleNamespace

from lmgc90_core import DOFOperation, Project, pre
from lmgc90_engine.materialize import _apply_dof


class CapturingBody:
    def __init__(self):
        self.calls = []

    def imposeInitValue(self, **kwargs):
        self.calls.append(("imposeInitValue", kwargs))

    def imposeDrivenDof(self, **kwargs):
        self.calls.append(("imposeDrivenDof", kwargs))

    def rotate(self, **kwargs):
        self.calls.append(("rotate", kwargs))


def test_materialized_dof_keeps_lmgc_parameters_and_filters_color():
    project = Project(name="dof_color", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    red = project.add(pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL", color="REDxx"
    ))
    blue = project.add(pre.rigidDisk(
        r=0.1, center=[1.0, 0.0], model="rigid", material="STEEL", color="BLUEx"
    ))
    red_body = CapturingBody()
    blue_body = CapturingBody()
    scene = SimpleNamespace(body_by_avatar_id={
        red.avatar_id: red_body,
        blue.avatar_id: blue_body,
    })

    _apply_dof(
        project,
        scene,
        DOFOperation(
            "imposeInitValue", "color", "REDxx",
            {"group": "all", "component": 1, "value": 0.25},
        ),
    )

    assert red_body.calls == [
        ("imposeInitValue", {"group": "all", "component": 1, "value": 0.25})
    ]
    assert blue_body.calls == []

    driven = {
        "group": "down",
        "component": [1],
        "description": "evolution",
        "evolutionFile": "vertical_velocity.dat",
        "dofty": "vlocy",
    }
    _apply_dof(
        project,
        scene,
        DOFOperation("imposeDrivenDof", "avatar", red.avatar_id, driven),
    )
    _apply_dof(
        project,
        scene,
        DOFOperation(
            "rotate", "avatar", blue.avatar_id,
            {"description": "Euler", "phi": 0.1, "theta": 0.2, "psi": 0.3},
        ),
    )
    assert red_body.calls[-1] == ("imposeDrivenDof", driven)
    assert blue_body.calls == [
        ("rotate", {"description": "Euler", "phi": 0.1, "theta": 0.2, "psi": 0.3})
    ]
