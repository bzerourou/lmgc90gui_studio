import ast

import pytest

from lmgc90_core import Project
from lmgc90_core.compute_script import ComputeScriptGenerator


def _generate(set_entries):
    project = Project(name="set_actions", dimension=2)
    return ComputeScriptGenerator(project).generate_string({
        "use_mecaMAILx": False,
        "use_therMAILx": False,
        "use_poroMAILx": False,
        "set_entries": set_entries,
    })


def test_set_actions_are_generated_at_the_selected_times():
    script = _generate([
        {
            "func": "RBDY2_SetVisible",
            "args": "1",
            "step_mode": "before",
        },
        {
            "func": "SetThetaIntegrator",
            "args": "theta",
            "step_mode": "all",
        },
        {
            "func": "RBDY2_SetInvisible",
            "args": "2",
            "step_mode": "every_n",
            "step_val": 3,
        },
        {
            "func": "SetTimeStep",
            "args": "dt * 0.5",
            "step_mode": "at_k",
            "step_val": 0,
        },
        {
            "func": "RBDY2_SetInvisible",
            "args": "3",
            "step_mode": "after",
        },
    ])

    loop_start = script.index("for k in range(nb_steps):")
    assert script.index("chipy.RBDY2_SetVisible(1)") < loop_start
    assert "    chipy.SetThetaIntegrator(theta)\n" in script
    assert "if k % 3 == 0:\n        chipy.RBDY2_SetInvisible(2)" in script
    assert "if k == 0:\n        chipy.SetTimeStep(dt * 0.5)" in script
    assert "\nchipy.RBDY2_SetInvisible(3)\n" in script
    assert script.index("\nchipy.RBDY2_SetInvisible(3)\n") > loop_start
    ast.parse(script)


@pytest.mark.parametrize(
    "entry, message",
    [
        (
            {"func": "SetTimeStep", "args": "dt; chipy.SetTimeStep(0)"},
            "invalid Python arguments",
        ),
        (
            {"func": "SetTimeStep; chipy.SetTimeStep", "args": "dt"},
            "valid chipy function name",
        ),
        (
            {"func": "SetTimeStep", "args": "dt", "step_mode": "unknown"},
            "invalid step mode",
        ),
    ],
)
def test_invalid_set_actions_fail_with_a_clear_error(entry, message):
    with pytest.raises(ValueError, match=message):
        _generate([entry])
