# ============================================================================
# compute_script.py — lmgc90_core
# ============================================================================
"""Full chipy ``command.py`` generator (no Qt, no engine).

Pure function of ``Project`` + parameter dict (Compute / ChipyRoutines options).
GUI and engine call this via ``emit_chipy`` / ``generate_command_script``.
"""
from __future__ import annotations

import ast
import keyword
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from .project import Project


_CONTACT_ROUTINE_BY_PAIR = {
    ("DISKx", "DISKx"): "DKDKx",
    ("DISKx", "JONCx"): "DKJCx",
    ("JONCx", "DISKx"): "DKJCx",
    ("DISKx", "xKSID"): "DKKDx",
    ("xKSID", "DISKx"): "DKKDx",
    ("DISKx", "POLYG"): "DKKDx",
    ("POLYG", "DISKx"): "DKKDx",
    ("POLYG", "POLYG"): "PLPLx",
    ("CLxxx", "ALpxx"): "CLALp",
    ("ALpxx", "CLxxx"): "CLALp",
    ("ALpxx", "ALpxx"): "ALpALp",
    ("SPHER", "SPHER"): "SPSPx",
    ("SPHER", "CYLND"): "SPCDx",
    ("CYLND", "SPHER"): "SPCDx",
    ("SPHER", "PLANx"): "SPPLx",
    ("PLANx", "SPHER"): "SPPLx",
    ("CYLND", "CYLND"): "CDCDx",
    ("CYLND", "PLANx"): "CDPLx",
    ("PLANx", "CYLND"): "CDPLx",
    ("POLYR", "POLYR"): "PRPRx",
}
_CONTACT_ROUTINE_KEYS = (
    "DKDKx", "DKJCx", "DKKDx", "PLPLx", "CLALp", "ALpALp",
    "SPSPx", "SPCDx", "SPPLx", "CDCDx", "CDPLx", "PRPRx",
    "DKMECAx", "ALpMECAx", "SPMECAx", "PT2Dx", "PT3Dx", "NODES",
)


def _format_set_action_call(entry: dict, index: int) -> str:
    """Validate and format one user-configured chipy SET call."""
    func = str(entry.get('func', '')).strip()
    args = str(entry.get('args', '')).strip()
    if (
        not func
        or not func.isidentifier()
        or keyword.iskeyword(func)
        or 'Set' not in func
    ):
        raise ValueError(
            f"SET action {index}: expected a valid chipy function name containing 'Set'."
        )
    mode = entry.get('step_mode', 'before')
    if mode not in ('before', 'all', 'every_n', 'at_k', 'after'):
        raise ValueError(f"SET action {index} ({func}): invalid step mode {mode!r}.")
    if mode in ('every_n', 'at_k'):
        try:
            step_value = int(entry.get('step_val', 1))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"SET action {index} ({func}): step value must be an integer."
            ) from exc
        minimum = 0 if mode == 'at_k' else 1
        if step_value < minimum:
            raise ValueError(
                f"SET action {index} ({func}): step value must be at least {minimum}."
            )
    try:
        ast.parse(f'chipy.{func}({args})', mode='eval')
    except SyntaxError as exc:
        raise ValueError(
            f"SET action {index} ({func}): invalid Python arguments: {exc.msg}."
        ) from exc
    return f'chipy.{func}({args})'


def infer_chipy_contact_routines(project: Project) -> dict[str, bool]:
    """Infer rigid-body and contact detector defaults from dimension/see-tables."""
    dim = int(project.dimension)
    routines = {f"use_{name}": False for name in _CONTACT_ROUTINE_KEYS}
    routines["use_RBDY2"] = dim == 2
    routines["use_RBDY3"] = dim == 3
    if dim == 2 and not project.visibility:
        routines["use_DKDKx"] = True

    for rule in project.visibility:
        pair = (rule.candidate_contactor, rule.antagonist_contactor)
        detector = _CONTACT_ROUTINE_BY_PAIR.get(pair)
        if detector is not None:
            routines[f"use_{detector}"] = True
        for shape in pair:
            if shape == "PT2Dx" and dim == 2:
                routines["use_PT2Dx"] = True
            elif shape == "PT3Dx" and dim == 3:
                routines["use_PT3Dx"] = True
    return routines


class _JournalLike(Protocol):
    def warning(self, msg: str) -> None: ...


class ComputeScriptGenerator:
    """Genere le script command.py pour chipy."""

    _DEFAULTS: Dict[str, Any] = {
        'mhyp': 1, 'deformable': False, 'physics': 'MECAx',
        'Rloc_tol': 5e-2,
        'use_RBDY2': True,  'use_RBDY3': False,
        'use_DKDKx': True,  'use_DKJCx': False, 'use_DKKDx': False,
        'use_PLPLx': False, 'use_CLALp': False,  'use_ALpALp': False,
        'use_SPSPx': False, 'use_SPCDx': False,  'use_SPPLx': False,
        'use_CDCDx': False, 'use_CDPLx': False,  'use_PRPRx': False,
        'use_mecaMAILx': False, 'use_therMAILx': False, 'use_poroMAILx': False,
        'use_DKMECAx': False, 'use_ALpMECAx': False, 'use_SPMECAx': False,
        'use_PT2Dx': False,   'use_PT3Dx': False,
        'use_NODES': False,   'use_bulk_behav': False,
        'advanced_assemble_mechanical': False,
        'advanced_assemble_thermal': False,
        'advanced_assemble_poro': False,
        'advanced_assemble_multi': False,
        'advanced_fd_select_prox': False,
        'advanced_compute_rnod': False,
        'advanced_fatal_damping': False,
        'advanced_smooth_force': False,
        'advanced_display_out_dof': False,
        'advanced_display_out_rnod': False,
        'advanced_display_out_vloc_rloc': False,
        'advanced_display_prox_tactors': False,
        'advanced_hdf5': False,
        'advanced_add_dof2': False,
        'advanced_write_out_dof': False,
        'advanced_write_out_gpv': False,
        'advanced_write_out_mp_values': False,
        'advanced_write_out_rnod': False,
        'advanced_write_out_vloc_rloc': False,
        'advanced_write_last': False,
        'advanced_write_last_dof': False,
        'advanced_write_last_gpv': False,
        'advanced_write_last_mp_values': False,
        'advanced_write_last_rnod': False,
        'advanced_write_last_vloc_rloc': False,
        'advanced_write_behaviours': False,
        'advanced_write_bodies': False,
        'advanced_write_driven_dof': False,
        'advanced_write_mp_behaviours': False,
        'advanced_add_registers_to_display': False,
        'advanced_circular_selection': False,
        'advanced_set_contact_radius': False,
        'advanced_set_domain_boundary': False,
        'advanced_set_number_interaction': False,
        'advanced_set_periodic_condition': False,
        'advanced_hdf5_filename': 'command.h5',
        'advanced_circular_selection_args': '0.0, 0.0, 1.0',
        'advanced_set_contact_radius_args': '',
        'advanced_set_domain_boundary_args': '',
        'advanced_set_number_interaction_args': '',
        'advanced_set_periodic_condition_args': '',
        'visu_RBDY2': True,  'visu_RBDY3': False,
        'visu_mecaMAIL': False, 'visu_therMAIL': False, 'visu_poroMAIL': False,
        'display_in_loop': True,
        'extract_Rnod': False, 'extract_Vloc': False, 'extract_Rloc': False,
        'extract_energy': False, 'extract_KE': False,
        'extract_fields': False, 'extract_internal': False,
        'vis_entries': [],
        'gbv2_entries': [],
        'gbv3_entries': [],
        'insp2d_entries': [],
        'insp3d_entries': [],
        'inspi_entries':  [],
        'set_entries': [],
        'use_restart': False, 'restart_step': 0,
        'use_stop_crit': False, 'stop_crit_type': 'energy',
        'stop_crit_val': 1e-6, 'stop_crit_freq': 10,
        'use_multi_step': False, 'multi_step_nb': 3,
        'multi_step_sizes': '1e-3, 1e-4, 1e-5',
        'dt': 1e-3, 'nb_steps': 1000, 'theta': 0.5,
        'tol': 1.666e-4, 'relax': 1.0, 'norm': 'Quad ',
        'gs_it1': 50, 'gs_it2': 1000,
        'solver_type': 'Stored_Delassus_Loops         ',
        'freq_write': 50, 'freq_display': 50,
        'disable_log': False,
    }

    _NO_ID_FUNCS = frozenset({
        'RBDY2_GetNbRBDY2', 'RBDY3_GetNbRBDY3',
        'RBDY2_KineticEnergy',
        'DISKx_GetNbDISKx', 'JONCx_GetNbJONCx',
        'POLYR_GetNbPOLYR', 'xKSID_GetNbxKSID',
        'SPHER_GetNbSPHER', 'POLYH_GetNbPOLYH',
        'CYLND_GetNbCYLND', 'PLANE_GetNbPLANE',
        'PT2Dx_GetNbPT2Dx', 'PT3Dx_GetNbPT3Dx',
        'DKDKx_GetNbDKDKx', 'DKJCx_GetNbDKJCx',
        'DKKDx_GetNbDKKDx', 'PLPLx_GetNbPLPLx',
        'CLALp_GetNbCLALp', 'ALpALp_GetNbALpALp',
        'SPSPx_GetNbSPSPx', 'SPCDx_GetNbSPCDx',
        'SPPLx_GetNbSPPLx', 'CDCDx_GetNbCDCDx',
        'CDPLx_GetNbCDPLx', 'PRPRx_GetNbPRPRx',
        'DKMECAx_GetNbDKMECAx', 'ALpMECAx_GetNbALpMECAx',
        'SPMECAx_GetNbSPMECAx',
    })

    def __init__(
        self,
        project: Project,
        *,
        journal: Optional[_JournalLike] = None,
    ):
        if project is None:
            raise TypeError("ComputeScriptGenerator requires a Project")
        self.project = project
        self.journal = journal

    # =========================================================================
    # API publique
    # =========================================================================

    def generate(self, output_path: Path, params: Dict[str, Any]) -> None:
        """Ecrit command.py dans output_path."""
        output_path.write_text(self.generate_string(params), encoding='utf-8')

    def generate_string(self, params: Dict[str, Any]) -> str:
        """Retourne le script complet sous forme de chaine."""
        p   = {**self._DEFAULTS, **params}
        for current, legacy in (
            ('use_mecaMAILx', 'use_mecaMAIL'),
            ('use_therMAILx', 'use_therMAIL'),
            ('use_poroMAILx', 'use_poroMAIL'),
        ):
            if current not in params and legacy in params:
                p[current] = params[legacy]
        for index, entry in enumerate(p.get('set_entries', []), start=1):
            _format_set_action_call(entry, index)
        if "mhyp" not in params and int(self.project.dimension) == 3:
            p["mhyp"] = 3
        for key, value in infer_chipy_contact_routines(self.project).items():
            if key not in params:
                p[key] = value
        buf = StringIO()
        w   = buf.write

        self._unresolved_group_refs = {}

        # ── Factories ─────────────────────────────────────────────────────────
        # Les indices corps sont lus depuis body_collection.pkl (genere par
        # le script pre.py au moment de bodies.addAvatar), sur le modele
        # exemples/box_generation.py / box_simulation.py.
        _factory_active = []  # ParticleFactory optional — skipped in studio


        dim        = int(getattr(self.project, "dimension", 2) or 2)
        deformable = p['deformable']
        mhyp       = p['mhyp']

        use_RBDY2   = p['use_RBDY2']   and dim == 2
        use_RBDY3   = p['use_RBDY3']   and dim == 3
        use_mecaMAILx = p['use_mecaMAILx'] and deformable
        use_therMAILx = p['use_therMAILx'] and deformable
        use_poroMAILx = p['use_poroMAILx'] and deformable
        any_MAILx     = use_mecaMAILx or use_therMAILx or use_poroMAILx

        tacts_2d = [t for t in ('DKDKx','DKJCx','DKKDx','PLPLx','CLALp','ALpALp')
                    if dim == 2 and p.get(f'use_{t}')]
        tacts_3d = [t for t in ('SPSPx','SPCDx','SPPLx','CDCDx','CDPLx','PRPRx')
                    if dim == 3 and p.get(f'use_{t}')]
        tacts_mix = [
            t for t in ('DKMECAx','ALpMECAx','SPMECAx')
            if p.get(f'use_{t}') and (
                (dim == 2 and t in ('DKMECAx', 'ALpMECAx'))
                or (dim == 3 and t == 'SPMECAx')
            )
        ]
        tacts_pt = [
            t for t in ('PT2Dx','PT3Dx','NODES')
            if p.get(f'use_{t}') and (
                t == 'NODES' or (dim == 2 and t == 'PT2Dx')
                or (dim == 3 and t == 'PT3Dx')
            )
        ]
        all_tacts = tacts_2d + tacts_3d + tacts_mix + tacts_pt

        use_multi   = p.get('use_multi_step', False)
        use_restart = p.get('use_restart', False)
        use_stop    = p.get('use_stop_crit', False)

        # Prefixe RBDY selon la dimension du projet (utilise pour les factories)
        _rbdy_prefix = 'RBDY2' if dim == 2 else 'RBDY3'

        # ── 1. En-tete ────────────────────────────────────────────────────────
        w('# -*- coding: utf-8 -*-\n')
        w('# Script de calcul genere automatiquement par LMGC90_GUI\n')
        w(f'# Projet    : {getattr(self.project, "name", "?")!r}\n')
        w(f'# Dimension : {dim}D\n')
        if _factory_active:
            w('#\n')
            w('# Particle Factories : indices corps via body_collection.pkl\n')
            w('# (genere par le script pre.py — cf. exemples/box_simulation.py)\n')
        w('\n')
        w('from pylmgc90 import chipy\n')
        if use_stop:
            w('import math\n')
        w('\n')

        # ── 2. Initialisation ─────────────────────────────────────────────────
        w('chipy.Initialize()\n')
        w('chipy.checkDirectories()\n')
        if p.get('disable_log'):
            w('chipy.utilities_DisableLogMes()\n')
        w('\n')

        # ── 3. Parametres ─────────────────────────────────────────────────────
        w('# ── Parametres generaux ──────────────────────────────────────\n')
        w(f'dim    = {dim}\n')
        w(f'mhyp   = {mhyp}\n')
        w('\n')
        w(f'dt          = {p["dt"]!r}\n')
        w(f'nb_steps    = {p["nb_steps"]}\n')
        w(f'theta       = {p["theta"]!r}\n')
        w('\n')
        w(f'Rloc_tol    = {p["Rloc_tol"]!r}\n')
        w('\n')
        w(f'tol         = {p["tol"]!r}\n')
        w(f'relax       = {p["relax"]!r}\n')
        w(f'norm        = {p["norm"]!r}\n')
        w(f'gs_it1      = {p["gs_it1"]}\n')
        w(f'gs_it2      = {p["gs_it2"]}\n')
        w(f'solver_type = {p["solver_type"]!r}\n')
        w('\n')
        w(f'freq_write   = {p["freq_write"]}\n')
        w(f'freq_display = {p["freq_display"]}\n')
        w('\n')

        if use_multi:
            sizes_str = p.get('multi_step_sizes', '1e-3')
            nb_phases  = p.get('multi_step_nb', 3)
            w('# Multi-pas : sequence de pas de temps\n')
            w(f'dt_sequence      = [{sizes_str}]\n')
            w(f'steps_per_phase  = nb_steps // {nb_phases}\n')
            w('\n')

        if use_stop:
            w("# Critere d'arret\n")
            w(f'stop_tol  = {p["stop_crit_val"]!r}\n')
            w(f'stop_freq = {p["stop_crit_freq"]}\n')
            w('\n')

        # ── 4. Configuration chipy ────────────────────────────────────────────
        w('# ── Configuration ───────────────────────────────────────────\n')
        w('chipy.SetDimension(dim, mhyp)\n')
        w("chipy.utilities_logMes('INIT TIME STEPPING')\n")
        w('chipy.TimeEvolution_SetTimeStep(dt)\n')
        w('chipy.Integrator_InitTheta(theta)\n')
        w('\n')
        w(f'chipy.ReadDatbox(deformable={deformable})\n')
        w('\n')

        for option, func, argument_key in (
            ('advanced_set_contact_radius', 'SetContactRadius',
             'advanced_set_contact_radius_args'),
            ('advanced_set_domain_boundary', 'SetDomainBoundary',
             'advanced_set_domain_boundary_args'),
            ('advanced_set_number_interaction', 'SetNumberInteractionByContact',
             'advanced_set_number_interaction_args'),
            ('advanced_set_periodic_condition', 'SetPeriodicCondition',
             'advanced_set_periodic_condition_args'),
        ):
            if p.get(option):
                args = str(p.get(argument_key, '')).strip()
                w(_format_set_action_call(
                    {'func': func, 'args': args}, option
                ) + '\n')

        if p.get('advanced_circular_selection'):
            args = str(p.get('advanced_circular_selection_args', '')).strip()
            try:
                ast.parse(f'chipy.CircularSelection({args})', mode='eval')
            except SyntaxError as exc:
                raise ValueError(
                    f"CircularSelection: invalid Python arguments: {exc.msg}."
                ) from exc
            w(f'chipy.CircularSelection({args})\n')

        if p.get('disable_log'):
            w('chipy.utilities_DisableLogMes()\n')
            w('\n')

        # ── 5. Ouverture fichiers sortie ──────────────────────────────────────
        w("chipy.utilities_logMes('DISPLAY & WRITE')\n")
        if p.get('advanced_add_registers_to_display'):
            w('chipy.addRegistersToDisplay()\n')
        if p.get('advanced_hdf5'):
            filename = str(p.get('advanced_hdf5_filename', '')).strip()
            if not filename:
                raise ValueError("HDF5 output requires a non-empty filename.")
            w(f'chipy.InitHDF5({filename!r})\n')
        w('chipy.OpenDisplayFiles()\n')
        w('chipy.OpenPostproFiles()\n')
        w('\n')

        # ── 6. Masse ──────────────────────────────────────────────────────────
        w("chipy.utilities_logMes('COMPUTE MASS')\n")
        w('chipy.ComputeMass()\n')
        if use_mecaMAILx:
            w('chipy.mecaMAILx_ComputeMass()\n')
        if use_therMAILx:
            w('chipy.therMAILx_ComputeMass()\n')
        if use_poroMAILx:
            w('chipy.poroMAILx_ComputeMass()\n')
        w('\n')

        # ── Helpers locaux ────────────────────────────────────────────────────

        def _resolve_group_ids(grp_name: str):
            """
            Retourne les numéros de corps LMGC90 (1-based, en chaînes) pour
            les avatars du groupe donné.

            Deux stratégies selon l'origine de l'avatar :
            - Avatar NORMAL  → position dans state.avatars + 1
            - Avatar FACTORY → body_index_start + i depuis FactoryConfig
              (les parois de conteneur décalent les indices, l'index de position
              serait faux ; seul body_collection.pkl / FactoryConfig est fiable)
            """
            if not grp_name or self.project is None:
                return []
            groups = getattr(self.project, "avatar_groups", None) or {}
            avatar_ids = groups.get(grp_name, [])
            if not avatar_ids:
                return []

            factory_body_map: dict = {}
            # ParticleFactory optional — body indices from avatar order in Project

            id_to_idx = {
                av.avatar_id: i for i, av in enumerate(self.project.avatars)
            }

            result = []
            missing = []
            for aid in avatar_ids:
                if aid in factory_body_map:
                    # Numéro exact depuis FactoryConfig
                    result.append(str(factory_body_map[aid]))
                elif aid in id_to_idx:
                    # Position dans state.avatars + 1 (correct pour non-factory)
                    result.append(str(id_to_idx[aid] + 1))
                else:
                    missing.append(aid)
            if missing:
                msg = (
                    f"Groupe '{grp_name}' : {len(missing)} avatar_id introuvable(s) — "
                    f"ignoré(s) (résolu={len(result)}/{len(avatar_ids)}). "
                    f"IDs: {', '.join(m[:8] + '…' for m in missing[:10])}"
                )
                if self.journal is not None:
                    self.journal.warning(msg)
                else:
                    print("WARNING:", msg)
                self._unresolved_group_refs = getattr(self, '_unresolved_group_refs', {})
                self._unresolved_group_refs[grp_name] = list(missing)
            return result

        def _normalize_mode(entry: dict) -> str:
            """
            Normalise step_mode vers une des 5 valeurs :
              "before" | "all" | "every_n" | "at_k" | "after"

            Compat ascendante :
              - step_mode absent + in_loop=False  → "after"
              - step_mode absent + freq > 1       → "every_n"
              - step_mode absent / vide           → "before"  (ancien comportement vis)
              - sinon                             → valeur brute
            """
            mode = entry.get('step_mode', None)
            if mode is None or mode == '':
                if 'step_mode' not in entry:
                    if not entry.get('in_loop', True):
                        return 'after'
                    if entry.get('freq', 1) > 1:
                        return 'every_n'
                # Ancien cas vis (step_mode vide) ou défaut prudent
                return 'before'
            return mode

        def _timing_guard(entry: dict):
            """
            Retourne (ligne_if, indentation_corps) pour les modes dans la boucle.
            - every_n : if k % N == 0
            - at_k    : if k == k_val
            - all     : pas de garde (appel à chaque pas)
            - before / after : ne devraient pas arriver ici
            """
            mode = _normalize_mode(entry)
            val = int(entry.get('step_val', entry.get('freq', 1)))
            if mode == 'every_n' and val > 1:
                return ind + 'if k % {} == 0:\n'.format(val), ind + '    '
            if mode == 'at_k':
                return ind + 'if k == {}:\n'.format(val), ind + '    '
            return '', ind

        def _emit_set_action(entry: dict, index: int, prefix: str) -> None:
            """Emit a SET call, optionally once per selected avatar."""
            func = str(entry.get('func', '')).strip()
            args = str(entry.get('args', entry.get('ids', ''))).strip()
            ids_str = str(entry.get('ids', '')).strip()
            group = str(entry.get('group', '')).strip()
            store = str(entry.get('store', '')).strip()

            if store and (
                not store.isidentifier() or keyword.iskeyword(store)
            ):
                raise ValueError(
                    f"SET action {index} ({func}): invalid Python variable name {store!r}."
                )

            if group:
                target_ids = _resolve_group_ids(group)
            elif ids_str and all(
                token.strip().isdigit() for token in ids_str.split(',')
            ):
                target_ids = [
                    token.strip() for token in ids_str.split(',') if token.strip()
                ]
            else:
                target_ids = []

            if target_ids:
                call_args = args if group and '_id' in args else '_id'
                call = _format_set_action_call(
                    {**entry, 'func': func, 'args': call_args}, index
                )
                w(prefix + 'for _id in [{}]:\n'.format(', '.join(target_ids)))
                assignment = '{} = {}'.format(store, call) if store else call
                w(prefix + '    ' + assignment + '\n')
                return

            call = _format_set_action_call(
                {**entry, 'func': func, 'args': args}, index
            )
            w(prefix + ('{} = '.format(store) if store else '') + call + '\n')

        def _is_no_id_func(func_name: str) -> bool:
            if func_name in self._NO_ID_FUNCS:
                return True
            if 'GetNb' in func_name:
                return True
            return False

        def _write_vis_before(entry: dict) -> None:
            action   = entry.get('action', 'visible')
            edim     = entry.get('dim', '2D')
            ids_str  = entry.get('ids', '').strip()
            grp_name = entry.get('group', '').strip()
            id_list  = (
                [t.strip() for t in ids_str.split(',') if t.strip().isdigit()]
                if ids_str else _resolve_group_ids(grp_name)
            )
            suffix = '_SetVisible' if action == 'visible' else '_SetInvisible'
            func   = ('RBDY2' if edim == '2D' else 'RBDY3') + suffix
            for av_id in id_list:
                w('chipy.{}({})\n'.format(func, av_id))

        def _emit_vis_entry(entry: dict, in_loop_context: bool = False) -> None:
            action   = entry.get('action', 'visible')
            edim     = entry.get('dim', '2D')
            ids_str  = entry.get('ids', '').strip()
            grp_name = entry.get('group', '').strip()
            if ids_str:
                id_list = [t.strip() for t in ids_str.split(',') if t.strip().isdigit()]
            elif grp_name:
                id_list = _resolve_group_ids(grp_name)
            else:
                return
            suffix = '_SetVisible' if action == 'visible' else '_SetInvisible'
            func   = ('RBDY2' if edim == '2D' else 'RBDY3') + suffix
            if in_loop_context:
                guard, xi = _timing_guard(entry)
                if guard:
                    w(guard)
                    for av_id in id_list:
                        w(xi + 'chipy.{}({})\n'.format(func, av_id))
                else:
                    for av_id in id_list:
                        w(ind + 'chipy.{}({})\n'.format(func, av_id))
            else:
                for av_id in id_list:
                    w('chipy.{}({})\n'.format(func, av_id))

        def _emit_gbv(entry: dict, func_name: str) -> None:
            vec     = entry.get('vec', 'Coor_')
            ids_str = entry.get('ids', '').strip()
            grp     = entry.get('group', '').strip()
            id_list = (
                [t.strip() for t in ids_str.split(',') if t.strip().isdigit()]
                if ids_str else _resolve_group_ids(grp)
            )
            if not id_list:
                return
            ids_repr = '[{}]'.format(', '.join(id_list))
            guard, xi = _timing_guard(entry)
            if guard:
                w(guard)
                w(xi + 'for _id in {}:\n'.format(ids_repr))
                w(xi + "    chipy.{}('{}', _id)\n".format(func_name, vec))
            else:
                w(xi + 'for _id in {}:\n'.format(ids_repr))
                w(xi + "    chipy.{}('{}', _id)\n".format(func_name, vec))
            w('\n')

        def _emit_insp(entry: dict) -> None:
            func    = entry.get('func', '')
            ids_str = entry.get('ids', '').strip()
            grp     = entry.get('group', '').strip()
            store   = entry.get('store', '').strip()
            if not func:
                return
            no_id = _is_no_id_func(func) or (not ids_str and not grp)
            guard, extra_ind = _timing_guard(entry)
            if no_id:
                call_str = 'chipy.{}()'.format(func)
                line     = '{} = {}'.format(store, call_str) if store else call_str
                if guard:
                    w(guard)
                    w(extra_ind + line + '\n')
                else:
                    w(ind + line + '\n')
            else:
                id_list = (
                    [t.strip() for t in ids_str.split(',') if t.strip().isdigit()]
                    if ids_str else _resolve_group_ids(grp)
                )
                if not id_list:
                    return
                ids_repr = '[{}]'.format(', '.join(id_list))
                inner = (
                    '    {}_{{_id}} = chipy.{}(_id)\n'.format(store, func)
                    if store
                    else '    chipy.{}(_id)\n'.format(func)
                )
                if guard:
                    w(guard)
                    w(extra_ind + 'for _id in {}:\n'.format(ids_repr))
                    w(extra_ind + '    ' + inner.lstrip())
                else:
                    w(ind + 'for _id in {}:\n'.format(ids_repr))
                    w(ind + inner)
            w('\n')

        def _is_in_loop(e: dict) -> bool:
            """True si l'entrée doit être émise à l'intérieur de la boucle for k."""
            return _normalize_mode(e) in ('all', 'every_n', 'at_k')

        def _is_before(e: dict) -> bool:
            """True si l'entrée doit être émise une seule fois avant la boucle."""
            return _normalize_mode(e) == 'before'

        def _is_after(e: dict) -> bool:
            """True si l'entrée doit être émise une seule fois après la boucle."""
            return _normalize_mode(e) == 'after'

        # ── 6b. Visibilite des avatars avant la boucle ────────────────────────
        # "before" (ou ancien step_mode vide) → une seule fois avant for k
        # "all" / "every_n" / "at_k"          → dans la boucle
        # "after"                            → après la boucle
        _vis_before  = [e for e in p.get('vis_entries', []) if _is_before(e)]
        _vis_in_loop = [e for e in p.get('vis_entries', []) if _is_in_loop(e)]
        _vis_after   = [e for e in p.get('vis_entries', []) if _is_after(e)]

        for _ve in _vis_before:
            _write_vis_before(_ve)
        if _vis_before:
            w('\n')

        # ── 6c. Particle Factories : pickle + invisibilite + planning ───────────
        #
        # Pattern box_simulation.py :
        #   1. Charger body_collection.pkl (ecrit par pre.py apres addAvatar)
        #   2. SetInvisible sur tous les corps factory
        #   3. Construire _factory_schedule = {k: [ids]} depuis les vagues
        #   4. Dans la boucle : SetVisible aux pas planifies
        #
        if _factory_active:
            w('# ============================================================\n')
            w('# Particle Factories — body_collection.pkl\n')
            w('# ============================================================\n')
            w('import pickle\n')
            w('import os\n')
            w(f"_pkl_path = '{BODY_COLLECTION_PICKLE}'\n")
            w("if not os.path.isfile(_pkl_path):\n")
            w("    raise FileNotFoundError(\n")
            w(f"        f\"Fichier '{{_pkl_path}}' introuvable. \"\n")
            w("        \"Executez d'abord le script pre.py (generation DATBOX) \"\n")
            w("        \"pour creer body_collection.pkl.\")\n")
            w("with open(_pkl_path, 'rb') as _pkl_f:\n")
            w("    body_collection = pickle.load(_pkl_f)\n")
            w("print('Charge', _pkl_path, '—', body_collection.get('total_nb_bodies', '?'), 'corps')\n")
            w('\n')

            w('# Masquer toutes les particules de factory au depart\n')
            w("for _fcfg in body_collection.get('factories', {}).values():\n")
            w("    if not _fcfg.get('enabled', True):\n")
            w("        continue\n")
            w(f"    for _bnum in _fcfg['body_numbers']:\n")
            w(f"        chipy.{_rbdy_prefix}_SetInvisible(_bnum)\n")
            w('\n')

            w("# Planning d'activation : {k: [ids_corps_a_rendre_visibles]}\n")
            w('_factory_schedule: dict = {}\n')
            w("for _fname, _fcfg in body_collection.get('factories', {}).items():\n")
            w("    if not _fcfg.get('enabled', True):\n")
            w("        continue\n")
            w("    _nums = _fcfg['body_numbers']\n")
            w("    _bs   = _fcfg['batch_size']\n")
            w("    _ss   = _fcfg['start_step']\n")
            w("    _iv   = _fcfg['interval_steps']\n")
            w("    _nb   = (len(_nums) + _bs - 1) // _bs\n")
            w("    for _bi in range(_nb):\n")
            w("        _k = _ss + _bi * _iv\n")
            w("        _batch = _nums[_bi * _bs : (_bi + 1) * _bs]\n")
            w("        _factory_schedule.setdefault(_k, []).extend(_batch)\n")
            w('\n')

        # ── 7. Restart ────────────────────────────────────────────────────────
        if use_restart:
            w('# ── Restart ─────────────────────────────────────────────\n')
            w('chipy.ReadIni()\n')
            w(f'chipy.SetStep({p["restart_step"]})\n')
            w('\n')

        # ── 7b. GBV / Inspection avant la boucle (step_mode="before") ─────────
        # Émis après un éventuel restart pour lire l'état initial chargé.
        def _emit_insp_outside(entry: dict) -> None:
            """Émet un appel d'inspection hors boucle (before ou after)."""
            func    = entry.get('func', '')
            ids_str = entry.get('ids', '').strip()
            grp     = entry.get('group', '').strip()
            store   = entry.get('store', '').strip()
            if not func:
                return
            if _is_no_id_func(func) or (not ids_str and not grp):
                if store:
                    w('{} = chipy.{}()\n'.format(store, func))
                else:
                    w('chipy.{}()\n'.format(func))
            else:
                id_list = (
                    [t.strip() for t in ids_str.split(',') if t.strip().isdigit()]
                    if ids_str else _resolve_group_ids(grp)
                )
                if id_list:
                    w('for _id in [{}]:\n'.format(', '.join(id_list)))
                    if store:
                        w('    {}_{{_id}} = chipy.{}(_id)\n'.format(store, func))
                    else:
                        w('    chipy.{}(_id)\n'.format(func))
            w('\n')

        for _gbv_key_b, _gbv_func_b, _gbv_flag_b in [
            ('gbv2_entries', 'RBDY2_GetBodyVector', use_RBDY2),
            ('gbv3_entries', 'RBDY3_GetBodyVector', use_RBDY3),
        ]:
            if not _gbv_flag_b:
                continue
            _before_entries = [e for e in p.get(_gbv_key_b, []) if _is_before(e)]
            if _before_entries:
                w('# ── {} avant boucle ──────\n'.format(_gbv_func_b))
                for _eb in _before_entries:
                    _vb  = _eb.get('vec', 'Coor_')
                    _sb  = _eb.get('ids', '').strip()
                    _gb  = _eb.get('group', '').strip()
                    _ilb = (
                        [t.strip() for t in _sb.split(',') if t.strip().isdigit()]
                        if _sb else _resolve_group_ids(_gb)
                    )
                    if _ilb:
                        w('for _id in [{}]:\n'.format(', '.join(_ilb)))
                        w("    chipy.{}('{}', _id)\n".format(_gbv_func_b, _vb))
                        w('\n')

        _all_insp_before = (
            [e for e in p.get('insp2d_entries', []) if _is_before(e)]
            + [e for e in p.get('insp3d_entries', []) if _is_before(e)]
            + [e for e in p.get('inspi_entries',  []) if _is_before(e)]
        )
        if _all_insp_before:
            w('# ── Inspection avant boucle ──────\n')
            for _ebi in _all_insp_before:
                _emit_insp_outside(_ebi)

        _set_before = [
            (index, entry)
            for index, entry in enumerate(p.get('set_entries', []), start=1)
            if _is_before(entry)
        ]
        if _set_before:
            w('# ── Actions SET avant boucle ──────\n')
            for index, entry in _set_before:
                _emit_set_action(entry, index, '')
            w('\n')

        # ── 8. Boucle(s) de calcul ────────────────────────────────────────────
        if use_multi:
            w('# ── Boucle multi-pas ────────────────────────────────────\n')
            w('for _phase, _dt in enumerate(dt_sequence):\n')
            w('    chipy.TimeEvolution_SetTimeStep(_dt)\n')
            w("    chipy.utilities_logMes(f'PHASE {_phase + 1} / {len(dt_sequence)} - dt = {_dt}')\n")
            w('    for k in range(steps_per_phase):\n')
            ind = '        '
        else:
            w('# ── Boucle de calcul ─────────────────────────────────────\n')
            w('for k in range(nb_steps):\n')
            ind = '    '

        def L(line: str) -> None:
            w(ind + line + '\n')

        L("chipy.utilities_logMes('INCREMENT STEP')")
        L('chipy.IncrementStep()')
        if p.get('advanced_fatal_damping'):
            L('chipy.FatalDamping()')
        w('\n')

        _set_in_loop = [
            (index, entry)
            for index, entry in enumerate(p.get('set_entries', []), start=1)
            if _is_in_loop(entry)
        ]
        if _set_in_loop:
            L('# Actions SET')
            for index, entry in _set_in_loop:
                guard, extra_ind = _timing_guard(entry)
                if guard:
                    w(guard)
                    _emit_set_action(entry, index, extra_ind)
                else:
                    _emit_set_action(entry, index, ind)
            w('\n')

        # ── 8a. Activation des vagues de factory dans la boucle ───────────────
        if _factory_active:
            L('# ── Particle Factory : activation des vagues planifiees ───')
            L('if k in _factory_schedule:')
            w(ind + '    for _bnum in _factory_schedule[k]:\n')
            w(ind + f'        chipy.{_rbdy_prefix}_SetVisible(_bnum)\n')
            w('\n')

        # a. FreeVelocity corps rigides
        if use_RBDY2:
            L("chipy.utilities_logMes('COMPUTE Fext/Fint - RBDY2')")
            L('chipy.ComputeFext()')
            L('chipy.ComputeBulk()')
            L("chipy.utilities_logMes('COMPUTE Free Velocity - RBDY2')")
            L('chipy.ComputeFreeVelocity()')
        if use_RBDY3:
            L("chipy.utilities_logMes('COMPUTE Free Velocity - RBDY3')")
            L('chipy.ComputeFext()')
            L('chipy.ComputeBulk()')
            L('chipy.ComputeFreeVelocity()')
        w('\n')

        # b. FreeVelocity deformables
        if use_mecaMAILx:
            L("chipy.utilities_logMes('mecaMAILx - assembly + FreeVelocity')")
            L('chipy.mecaMAILx_ComputeFext()')
            L('chipy.mecaMAILx_ComputeBulk()')
            if p.get('advanced_assemble_mechanical'):
                L('chipy.AssembleMechanicalLHS()')
                L('chipy.AssembleMechanicalRHS()')
            L('chipy.mecaMAILx_ComputeFreeVelocity()')
        if use_therMAILx:
            L("chipy.utilities_logMes('therMAILx - flux + FreeVelocity')")
            L('chipy.therMAILx_ComputeFext()')
            L('chipy.therMAILx_ComputeBulk()')
            if p.get('advanced_assemble_thermal'):
                L('chipy.AssembleThermalLHS()')
                L('chipy.AssembleThermalRHS()')
            L('chipy.therMAILx_ComputeFreeVelocity()')
        if use_poroMAILx:
            L("chipy.utilities_logMes('poroMAILx - pression + FreeVelocity')")
            L('chipy.poroMAILx_ComputeFext()')
            L('chipy.poroMAILx_ComputeBulk()')
            if p.get('advanced_assemble_poro'):
                L('chipy.AssemblePoroLHS()')
                L('chipy.AssemblePoroRHS()')
            if p.get('advanced_assemble_multi') and p.get('physics') == 'THMx':
                L('chipy.AssembleMultiLHS()')
                L('chipy.AssembleMultiRHS()')
            L('chipy.poroMAILx_ComputeFreeVelocity()')
        if any_MAILx:
            w('\n')

        # c. Detection de contact
        L("chipy.utilities_logMes('SELECT PROX TACTORS')")
        if p.get('advanced_fd_select_prox'):
            pair_shapes = {
                (rule.candidate_contactor, rule.antagonist_contactor)
                for rule in self.project.visibility
            }
            if not pair_shapes or any(pair != ('SPHER', 'SPHER') for pair in pair_shapes):
                raise ValueError(
                    "FdSelectProxTactors is only valid when all project contacts "
                    "are SPHER/SPHER."
                )
            L('chipy.FdSelectProxTactors()')
        elif all_tacts:
            for t in tacts_2d:
                L(f'chipy.{t}_SelectProxTactors()')
            for t in tacts_3d:
                L(f'chipy.{t}_SelectProxTactors()')
            for t in tacts_mix:
                L(f'chipy.{t}_SelectProxTactors()')
            for t in tacts_pt:
                L(f'chipy.{t}_SelectProxTactors()')
        else:
            L('chipy.SelectProxTactors()')
        if p.get('advanced_display_prox_tactors'):
            L('chipy.DisplayProxTactors()')
        w('\n')

        # d. Resolution
        L("chipy.utilities_logMes('RESOLUTION')")
        L('chipy.RecupRloc(Rloc_tol)')
        L('chipy.ExSolver(solver_type, norm, tol, relax, gs_it1, gs_it2)')
        L('chipy.UpdateTactBehav()')
        L('chipy.StockRloc()')
        if p.get('advanced_smooth_force'):
            L('chipy.SmoothForceComputation()')
        w('\n')

        # e. Comportement volumique
        if p.get('use_bulk_behav'):
            L("chipy.utilities_logMes('UPDATE BULK BEHAV')")
            L('chipy.UpdateBulkBehav()')
            w('\n')

        # f. ComputeDof + UpdateStep
        L("chipy.utilities_logMes('COMPUTE DOF')")
        L('chipy.ComputeDof()')
        if use_mecaMAILx:
            L('chipy.mecaMAILx_ComputeDof()')
        if use_therMAILx:
            L('chipy.therMAILx_ComputeDof()')
        if use_poroMAILx:
            L('chipy.poroMAILx_ComputeDof()')
        w('\n')
        L("chipy.utilities_logMes('UPDATE DOF')")
        L('chipy.UpdateStep()')
        if use_mecaMAILx:
            L('chipy.mecaMAILx_UpdateStep()')
        if use_therMAILx:
            L('chipy.therMAILx_UpdateStep()')
        if use_poroMAILx:
            L('chipy.poroMAILx_UpdateStep()')
        w('\n')

        if p.get('advanced_compute_rnod'):
            L('chipy.ComputeRnod()')
        if p.get('advanced_display_out_dof'):
            L('chipy.DisplayOutDof()')
        if p.get('advanced_display_out_rnod'):
            L('chipy.DisplayOutRnod(1, nb_steps)')
        if p.get('advanced_display_out_vloc_rloc'):
            L('chipy.DisplayOutVlocRloc()')

        # g. Extraction
        if p.get('extract_energy'):
            L('chipy.ComputeEnergy()')
            L('chipy.WriteEnergy()')
        if p.get('extract_KE') and use_RBDY2:
            L('chipy.RBDY2_KineticEnergy()')
        if p.get('extract_Rnod'):
            L('chipy.inter_handler_Rnod()')
        if p.get('extract_Vloc'):
            L('chipy.inter_handler_Vloc()')
        if p.get('extract_Rloc'):
            L('chipy.inter_handler_Rloc()')
        if p.get('extract_fields') and use_mecaMAILx:
            L('chipy.mecaMAILx_WriteBodies(freq_write)')
        if p.get('extract_internal') and use_mecaMAILx:
            L('chipy.mecaMAILx_WriteInternalVariables(freq_write)')
        if any(p.get(k) for k in (
            'extract_energy', 'extract_KE', 'extract_Rnod',
            'extract_Vloc',   'extract_Rloc',
            'extract_fields', 'extract_internal',
        )):
            w('\n')

        # ── GetBodyVector RBDY2 / RBDY3 dans la boucle ───────────────────────
        # Modes "all" / "every_n" / "at_k" uniquement (pas before ni after)
        for _gbv_key, _gbv_func, _gbv_flag in [
            ('gbv2_entries', 'RBDY2_GetBodyVector', use_RBDY2),
            ('gbv3_entries', 'RBDY3_GetBodyVector', use_RBDY3),
        ]:
            if not _gbv_flag:
                continue
            _in_entries = [e for e in p.get(_gbv_key, []) if _is_in_loop(e)]
            if _in_entries:
                L("chipy.utilities_logMes('{} extraction')".format(_gbv_func))
                for _e in _in_entries:
                    _emit_gbv(_e, _gbv_func)

        # ── Visibilite dans la boucle ─────────────────────────────────────────
        for _ve_loop in _vis_in_loop:
            _emit_vis_entry(_ve_loop, in_loop_context=True)

        # ── Inspection contacteurs / interactions (dans la boucle) ────────────
        _all_insp_in = (
            [e for e in p.get('insp2d_entries', []) if _is_in_loop(e)]
            + [e for e in p.get('insp3d_entries', []) if _is_in_loop(e)]
            + [e for e in p.get('inspi_entries',  []) if _is_in_loop(e)]
        )
        if _all_insp_in:
            L("chipy.utilities_logMes('INSPECTION')")
            for _ei in _all_insp_in:
                _emit_insp(_ei)

        # h. Critere d'arret
        if use_stop:
            L("# Critere d'arret")
            L('if k % stop_freq == 0:')
            stop_type = p.get('stop_crit_type', 'energy')
            if stop_type == 'energy':
                w(ind + '    _crit = chipy.GetResidualEnergy()\n')
            elif stop_type == 'disp_max':
                w(ind + '    _crit = chipy.GetMaxDisplacement()\n')
            else:
                w(ind + '    _crit = chipy.GetForceResidual()\n')
            w(ind + '    if _crit < stop_tol:\n')
            w(ind + "        chipy.utilities_logMes(\n")
            w(ind + "            f'Critere atteint a k={k} : {_crit:.4e} < {stop_tol:.2e}')\n")
            w(ind + '        break\n')
            w('\n')

        # i. Ecriture resultats
        L("chipy.utilities_logMes('WRITE OUT')")
        output_options = (
            ('advanced_write_out_dof', 'WriteOutDof'),
            ('advanced_write_out_gpv', 'WriteOutGPV'),
            ('advanced_write_out_mp_values', 'WriteOutMpValues'),
            ('advanced_write_out_rnod', 'WriteOutRnod'),
            ('advanced_write_out_vloc_rloc', 'WriteOutVlocRloc'),
        )
        selected_output_options = [
            func for option, func in output_options if p.get(option)
        ]
        if p.get('advanced_hdf5') or not selected_output_options:
            L('chipy.WriteOut(freq_write)')
        else:
            for func in selected_output_options:
                L(f'chipy.{func}(freq_write)')
        if use_RBDY3 and not selected_output_options:
            L('chipy.RBDY3_WriteOut(freq_write)')
        w('\n')

        # Visualisation dans la boucle
        if p.get('display_in_loop', True):
            L("chipy.utilities_logMes('VISU & POSTPRO')")
            wrote_visu = False
            if p.get('visu_RBDY2') and use_RBDY2:
                L('chipy.WriteDisplayFiles(freq_display)')
                wrote_visu = True
            if p.get('visu_RBDY3') and use_RBDY3:
                L('chipy.WriteDisplayFiles(freq_display)')
                wrote_visu = True
            if p.get('visu_mecaMAILx') and use_mecaMAILx:
                L('chipy.mecaMAILx_WriteDisplayFiles(freq_display)')
                wrote_visu = True
            if p.get('visu_therMAILx') and use_therMAILx:
                L('chipy.therMAILx_WriteDisplayFiles(freq_display)')
                wrote_visu = True
            if p.get('visu_poroMAILx') and use_poroMAILx:
                L('chipy.poroMAILx_WriteDisplayFiles(freq_display)')
                wrote_visu = True
            if not wrote_visu:
                L('chipy.WriteDisplayFiles(freq_display)')
            L('chipy.WritePostproFiles()')
            w('\n')

        # ── GetBodyVector après boucle (step_mode="after") ───────────────────
        for _gbv_key2, _gbv_func2, _gbv_flag2 in [
            ('gbv2_entries', 'RBDY2_GetBodyVector', use_RBDY2),
            ('gbv3_entries', 'RBDY3_GetBodyVector', use_RBDY3),
        ]:
            if not _gbv_flag2:
                continue
            _out_entries = [e for e in p.get(_gbv_key2, []) if _is_after(e)]
            if _out_entries:
                w('# ── {} apres boucle ──────\n'.format(_gbv_func2))
                for _e2 in _out_entries:
                    _v2  = _e2.get('vec', 'Coor_')
                    _s2  = _e2.get('ids', '').strip()
                    _g2  = _e2.get('group', '').strip()
                    _il2 = (
                        [t.strip() for t in _s2.split(',') if t.strip().isdigit()]
                        if _s2 else _resolve_group_ids(_g2)
                    )
                    if _il2:
                        w('for _id in [{}]:\n'.format(', '.join(_il2)))
                        w("    chipy.{}('{}', _id)\n".format(_gbv_func2, _v2))
                        w('\n')

        # ── Inspection après boucle (step_mode="after") ──────────────────────
        _all_insp_out = (
            [e for e in p.get('insp2d_entries', []) if _is_after(e)]
            + [e for e in p.get('insp3d_entries', []) if _is_after(e)]
            + [e for e in p.get('inspi_entries',  []) if _is_after(e)]
        )
        if _all_insp_out:
            w('# ── Inspection apres boucle ──────\n')
            for _eo in _all_insp_out:
                _emit_insp_outside(_eo)

        _set_after = [
            (index, entry)
            for index, entry in enumerate(p.get('set_entries', []), start=1)
            if _is_after(entry)
        ]
        if _set_after:
            w('# ── Actions SET apres boucle ──────\n')
            for index, entry in _set_after:
                _emit_set_action(entry, index, '')
            w('\n')

        # ── Visibilite apres boucle (step_mode="after") ───────────────────────
        if _vis_after:
            w('# ── Visibilite apres boucle ──────\n')
            for _ve_after in _vis_after:
                _emit_vis_entry(_ve_after, in_loop_context=False)
            w('\n')

        # ── 9. Visualisation hors-boucle ──────────────────────────────────────
        if not p.get('display_in_loop', True):
            w('# ── Visualisation finale (hors boucle) ──────────────────\n')
            if p.get('visu_RBDY2') and use_RBDY2:
                w('chipy.RBDY2_WriteDisplayFiles(1)\n')
            if p.get('visu_RBDY3') and use_RBDY3:
                w('chipy.RBDY3_WriteDisplayFiles(1)\n')
            if p.get('visu_mecaMAILx') and use_mecaMAILx:
                w('chipy.mecaMAILx_WriteDisplayFiles(1)\n')
            if p.get('visu_therMAILx') and use_therMAILx:
                w('chipy.therMAILx_WriteDisplayFiles(1)\n')
            if p.get('visu_poroMAILx') and use_poroMAILx:
                w('chipy.poroMAILx_WriteDisplayFiles(1)\n')
            w('chipy.WritePostproFiles()\n')
            w('\n')

        if p.get('advanced_add_dof2') and dim == 2:
            w('chipy.AddDof2InBodies()\n')
        if p.get('advanced_write_bodies'):
            w('chipy.WriteBodies()\n')
        if p.get('advanced_write_behaviours'):
            w('chipy.WriteBehaviours()\n')
        if p.get('advanced_write_driven_dof'):
            w('chipy.WriteDrivenDof()\n')
        if p.get('advanced_write_mp_behaviours'):
            w('chipy.WriteMpBehaviours()\n')
        if p.get('advanced_write_last'):
            if p.get('advanced_hdf5'):
                w('chipy.WriteLast({!r})\n'.format(
                    str(p.get('advanced_hdf5_filename', '')).strip()
                ))
            else:
                w('chipy.WriteLast()\n')
        else:
            for option, func in (
                ('advanced_write_last_dof', 'WriteLastDof'),
                ('advanced_write_last_gpv', 'WriteLastGPV'),
                ('advanced_write_last_vloc_rloc', 'WriteLastVlocRloc'),
            ):
                if p.get(option):
                    w(f'chipy.{func}()\n')
        for option, func in (
            ('advanced_write_last_mp_values', 'WriteLastMpValues'),
            ('advanced_write_last_rnod', 'WriteLastRnod'),
        ):
            if p.get(option):
                w(f'chipy.{func}()\n')

        #-----Avertissement - références de groupes non résolues (avatars introuvables) -----
        if getattr(self, '_unresolved_group_refs', None):
            w('\n')
            w('# ' + '=' * 68 + '\n')
            w('# ⚠️  ATTENTION — références de groupe incomplètes\n')
            w('# Certains avatar_id référencés par un groupe étaient introuvables\n')
            w('# au moment de la génération de ce script (avatar supprimé après\n')
            w('# coup sans nettoyage du groupe, ou factory non générée).\n')
            w('# Les extractions/visibilités listées ci-dessous sont donc\n')
            w('# potentiellement INCOMPLÈTES par rapport à ce que vous attendez :\n')
            for grp_name, missing_ids in self._unresolved_group_refs.items():
                w(f"#   - groupe '{grp_name}' : {len(missing_ids)} avatar(s) manquant(s)\n")
            w('# Vérifiez le journal de l\'application (F7) pour le détail complet,\n')
            w('# ou nettoyez les groupes concernés puis régénérez ce script.\n')
            w('# ' + '=' * 68 + '\n')

        # ── 10. Finalisation ──────────────────────────────────────────────────
        w('chipy.CloseDisplayFiles()\n')
        w('chipy.ClosePostproFiles()\n')
        w('chipy.Finalize()\n')
        w('\n')
        w("print('CALCUL TERMINE')\n")

        return buf.getvalue()


def generate_command_script(
    project: Project,
    params: Optional[Dict[str, Any]] = None,
    *,
    journal: Optional[_JournalLike] = None,
) -> str:
    """Public API: full ``command.py`` text from *project* + *params*."""
    gen = ComputeScriptGenerator(project, journal=journal)
    return gen.generate_string(params or {})


def write_command_script(
    project: Project,
    path: Path | str,
    params: Optional[Dict[str, Any]] = None,
    *,
    journal: Optional[_JournalLike] = None,
) -> Path:
    path = Path(path)
    path.write_text(generate_command_script(project, params, journal=journal), encoding="utf-8")
    return path
