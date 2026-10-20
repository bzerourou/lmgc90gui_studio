from lmgc90_core import Project
from lmgc90_core.compute_script import ComputeScriptGenerator


def _generate(dim: int, *, write_out_dof: bool) -> str:
    project = Project(name="advanced_output", dimension=dim)
    params = {
        "use_RBDY2": dim == 2,
        "use_RBDY3": dim == 3,
        "advanced_write_out_dof": write_out_dof,
    }
    return ComputeScriptGenerator(project).generate_string(params)


def test_write_out_dof_is_not_generated_when_disabled():
    for dim in (2, 3):
        script = _generate(dim, write_out_dof=False)
        assert "chipy.WriteOut(freq_write)" in script
        assert "chipy.RBDY2_WriteOutDof(freq_write)" not in script
        assert "chipy.RBDY3_WriteOutDof(freq_write)" not in script


def test_write_out_dof_is_generated_only_for_the_active_rigid_body_dimension():
    script_2d = _generate(2, write_out_dof=True)
    assert "chipy.RBDY2_WriteOutDof(freq_write)" in script_2d
    assert "chipy.RBDY3_WriteOutDof(freq_write)" not in script_2d

    script_3d = _generate(3, write_out_dof=True)
    assert "chipy.RBDY3_WriteOutDof(freq_write)" in script_3d
    assert "chipy.RBDY2_WriteOutDof(freq_write)" not in script_3d


def test_advanced_routine_options_are_emitted_when_enabled():
    project = Project(name="advanced_options", dimension=3)
    params = {
        "deformable": True,
        "physics": "THMx",
        "use_RBDY3": True,
        "use_mecaMAILx": True,
        "use_therMAILx": True,
        "use_poroMAILx": True,
        "advanced_assemble_mechanical": True,
        "advanced_assemble_thermal": True,
        "advanced_assemble_poro": True,
        "advanced_assemble_multi": True,
        "advanced_fd_select_prox": True,
        "advanced_compute_rnod": True,
        "advanced_fatal_damping": True,
        "advanced_smooth_force": True,
        "advanced_display_out_dof": True,
        "advanced_display_out_rnod": True,
        "advanced_display_out_vloc_rloc": True,
        "advanced_display_prox_tactors": True,
        "advanced_hdf5": True,
        "advanced_hdf5_filename": "results.h5",
        "advanced_write_out_dof": True,
        "advanced_write_out_gpv": True,
        "advanced_write_out_mp_values": True,
        "advanced_write_out_rnod": True,
        "advanced_write_out_vloc_rloc": True,
        "advanced_write_last": True,
        "advanced_write_last_dof": True,
        "advanced_write_last_gpv": True,
        "advanced_write_last_mp_values": True,
        "advanced_write_last_rnod": True,
        "advanced_write_last_vloc_rloc": True,
        "advanced_add_dof2": True,
        "advanced_write_bodies": True,
        "advanced_write_behaviours": True,
        "advanced_write_driven_dof": True,
        "advanced_write_mp_behaviours": True,
        "advanced_add_registers_to_display": True,
        "advanced_circular_selection": True,
        "advanced_circular_selection_args": "1.0, 2.0, 3.0",
        "advanced_set_contact_radius": True,
        "advanced_set_contact_radius_args": "0.02",
        "advanced_set_domain_boundary": True,
        "advanced_set_domain_boundary_args": "Xmin=-1.0, Xmax=1.0",
        "advanced_set_number_interaction": True,
        "advanced_set_number_interaction_args": "4",
        "advanced_set_periodic_condition": True,
        "advanced_set_periodic_condition_args": "xperiod=1.0",
    }
    script = ComputeScriptGenerator(project).generate_string(params)

    expected_calls = (
        "chipy.AssembleMechanicalLHS()",
        "chipy.AssembleMechanicalRHS()",
        "chipy.AssembleThermalLHS()",
        "chipy.AssembleThermalRHS()",
        "chipy.AssemblePoroLHS()",
        "chipy.AssemblePoroRHS()",
        "chipy.AssembleMultiLHS()",
        "chipy.AssembleMultiRHS()",
        "chipy.FdSelectProxTactors()",
        "chipy.ComputeRnod()",
        "chipy.RBDY3_FatalDamping()",
        "chipy.SmoothForceComputation()",
        "chipy.DisplayProxTactors()",
        "chipy.DisplayOutDof()",
        "chipy.DisplayOutRnod()",
        "chipy.DisplayOutVlocRloc()",
        "chipy.InitHDF5('results.h5')",
        "chipy.WriteHDF5()",
        "chipy.RBDY3_WriteOutDof(freq_write)",
        "chipy.WriteOutGPV(freq_write)",
        "chipy.WriteOutMpValues(freq_write)",
        "chipy.WriteOutRnod(freq_write)",
        "chipy.WriteOutVlocRloc(freq_write)",
        "chipy.WriteLast()",
        "chipy.WriteLastDof()",
        "chipy.WriteLastGPV()",
        "chipy.WriteLastMpValues()",
        "chipy.WriteLastRnod()",
        "chipy.WriteLastVlocRloc()",
        "chipy.AddDof2InBodies()",
        "chipy.WriteBodies()",
        "chipy.WriteBehaviours()",
        "chipy.WriteDrivenDof()",
        "chipy.WriteMpBehaviours()",
        "chipy.addRegistersToDisplay()",
        "chipy.CircularSelection(1.0, 2.0, 3.0)",
        "chipy.SetContactRadius(0.02)",
        "chipy.SetDomainBoundary(Xmin=-1.0, Xmax=1.0)",
        "chipy.SetNumberInteractionByContact(4)",
        "chipy.SetPeriodicCondition(xperiod=1.0)",
    )
    for call in expected_calls:
        assert call in script


def test_advanced_calls_are_absent_by_default():
    script = _generate(3, write_out_dof=False)
    for call in (
        "chipy.FdSelectProxTactors()",
        "chipy.ComputeRnod()",
        "chipy.RBDY3_FatalDamping()",
        "chipy.SmoothForceComputation()",
        "chipy.DisplayProxTactors()",
        "chipy.WriteOutGPV(freq_write)",
        "chipy.WriteLast()",
        "chipy.InitHDF5(",
        "chipy.CircularSelection(",
        "chipy.SetContactRadius(",
        "chipy.addRegistersToDisplay()",
    ):
        assert call not in script


def test_prox_tactors_are_selected_once_per_step_with_fallback_or_detector():
    project = Project(name="prox_selection", dimension=3)
    base_params = {
        "use_RBDY2": False,
        "use_RBDY3": True,
        "use_DKDKx": False,
        "use_SPSPx": False,
        "use_SPPLx": False,
    }

    fallback_script = ComputeScriptGenerator(project).generate_string(base_params)
    assert fallback_script.count("chipy.SelectProxTactors()") == 1

    detector_script = ComputeScriptGenerator(project).generate_string({
        **base_params,
        "use_SPSPx": True,
    })
    assert detector_script.count("chipy.SelectProxTactors()") == 0
    assert detector_script.count("chipy.SPSPx_SelectProxTactors()") == 1
