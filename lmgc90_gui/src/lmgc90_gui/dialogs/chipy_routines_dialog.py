# =============================================================================
# chipy_routines_dialog.py  —  LMGC90_GUI
# =============================================================================
"""Dialogue de configuration des routines chipy pour ``command.py``.

Onglets : modele, routines, extraction, pilotage, inspections 2D/3D/interactions
et actions SET configurables.
"""

import ast
import keyword

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QDialogButtonBox,
    QScrollArea, QFrame, QButtonGroup, QRadioButton,
    QMessageBox, QPushButton, QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional


# ── Helpers UI ────────────────────────────────────────────────────────────────

def _section(title: str) -> QGroupBox:
    """QGroupBox avec titre en gras et bordure subtile."""
    gb = QGroupBox(title)
    gb.setStyleSheet(
        "QGroupBox {"
        "  font-weight: bold;"
        "  border: 1px solid #b8b8b8;"
        "  border-radius: 4px;"
        "  margin-top: 8px;"
        "  padding-top: 4px;"
        "}"
        "QGroupBox::title {"
        "  subcontrol-origin: margin;"
        "  left: 10px;"
        "  padding: 0 4px;"
        "  color: #2c3e50;"
        "}"
    )
    return gb


def _scroll(widget: QWidget) -> QScrollArea:
    """Enrobe un widget dans un QScrollArea sans cadre."""
    sc = QScrollArea()
    sc.setWidget(widget)
    sc.setWidgetResizable(True)
    sc.setFrameShape(QFrame.Shape.NoFrame)
    return sc


def _cb(label: str, checked: bool = False, tip: str = "") -> QCheckBox:
    """Cree une QCheckBox avec tooltip optionnel."""
    c = QCheckBox(label)
    c.setChecked(checked)
    if tip:
        c.setToolTip(tip)
    return c


def _note(text: str) -> QLabel:
    """Label de note informatif."""
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        "color:#555; font-size:8pt;"
        "background:#f7f7f7; padding:4px 6px; border-radius:3px;"
    )
    return lbl


# =============================================================================
# ChipyRoutinesDialog
# =============================================================================

# Vecteurs d'etat disponibles pour RBDY2 et RBDY3
_GBV_VECTORS = [
    ("Coor0", "Position initiale                 (x0, y0[, z0])"),
    ("Coor_", "Position courante                 (x, y[, z])"),
    ("Coorb", "Position debut de pas             (xb, yb[, zb])"),
    ("Coorm", "Position milieu de pas            (xm, ym[, zm])"),
    ("X____", "Coordonnees generalisees          (x, y, angle[, ...])"),
    ("V____", "Vitesses generalisees             (vx, vy, omega[, ...])"),
    ("Vbeg_", "Vitesses debut de pas             (vxb, vyb[, ...])"),
    ("Vfree", "Vitesses libres (sans contact)    (vxf, vyf[, ...])"),
    ("Fext",  "Forces externes                   (Fx, Fy[, Fz, ...])"),
    ("Fint_", "Forces internes                   (Fix, Fiy[, Fiz, ...])"),
    ("Reac",  "Forces de reaction (contact)      (Rx, Ry[, Rz, ...])"),
    ("Ireac", "Impulsions de reaction             (IRx, IRy[, IRz, ...])"),
]

# Garde les anciennes listes pour compatibilite avec _load/_auto_detect
_GBV_VECTORS_2D = _GBV_VECTORS
_GBV_VECTORS_3D = _GBV_VECTORS


class ChipyRoutinesDialog(QDialog):
    """\n    Dialogue de configuration des routines chipy.    Utilisation :        dlg = ChipyRoutinesDialog(current_params, controller, parent)        if dlg.exec() == QDialog.DialogCode.Accepted:            params = dlg.get_params()    """

    # ── Valeurs par defaut ────────────────────────────────────────────────────
    DEFAULTS: Dict[str, Any] = {
        # Onglet Modele
        "mhyp":               1,
        "deformable":         False,
        "physics":            "MECAx",
        "Rloc_tol":           5e-2,
        # Onglet Routines — Corps rigides
        "use_RBDY2":          True,
        "use_RBDY3":          False,
        # Detecteurs 2D
        "use_DKDKx":          True,
        "use_DKJCx":          False,
        "use_DKKDx":          False,
        "use_PLPLx":          False,
        "use_CLALp":          False,
        "use_ALpALp":         False,
        # Detecteurs 3D
        "use_SPSPx":          False,
        "use_SPCDx":          False,
        "use_SPPLx":          False,
        "use_CDCDx":          False,
        "use_CDPLx":          False,
        "use_PRPRx":          False,
        # Deformables
        "use_mecaMAILx":       False,
        "use_therMAILx":       False,
        "use_poroMAILx":       False,
        # Contacteurs mixtes rigide/deformable
        "use_DKMECAx":        False,
        "use_ALpMECAx":       False,
        "use_SPMECAx":        False,
        # Routines speciales
        "use_PT2Dx":          False,
        "use_PT3Dx":          False,
        "use_NODES":          False,
        "use_bulk_behav":     False,
        # Routines avancees optionnelles (les etapes du cycle restent automatiques)
        "advanced_assemble_mechanical": False,
        "advanced_assemble_thermal": False,
        "advanced_assemble_poro": False,
        "advanced_assemble_multi": False,
        "advanced_fd_select_prox": False,
        "advanced_compute_rnod": False,
        "advanced_fatal_damping": False,
        "advanced_smooth_force": False,
        "advanced_display_out_dof": False,
        "advanced_display_out_rnod": False,
        "advanced_display_out_vloc_rloc": False,
        "advanced_display_prox_tactors": False,
        "advanced_hdf5": False,
        "advanced_add_dof2": False,
        "advanced_write_out_dof": False,
        "advanced_write_out_gpv": False,
        "advanced_write_out_mp_values": False,
        "advanced_write_out_rnod": False,
        "advanced_write_out_vloc_rloc": False,
        "advanced_write_last": False,
        "advanced_write_last_dof": False,
        "advanced_write_last_gpv": False,
        "advanced_write_last_mp_values": False,
        "advanced_write_last_rnod": False,
        "advanced_write_last_vloc_rloc": False,
        "advanced_write_behaviours": False,
        "advanced_write_bodies": False,
        "advanced_write_driven_dof": False,
        "advanced_write_mp_behaviours": False,
        "advanced_add_registers_to_display": False,
        "advanced_circular_selection": False,
        "advanced_set_contact_radius": False,
        "advanced_set_domain_boundary": False,
        "advanced_set_number_interaction": False,
        "advanced_set_periodic_condition": False,
        "advanced_hdf5_filename": "command.h5",
        "advanced_circular_selection_args": "0.0, 0.0, 1.0",
        "advanced_set_contact_radius_args": "",
        "advanced_set_domain_boundary_args": "",
        "advanced_set_number_interaction_args": "",
        "advanced_set_periodic_condition_args": "",
        # Onglet Extraction — Logs
        "disable_log":        False,
        # Visualisation
        "visu_RBDY2":         True,
        "visu_RBDY3":         False,
        "visu_mecaMAIL":       False,
        "visu_therMAIL":       False,
        "visu_poroMAIL":       False,
        "display_in_loop":    True,
        # Visibilite avatars — listes d'IDs (ex: "1, 3, 5") ou "" = desactive
        # Visibilite — liste d'entrees dynamiques
        # Chaque entree : {"action": "visible"|"invisible",
        #   "dim": "2D"|"3D", "ids": str, "group": str,
        #   "step_mode": "before"|"all"|"every_n"|"at_k"|"after",
        #   "step_val": int}
        "vis_entries": [],
        # GetBodyVector RBDY2 — liste d'entrees configurables
        # Chaque entree : {"vec": str, "ids": str, "group": str,
        #   "step_mode": "before"|"all"|"every_n"|"at_k"|"after",
        #   "step_val": int}  (N pour every_n, k pour at_k)
        "gbv2_entries": [],
        # GetBodyVector RBDY3
        "gbv3_entries": [],
        # Forces de contact
        "extract_Rnod":       False,
        "extract_Vloc":       False,
        "extract_Rloc":       False,
        # Energie
        "extract_energy":     False,
        "extract_KE":         False,
        # Champs FEM
        "extract_fields":     False,
        "extract_internal":   False,
        # ── Inspection 2D ────────────────────────────────────────────────────
        # Chaque entree : {"func": str, "ids": str, "group": str,
        #   "step_mode": "before"|"all"|"every_n"|"at_k"|"after",
        #   "step_val": int, "store": str}
        "insp2d_entries": [],
        # ── Inspection 3D ────────────────────────────────────────────────────
        "insp3d_entries": [],
        # ── Inspection Interactions ───────────────────────────────────────────
        "inspi_entries": [],
        # Actions chipy SET configurables
        "set_entries": [],
        # Onglet Pilotage — Restart
        "use_restart":        False,
        "restart_step":       0,
        # Critere d'arret
        "use_stop_crit":      False,
        "stop_crit_type":     "energy",
        "stop_crit_val":      1e-6,
        "stop_crit_freq":     10,
        # Multi-pas
        "use_multi_step":     False,
        "multi_step_nb":      3,
        "multi_step_sizes":   "1e-3, 1e-4, 1e-5",
    }

    def __init__(
        self,
        current_params: Optional[Dict[str, Any]] = None,
        controller=None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Configuration des routines chipy")
        self.resize(800, 700)
        self.controller = controller

        self._params: Dict[str, Any] = dict(self.DEFAULTS)
        if current_params:
            params = dict(current_params)
            for current, legacy in (
                ("use_mecaMAILx", "use_mecaMAIL"),
                ("use_therMAILx", "use_therMAIL"),
                ("use_poroMAILx", "use_poroMAIL"),
            ):
                if current not in params and legacy in params:
                    params[current] = params[legacy]
            self._params.update(
                {k: v for k, v in params.items() if k in self.DEFAULTS}
            )

        self._build_ui()
        self._load()
        self._wire()
        self._auto_detect()

    # =========================================================================
    # Construction de l'interface
    # =========================================================================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._tab_model(),    "Modele")
        self._tabs.addTab(self._tab_routines(), "Routines")
        self._tabs.addTab(self._tab_advanced_routines(), "Avance")
        self._tabs.addTab(self._tab_extract(),  "Extraction")
        self._tabs.addTab(self._tab_pilot(),    "Pilotage")
        self._tabs.addTab(self._tab_insp_2d(),  "Inspect. 2D")
        self._tabs.addTab(self._tab_insp_3d(),  "Inspect. 3D")
        self._tabs.addTab(self._tab_insp_int(), "Inspect. Interact.")
        self._tabs.addTab(self._tab_set_actions(), "Actions SET")

        root.addWidget(self._tabs, stretch=1)

        btn_preview = QPushButton("Apercu du script command.py")
        btn_preview.setToolTip(
            "Genere et affiche le script de calcul avec les options courantes."
        )
        btn_preview.clicked.connect(self._show_preview)
        root.addWidget(btn_preview)

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        box.accepted.connect(self._on_accept)
        box.rejected.connect(self.reject)
        box.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._on_restore_defaults)
        root.addWidget(box)

    # ── Onglet 1 : Modele ─────────────────────────────────────────────────────

    def _tab_model(self) -> QWidget:
        w = QWidget()
        vb = QVBoxLayout(w)
        vb.setSpacing(10)

        # Hypothese mecanique
        grp_h = _section("Hypothese mecanique  (mhyp)")
        vb_h = QVBoxLayout()
        self._rb_cp = QRadioButton("Contraintes planes       (mhyp = 1)  -- 2D")
        self._rb_dp = QRadioButton("Deformations planes      (mhyp = 2)  -- 2D")
        self._rb_3d = QRadioButton("Tridimensionnel          (mhyp = 3)  -- 3D")
        self._mhyp_grp = QButtonGroup(self)
        for rb in (self._rb_cp, self._rb_dp, self._rb_3d):
            self._mhyp_grp.addButton(rb)
            vb_h.addWidget(rb)
        vb_h.addWidget(_note(
            "La dimension du projet est detectee automatiquement. "
            "mhyp est pertinent uniquement en 2D."
        ))
        grp_h.setLayout(vb_h)
        vb.addWidget(grp_h)

        # Corps deformables
        grp_d = _section("Corps deformables")
        fl_d = QFormLayout()
        self._cb_deformable = _cb(
            "Activer les corps deformables  (ReadDatbox deformable=True)",
            tip="Active le chargement et le calcul des corps deformables "
                "(MESH_DEFORMABLE). Active mecaMAILx automatiquement si MECAx.",
        )
        fl_d.addRow(self._cb_deformable)

        self._combo_phys = QComboBox()
        self._combo_phys.addItems([
            "MECAx  -- Mecanique des solides",
            "THERx  -- Thermique",
            "POROx  -- Hydraulique",
            "MULTI   -- Thermo-hydraulique-mecanique",
        ])
        fl_d.addRow("Physique MAILx :", self._combo_phys)

        self._dspin_rloc = QDoubleSpinBox()
        self._dspin_rloc.setRange(1e-8, 1.0)
        self._dspin_rloc.setDecimals(4)
        self._dspin_rloc.setSingleStep(1e-3)
        self._dspin_rloc.setValue(5e-2)
        self._dspin_rloc.setToolTip(
            "Tolerance sur les efforts de contact pour la reprise de Rloc. "
            "Typiquement 5e-2."
        )
        fl_d.addRow("Rloc_tol :", self._dspin_rloc)
        grp_d.setLayout(fl_d)
        vb.addWidget(grp_d)

        # Resume projet
        grp_info = _section("Resume du projet (detection automatique)")
        vb_info = QVBoxLayout()
        self._lbl_info = QLabel("(aucun projet charge)")
        self._lbl_info.setWordWrap(True)
        self._lbl_info.setStyleSheet(
            "font-family: monospace; font-size: 8pt;"
            "background:#f0f4f8; padding:8px; border-radius:4px;"
        )
        vb_info.addWidget(self._lbl_info)
        grp_info.setLayout(vb_info)
        vb.addWidget(grp_info)

        vb.addStretch()
        return _scroll(w)

    # ── Onglet 2 : Routines ───────────────────────────────────────────────────

    def _tab_routines(self) -> QWidget:
        w = QWidget()
        vb = QVBoxLayout(w)
        vb.setSpacing(10)

        # Corps rigides 2D
        grp_r2d = _section("Corps rigides 2D  --  RBDY2")
        vb_r2d = QVBoxLayout()
        self._cb_RBDY2 = _cb(
            "Activer RBDY2  (NewStep / FreeVelocity / WriteOut)",
            checked=True,
            tip="Routines obligatoires pour tout corps rigide 2D.",
        )
        vb_r2d.addWidget(self._cb_RBDY2)
        grp_r2d.setLayout(vb_r2d)
        vb.addWidget(grp_r2d)

        # Corps rigides 3D
        grp_r3d = _section("Corps rigides 3D  --  RBDY3")
        vb_r3d = QVBoxLayout()
        self._cb_RBDY3 = _cb(
            "Activer RBDY3  (NewStep / FreeVelocity / WriteOut)",
            tip="Routines obligatoires pour tout corps rigide 3D.",
        )
        vb_r3d.addWidget(self._cb_RBDY3)
        grp_r3d.setLayout(vb_r3d)
        vb.addWidget(grp_r3d)

        # Detecteurs contact 2D
        grp_t2d = _section("Detecteurs de contact 2D")
        vb_t2d = QVBoxLayout()
        self._cb_DKDKx  = _cb("DKDKx   -- Disque / Disque",    checked=True)
        self._cb_DKJCx  = _cb("DKJCx   -- Disque / Jonc")
        self._cb_DKKDx  = _cb("DKKDx   -- Disque / Polygone")
        self._cb_PLPLx  = _cb("PLPLx   -- Plan / Plan")
        self._cb_CLALp  = _cb(
            "CLALp   -- Ligne / Ligne  (maconnerie)",
            tip="Detecteur pour les interfaces de briques (CLALp).",
        )
        self._cb_ALpALp = _cb("ALpALp  -- Ligne / Ligne (ALp)")
        for c in (self._cb_DKDKx, self._cb_DKJCx, self._cb_DKKDx,
                  self._cb_PLPLx, self._cb_CLALp, self._cb_ALpALp):
            vb_t2d.addWidget(c)
        grp_t2d.setLayout(vb_t2d)
        vb.addWidget(grp_t2d)

        # Detecteurs contact 3D
        grp_t3d = _section("Detecteurs de contact 3D")
        vb_t3d = QVBoxLayout()
        self._cb_SPSPx = _cb("SPSPx   -- Sphere / Sphere")
        self._cb_SPCDx = _cb("SPCDx   -- Sphere / Cylindre")
        self._cb_SPPLx = _cb("SPPLx   -- Sphere / Plan")
        self._cb_CDCDx = _cb("CDCDx   -- Cylindre / Cylindre")
        self._cb_CDPLx = _cb("CDPLx   -- Cylindre / Plan")
        self._cb_PRPRx = _cb("PRPRx   -- Polyedre / Polyedre")
        for c in (self._cb_SPSPx, self._cb_SPCDx, self._cb_SPPLx,
                  self._cb_CDCDx, self._cb_CDPLx, self._cb_PRPRx):
            vb_t3d.addWidget(c)
        grp_t3d.setLayout(vb_t3d)
        vb.addWidget(grp_t3d)

        # Deformables
        grp_fem = _section("Corps deformables  --  Routines MAILx")
        vb_fem = QVBoxLayout()
        self._cb_mecaMAILx = _cb(
            "mecaMAILx  -- Mecanique  (assembly / Fint / Fext / K / ComputeDof)",
            tip="Active l'assemblage et le calcul des forces internes mecaniques.",
        )
        self._cb_therMAILx = _cb(
            "therMAILx  -- Thermique  (flux / bilan thermique / ComputeDof)",
            tip="Active les routines de diffusion thermique par elements finis.",
        )
        self._cb_poroMAILx = _cb(
            "poroMAILx  -- Hydraulique  (pression / flux fluide / ComputeDof)",
            tip="Active les routines de pression hydraulique par elements finis.",
        )
        for c in (self._cb_mecaMAILx, self._cb_therMAILx, self._cb_poroMAILx):
            vb_fem.addWidget(c)
        grp_fem.setLayout(vb_fem)
        vb.addWidget(grp_fem)

        # Contacteurs mixtes
        grp_mix = _section("Contacteurs mixtes  --  Rigide / Deformable")
        vb_mix = QVBoxLayout()
        self._cb_DKMECAx  = _cb(
            "DKMECAx   -- Disque rigide / Meca MAILx 2D",
            tip="Interaction entre disques rigides et elements finis mecaniques 2D.",
        )
        self._cb_ALpMECAx = _cb(
            "ALpMECAx  -- CLALp (maconnerie) / Meca MAILx 2D",
            tip="Interaction interfaces maconnerie et elements finis mecaniques.",
        )
        self._cb_SPMECAx  = _cb(
            "SPMECAx   -- Sphere rigide / Meca MAILx 3D",
            tip="Interaction entre spheres rigides et elements finis mecaniques 3D.",
        )
        for c in (self._cb_DKMECAx, self._cb_ALpMECAx, self._cb_SPMECAx):
            vb_mix.addWidget(c)
        grp_mix.setLayout(vb_mix)
        vb.addWidget(grp_mix)

        # Routines speciales
        grp_spe = _section("Routines speciales")
        vb_spe = QVBoxLayout()
        self._cb_PT2Dx = _cb(
            "PT2Dx   -- Noeuds ponctuels 2D  (cables, barres elastiques)",
            tip="Interaction point/point 2D pour ELASTIC_WIRE, ELASTIC_ROD, etc.",
        )
        self._cb_PT3Dx = _cb(
            "PT3Dx   -- Noeuds ponctuels 3D",
            tip="Interaction point/point 3D.",
        )
        self._cb_NODES = _cb(
            "NODES   -- Noeuds couples  (DOF couples, COUPLED_DOF)",
            tip="Routines de couplage de degres de liberte entre noeuds.",
        )
        self._cb_bulk = _cb(
            "UpdateBulkBehav  -- Lois de comportement volumique",
            tip="Appel a chipy.UpdateBulkBehav() pour les lois plastiques, "
                "d'endommagement, etc.",
        )
        for c in (self._cb_PT2Dx, self._cb_PT3Dx, self._cb_NODES, self._cb_bulk):
            vb_spe.addWidget(c)
        grp_spe.setLayout(vb_spe)
        vb.addWidget(grp_spe)

        vb.addStretch()
        return _scroll(w)

    def _tab_advanced_routines(self) -> QWidget:
        """Options de calcul avancees, separees du cycle chipy obligatoire."""
        w = QWidget()
        vb = QVBoxLayout(w)
        vb.setSpacing(8)
        vb.addWidget(_note(
            "Les appels Initialize, ReadDatbox, ComputeFreeVelocity, WriteOut et "
            "les autres etapes indispensables restent automatiques. ReadDatbox "
            "charge deja les fichiers DAT/INI. Les options ci-dessous sont "
            "facultatives et ajoutees uniquement quand elles sont cochees."
        ))
        self._advanced_checks = {}
        self._advanced_edits = {}

        def add_group(title: str, options: list) -> None:
            group = _section(title)
            layout = QVBoxLayout()
            for option in options:
                key, label = option[:2]
                tip = option[2] if len(option) > 2 else ""
                checkbox = _cb(label, tip=tip)
                self._advanced_checks[key] = checkbox
                layout.addWidget(checkbox)
            group.setLayout(layout)
            vb.addWidget(group)

        add_group("Assemblage explicite par physique (MAILx)", [
            ("advanced_assemble_mechanical", "AssembleMechanicalLHS / RHS",
             "Appels explicites a chaque pas, uniquement si mecaMAILx est actif."),
            ("advanced_assemble_thermal", "AssembleThermalLHS / RHS",
             "Appels explicites a chaque pas, uniquement si therMAILx est actif."),
            ("advanced_assemble_poro", "AssemblePoroLHS / RHS",
             "Appels explicites a chaque pas, uniquement si poroMAILx est actif."),
            ("advanced_assemble_multi", "AssembleMultiLHS / RHS",
             "Appels explicites a chaque pas en physique THMx."),
        ])
        add_group("Contacts, forces et diagnostic", [
            ("advanced_fd_select_prox", "Utiliser FdSelectProxTactors",
             "Remplace la selection standard. Reserve aux contacts sphere/sphere."),
            ("advanced_compute_rnod", "Recalculer les reactions (ComputeRnod)",
             "Recalcule les reactions de contact apres la mise a jour du pas."),
            ("advanced_fatal_damping", "Activer FatalDamping",
             "Applique l'amortissement fatal a tous les corps a chaque pas."),
            ("advanced_smooth_force", "Activer SmoothForceComputation",
             "Recalcule explicitement les forces de contact apres resolution."),
            ("advanced_display_prox_tactors", "Afficher les contacteurs proches",
             "Appelle DisplayProxTactors a chaque pas."),
            ("advanced_display_out_dof", "Afficher les degres de liberte",
             "Appelle DisplayOutDof a chaque pas."),
            ("advanced_display_out_rnod", "Afficher les reactions (Rnod)",
             "Appelle DisplayOutRnod a chaque pas."),
            ("advanced_display_out_vloc_rloc", "Afficher les contacts (Vloc/Rloc)",
             "Appelle DisplayOutVlocRloc a chaque pas."),
        ])
        add_group("Sorties supplementaires", [
            ("advanced_hdf5", "Initialiser une sortie HDF5 (InitHDF5 / WriteHDF5)",
             "Ecrit aussi les resultats HDF5 a chaque pas d'ecriture."),
            ("advanced_write_out_dof", "WriteOutDof"),
            ("advanced_write_out_gpv", "WriteOutGPV"),
            ("advanced_write_out_mp_values", "WriteOutMpValues"),
            ("advanced_write_out_rnod", "WriteOutRnod"),
            ("advanced_write_out_vloc_rloc", "WriteOutVlocRloc"),
            ("advanced_write_last", "WriteLast"),
            ("advanced_write_last_dof", "WriteLastDof"),
            ("advanced_write_last_gpv", "WriteLastGPV"),
            ("advanced_write_last_mp_values", "WriteLastMpValues"),
            ("advanced_write_last_rnod", "WriteLastRnod"),
            ("advanced_write_last_vloc_rloc", "WriteLastVlocRloc"),
            ("advanced_add_dof2", "AddDof2InBodies avant WriteBodies",
             "Met a jour les coordonnees de reference avant l'ecriture des corps."),
            ("advanced_write_bodies", "WriteBodies"),
            ("advanced_write_behaviours", "WriteBehaviours"),
            ("advanced_write_driven_dof", "WriteDrivenDof"),
            ("advanced_write_mp_behaviours", "WriteMpBehaviours"),
        ])
        add_group("Affichage et post-traitement", [
            ("advanced_add_registers_to_display", "Ajouter les champs registres a l'affichage",
             "Active addRegistersToDisplay avant l'ouverture des fichiers display."),
            ("advanced_circular_selection", "Limiter le post-traitement a un disque",
             "Appelle CircularSelection(x, y, r) apres ReadDatbox."),
        ])

        args_form = QFormLayout()
        args_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        for key, label, default, tooltip in [
            ("advanced_hdf5_filename", "Fichier HDF5 :", "command.h5",
             "Nom du fichier HDF5 de sortie."),
            ("advanced_circular_selection_args", "Disque (x, y, r) :",
             "0.0, 0.0, 1.0", "Arguments Python de CircularSelection."),
            ("advanced_set_contact_radius_args", "SetContactRadius :", "",
             "Argument radius, par exemple 0.01."),
            ("advanced_set_domain_boundary_args", "SetDomainBoundary :",
             "", "Arguments nommes, par exemple Xmin=-1.0, Xmax=1.0."),
            ("advanced_set_number_interaction_args",
             "SetNumberInteractionByContact :", "",
             "Nombre d'interactions par contact."),
            ("advanced_set_periodic_condition_args", "SetPeriodicCondition :",
             "", "Arguments nommes, par exemple xperiod=1.0."),
        ]:
            edit = QLineEdit(self._params.get(key, default))
            edit.setToolTip(tooltip)
            self._advanced_edits[key] = edit
            args_form.addRow(label, edit)
        args_group = _section("Parametres des options avancees")
        args_group.setLayout(args_form)
        vb.addWidget(args_group)

        settings_group = _section("Reglages de contact")
        settings_layout = QVBoxLayout()
        for key, label in [
            ("advanced_set_contact_radius", "Configurer SetContactRadius"),
            ("advanced_set_domain_boundary", "Configurer SetDomainBoundary"),
            ("advanced_set_number_interaction",
             "Configurer SetNumberInteractionByContact (experimental)"),
            ("advanced_set_periodic_condition", "Configurer SetPeriodicCondition"),
        ]:
            checkbox = _cb(label)
            self._advanced_checks[key] = checkbox
            settings_layout.addWidget(checkbox)
        settings_group.setLayout(settings_layout)
        vb.addWidget(settings_group)

        vb.addStretch()
        self._refresh_advanced_routine_controls()
        return _scroll(w)

    def _refresh_advanced_routine_controls(self) -> None:
        if not hasattr(self, "_advanced_checks"):
            return
        availability = {
            "advanced_assemble_mechanical": self._cb_deformable.isChecked()
                and self._cb_mecaMAILx.isChecked(),
            "advanced_assemble_thermal": self._cb_deformable.isChecked()
                and self._cb_therMAILx.isChecked(),
            "advanced_assemble_poro": self._cb_deformable.isChecked()
                and self._cb_poroMAILx.isChecked()
                and self._combo_phys.currentIndex() != 3,
            "advanced_assemble_multi": self._cb_deformable.isChecked()
                and self._combo_phys.currentIndex() == 3,
        }
        for key, enabled in availability.items():
            self._advanced_checks[key].setEnabled(enabled)

    # ── Onglet 3 : Extraction ─────────────────────────────────────────────────

    def _tab_extract(self) -> QWidget:
        w = QWidget()
        vb = QVBoxLayout(w)
        vb.setSpacing(10)

        # ── 1. Logs chipy ─────────────────────────────────────────────────────
        grp_log = _section("Messages chipy  (logs)")
        vb_log = QVBoxLayout()
        self._cb_disable_log = _cb(
            "Desactiver les messages chipy  (utilities_DisableLogMes)",
            tip=(
                "Appelle chipy.utilities_DisableLogMes() apres Initialize(). "
                "Supprime tous les messages de progression dans la console. "
                "Utile en production ou pour les calculs tres longs."
            ),
        )
        vb_log.addWidget(self._cb_disable_log)
        grp_log.setLayout(vb_log)
        vb.addWidget(grp_log)

        # ── 2. Visualisation ──────────────────────────────────────────────────
        grp_vis = _section("Visualisation  (WriteDisplayFiles)")
        vb_vis = QVBoxLayout()
        self._cb_vRBDY2    = _cb("RBDY2_WriteDisplayFiles  -- Corps rigides 2D",
                                  checked=True)
        self._cb_vRBDY3    = _cb("RBDY3_WriteDisplayFiles  -- Corps rigides 3D")
        self._cb_vMeca     = _cb("mecaMAILx_WriteDisplayFiles  -- Deformables mecanique")
        self._cb_vTher     = _cb("therMAILx_WriteDisplayFiles  -- Deformables thermique")
        self._cb_vHydr     = _cb("poroMAILx_WriteDisplayFiles  -- Deformables hydraulique")
        self._cb_disp_loop = _cb(
            "Ecrire les fichiers display dans la boucle de calcul",
            checked=True,
            tip=(
                "Decocher pour n'ecrire qu'une seule fois a la fin du calcul. "
                "Utile pour les grands calculs."
            ),
        )
        for c in (self._cb_vRBDY2, self._cb_vRBDY3, self._cb_vMeca,
                  self._cb_vTher, self._cb_vHydr, self._cb_disp_loop):
            vb_vis.addWidget(c)
        grp_vis.setLayout(vb_vis)
        vb.addWidget(grp_vis)

        # ── 3. Visibilite des avatars ─────────────────────────────────────────
        grp_visi = _section("Visibilite des avatars  (SetVisible / SetInvisible)")
        vb_visi = QVBoxLayout()

        # En-tete colonnes
        hdr_vis = QHBoxLayout()
        for _lbl_v, _w_v in [
            ("Action",        110),
            ("Dim.",           50),
            ("IDs avatars",   120),
            ("Groupe",        110),
            ("Mode / Timing", 200),
        ]:
            _lv = QLabel("<b>{}</b>".format(_lbl_v))
            _lv.setFixedWidth(_w_v)
            hdr_vis.addWidget(_lv)
        hdr_vis.addStretch()
        vb_visi.addLayout(hdr_vis)

        # Zone de lignes
        self._vis_rows = []
        self._vis_rows_widget = QWidget()
        self._vis_rows_layout = QVBoxLayout(self._vis_rows_widget)
        self._vis_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._vis_rows_layout.setSpacing(2)
        vb_visi.addWidget(self._vis_rows_widget)

        btn_add_vis = QPushButton("+ Creer une visibilite")
        btn_add_vis.clicked.connect(lambda: self._add_vis_row())
        vb_visi.addWidget(btn_add_vis)
        vb_visi.addWidget(_note(
            "chipy.RBDY2_SetVisible(id) / chipy.RBDY2_SetInvisible(id) appeles avant "
            "ou pendant la boucle selon le mode choisi. "
            "IDs ou groupe : si les deux sont remplis les IDs ont la priorite."
        ))
        grp_visi.setLayout(vb_visi)
        vb.addWidget(grp_visi)

        # ── 4. GetBodyVector RBDY2 ────────────────────────────────────────────
        grp_gbv2 = _section(
            "Extraction vecteurs d'etat RBDY2  (RBDY2_GetBodyVector)"
        )
        grp_gbv2.setToolTip(
            "chipy.RBDY2_GetBodyVector(vecteur, id_avatar) retourne le vecteur "
            "d'etat de l'avatar id. Le script genere une boucle for sur les IDs."
        )
        vb_gbv2 = QVBoxLayout()
        self._gbv2_rows = []

        hdr2 = QHBoxLayout()
        for _lbl, _w in [("Vecteur", 110), ("IDs avatars", 120),
                          ("Groupe", 110), ("Mode / Timing", 200)]:
            _l = QLabel("<b>{}</b>".format(_lbl))
            _l.setFixedWidth(_w)
            hdr2.addWidget(_l)
        hdr2.addStretch()
        vb_gbv2.addLayout(hdr2)

        self._gbv2_rows_widget = QWidget()
        self._gbv2_rows_layout = QVBoxLayout(self._gbv2_rows_widget)
        self._gbv2_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._gbv2_rows_layout.setSpacing(2)
        vb_gbv2.addWidget(self._gbv2_rows_widget)

        btn_add2 = QPushButton("+ Ajouter une extraction RBDY2")
        btn_add2.clicked.connect(lambda: self._add_gbv_row("2D"))
        vb_gbv2.addWidget(btn_add2)
        vb_gbv2.addWidget(_note(
            "Vecteurs : Coor0, Coor_, Coorb, Coorm, X____, V____, Vbeg_, Vfree, "
            "Fext, Fint_, Reac, Ireac.  "
            "Le generateur produit une boucle for sur les IDs ou sur le groupe."
        ))
        grp_gbv2.setLayout(vb_gbv2)
        vb.addWidget(grp_gbv2)

        # ── 5. GetBodyVector RBDY3 ────────────────────────────────────────────
        grp_gbv3 = _section(
            "Extraction vecteurs d'etat RBDY3  (RBDY3_GetBodyVector)"
        )
        grp_gbv3.setToolTip(
            "chipy.RBDY3_GetBodyVector(vecteur, id_avatar) -- memes vecteurs que RBDY2."
        )
        vb_gbv3 = QVBoxLayout()
        self._gbv3_rows = []

        hdr3 = QHBoxLayout()
        for _lbl, _w in [("Vecteur", 110), ("IDs avatars", 120),
                          ("Groupe", 110), ("Mode / Timing", 200)]:
            _l = QLabel("<b>{}</b>".format(_lbl))
            _l.setFixedWidth(_w)
            hdr3.addWidget(_l)
        hdr3.addStretch()
        vb_gbv3.addLayout(hdr3)

        self._gbv3_rows_widget = QWidget()
        self._gbv3_rows_layout = QVBoxLayout(self._gbv3_rows_widget)
        self._gbv3_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._gbv3_rows_layout.setSpacing(2)
        vb_gbv3.addWidget(self._gbv3_rows_widget)

        btn_add3 = QPushButton("+ Ajouter une extraction RBDY3")
        btn_add3.clicked.connect(lambda: self._add_gbv_row("3D"))
        vb_gbv3.addWidget(btn_add3)
        vb_gbv3.addWidget(_note(
            "Memes vecteurs que RBDY2. "
            "Le generateur produit une boucle for sur les IDs ou sur le groupe."
        ))
        grp_gbv3.setLayout(vb_gbv3)
        vb.addWidget(grp_gbv3)

        # ── 6. Forces de contact ──────────────────────────────────────────────
        grp_frc = _section("Forces et reactions de contact")
        vb_frc = QVBoxLayout()
        self._cb_Rnod = _cb(
            "Forces nodales         (inter_handler_Rnod)",
            tip="Extrait les forces nodales aux points de contact dans POSTPRO/.",
        )
        self._cb_Vloc = _cb(
            "Vitesses locales       (inter_handler_Vloc)",
            tip="Extrait les vitesses relatives dans le repere local de contact.",
        )
        self._cb_Rloc = _cb(
            "Forces locales         (inter_handler_Rloc)",
            tip="Extrait les impulsions/forces dans le repere local de contact.",
        )
        for c in (self._cb_Rnod, self._cb_Vloc, self._cb_Rloc):
            vb_frc.addWidget(c)
        grp_frc.setLayout(vb_frc)
        vb.addWidget(grp_frc)

        # ── 7. Energie ────────────────────────────────────────────────────────
        grp_nrj = _section("Energie")
        vb_nrj = QVBoxLayout()
        self._cb_energy = _cb(
            "Bilan energetique global  (ComputeEnergy + WriteEnergy)",
            tip=(
                "Calcule et ecrit l'energie totale : "
                "cinetique + potentielle + dissipee par friction."
            ),
        )
        self._cb_KE = _cb(
            "Energie cinetique RBDY2  (RBDY2_KineticEnergy)",
            tip="Ecrit l'energie cinetique de chaque corps rigide 2D.",
        )
        for c in (self._cb_energy, self._cb_KE):
            vb_nrj.addWidget(c)
        grp_nrj.setLayout(vb_nrj)
        vb.addWidget(grp_nrj)

        # ── 8. Champs FEM ─────────────────────────────────────────────────────
        grp_fld = _section(
            "Champs MAILx  (contraintes, deformations, temperature...)"
        )
        vb_fld = QVBoxLayout()
        self._cb_fields = _cb(
            "Champs par element        (mecaMAILx_WriteBodies)",
            tip=(
                "Ecrit les champs par element : contraintes et deformations "
                "(MECAx), temperature (THERx), pression (POROx)."
            ),
        )
        self._cb_internal = _cb(
            "Variables internes        (mecaMAILx_WriteInternalVariables)",
            tip=(
                "Ecrit les variables internes aux points de Gauss : "
                "plasticite, endommagement, variables d'histoire."
            ),
        )
        vb_fld.addWidget(self._cb_fields)
        vb_fld.addWidget(self._cb_internal)
        vb_fld.addWidget(_note(
            "Ces extractions ne sont actives que si "
            "'mecaMAILx' est coche dans l'onglet Routines."
        ))
        grp_fld.setLayout(vb_fld)
        vb.addWidget(grp_fld)

        vb.addStretch()
        return _scroll(w)

    # ── Onglet 4 : Pilotage ───────────────────────────────────────────────────

    def _tab_pilot(self) -> QWidget:
        w = QWidget()
        vb = QVBoxLayout(w)
        vb.setSpacing(10)

        # Restart
        grp_rs = _section("Restart  --  Reprise de calcul")
        fl_rs = QFormLayout()
        self._cb_restart = _cb(
            "Activer le restart",
            tip=(
                "Charge l'etat depuis les fichiers .dat.last "
                "d'un calcul precedent avant de demarrer la boucle."
            ),
        )
        fl_rs.addRow(self._cb_restart)
        self._spin_rs_step = QSpinBox()
        self._spin_rs_step.setRange(0, 9_999_999)
        self._spin_rs_step.setValue(0)
        self._spin_rs_step.setEnabled(False)
        self._spin_rs_step.setToolTip(
            "Numero du pas de temps a partir duquel reprendre."
        )
        fl_rs.addRow("Pas de reprise :", self._spin_rs_step)
        fl_rs.addRow(_note(
            "Genere :  chipy.ReadIni()  +  chipy.SetStep(restart_step) "
            "avant la boucle de calcul."
        ))
        grp_rs.setLayout(fl_rs)
        vb.addWidget(grp_rs)

        # Critere d'arret
        grp_sc = _section("Critere d'arret automatique")
        fl_sc = QFormLayout()
        self._cb_stop = _cb(
            "Activer un critere d'arret",
            tip=(
                "Interrompt le calcul avant la fin des pas "
                "si le critere est satisfait."
            ),
        )
        fl_sc.addRow(self._cb_stop)
        self._combo_stop_type = QComboBox()
        self._combo_stop_type.addItems([
            "Energie residuelle      ||E_res|| < seuil",
            "Deplacement max         max|u|   < seuil",
            "Residu de force         ||F_res|| < seuil",
        ])
        self._combo_stop_type.setEnabled(False)
        fl_sc.addRow("Type de critere :", self._combo_stop_type)
        self._dspin_stop_val = QDoubleSpinBox()
        self._dspin_stop_val.setRange(1e-16, 1.0)
        self._dspin_stop_val.setDecimals(2)
        self._dspin_stop_val.setValue(1e-6)
        self._dspin_stop_val.setSingleStep(1e-7)
        self._dspin_stop_val.setEnabled(False)
        fl_sc.addRow("Seuil :", self._dspin_stop_val)
        self._spin_stop_freq = QSpinBox()
        self._spin_stop_freq.setRange(1, 100_000)
        self._spin_stop_freq.setValue(10)
        self._spin_stop_freq.setEnabled(False)
        self._spin_stop_freq.setToolTip("Evaluer le critere tous les N pas.")
        fl_sc.addRow("Frequence d'evaluation (pas) :", self._spin_stop_freq)
        grp_sc.setLayout(fl_sc)
        vb.addWidget(grp_sc)

        # Multi-pas
        grp_mp = _section("Sequence multi-pas  --  dt variable")
        fl_mp = QFormLayout()
        self._cb_multi = _cb(
            "Activer une sequence de pas de temps variables",
            tip=(
                "Definit plusieurs phases de calcul avec des dt differents. "
                "Genere une boucle externe sur les phases."
            ),
        )
        fl_mp.addRow(self._cb_multi)
        self._spin_mp_nb = QSpinBox()
        self._spin_mp_nb.setRange(2, 20)
        self._spin_mp_nb.setValue(3)
        self._spin_mp_nb.setEnabled(False)
        fl_mp.addRow("Nombre de phases :", self._spin_mp_nb)
        self._edit_mp_sizes = QLineEdit("1e-3, 1e-4, 1e-5")
        self._edit_mp_sizes.setPlaceholderText(
            "Ex : 1e-3, 1e-4, 1e-5  (un dt par phase, separes par virgules)"
        )
        self._edit_mp_sizes.setEnabled(False)
        fl_mp.addRow("dt par phase :", self._edit_mp_sizes)
        fl_mp.addRow(_note(
            "nb_steps est reparti equitablement entre les phases. "
            "Genere :  for _dt in dt_sequence: "
            "chipy.TimeEvolution_SetTimeStep(_dt) + boucle interne."
        ))
        grp_mp.setLayout(fl_mp)
        vb.addWidget(grp_mp)

        vb.addStretch()
        return _scroll(w)


    # =========================================================================
    # Catalogues de fonctions chipy pour l'inspection
    # =========================================================================

    # ── Contacteurs 2D : (nom_chipy, description, nb_params)
    # nb_params : 0 = pas d'ID, 1 = ID contacteur, 2 = ID corps
    _INSP2D_FUNCS = [
        # ---- DISKx ---------------------------------------------------------
        ("DISKx_GetNbDISKx",          "Nombre total de contacteurs DISKx",                    0),
        ("DISKx_GetPtrDISKx2BDYTY",   "Index local du contacteur dans son corps RBDY2",       1),
        ("DISKx_GetNbPointOutlines",     "Nombre de points d'outline du disque i",         1),
        ("DISKx_GetRadius",           "Rayon du disque i",                                    1),
        ("DISKx_GetNbScalarFields",             "Nombre de champs scalaires",                    1),
        ("DISKx_GetDISKx2BDYTY",         "Description de DISKx2BDYTY",                        1),
        ("DISKx_GetMaxRadius","Rayon maximum du disque i", 1),
        ("DISKx_GetMeanRadius","Rayon moyen du disque i", 1),
        ("DISKx_GetMinRadius","Rayon minimum du disque i", 1),
        ("DISKx_GetContactorColor","Couleur du contacteur", 1),
        ("DISKx_GetContactorCoor","Coordonnees du contacteur", 1),
        ("DISKx_GetContactorRadius","Rayon du contacteur", 1),  

        # ---- JONCx ---------------------------------------------------------
        ("JONCx_GetNbJONCx",          "Nombre total de contacteurs JONCx (joncs/ellipses)",   0),
        ("JONCx_GetBodyId",           "ID corps RBDY2 du jonc i",                             1),
        ("JONCx_GetPtrJONCx2BDYTY",   "Index local du jonc dans son corps RBDY2",             1),
        ("JONCx_GetNbScalarFields",     "Nombre de champs scalaires",               1),
        ("JONCx_GetShape",             "Forme du jonc i",                           1),
        ("JONCx_GetCoor",             "Coordonnees du centre du jonc i",                      1),
        ("JONCx_GetNbPointOutlines",     "Nombre de points d'outline du jonc i",         1),
        # -----POLYG ---------------------------------------------------------
        ("POLYG_GetNbPOLYG",          "Nombre total de contacteurs POLYG (polygones)", 0),
        ("POLYG_GetBodyId",           "ID corps RBDY2 du polygone i",                         1),
        ("POLYG_GetContactorRadius", "Rayon du contacteur POLYG i", 1),
        ("POLYG_GetMaxRadius", "Rayon maximum du contacteur POLYG i", 1),
        ("POLYG_GetMinRadius", "Rayon minimum du contacteur POLYG i", 1),
        ("POLYG_GetNbPointOutlines",     "Nombre de points d'outline du polygone i",         1),
        ("POLYG_GetNbScalarFields",             "Nombre de champs scalaires",                    1),
        ("POLYG_GetNbVertex",          "Nombre de sommets du polygone i",                      1),
        ("POLYG_GetNbVertices",          "Nombre de segments du polygone i",                      1),
        ("POLYG_GetPOLYG2BDYTY",         "Description de POLYG2BDYTY",                        1),
        ("POLYG_GetPtrPOLYG2BDYTY",   "Index local du polygone dans son corps RBDY2",         1),
        ("POLYG_GetVertex",            "Coordonnees des sommets du polygone i",                1),
        ("POLYG_GetVertices",            "Coordonnees des segments du polygone i",                1),
        # ---- xKSID (creux) ----------------------------------------
        ("xKSID_GetContactorCoor",    "Coordonnees du contacteur xKSID i",                    1),
        ("xKSID_GetContactorRadius",   "Rayon du contacteur xKSID i",                         1),
        ("xKSID_GetNbPointOutlines",   "Nombre de points d'outline du contacteur xKSID i",     1),
        ("xKSID_GetNbScalarFields",    "Nombre de champs scalaires du contacteur xKSID i",      1),
        ("xKSID_GetNbxKSID",           "Nombre total de contacteurs xKSID (disques discrets)", 1),
        ("xKSID_GetPtrxKSID2BDYTY",    "Index local du xKSID dans son corps RBDY2",            1),
        # ---- Rigid Body Dynamics 2 (RBDY2) -------------------------------------
        ("RBDY2_GetAllArea", "Aires de tous les corps RBDY2", 0),
        ("RBDY2_GetAllBodyVector", "Vecteurs de tous les corps RBDY2", 1),
        ("RBDY2_GetAllInertia", "Inerties de tous les corps RBDY2", 0),
        ("RBDY2_GetAllMass", "Masses de tous les corps RBDY2", 0),
        ("RBDY2_GetAverageSurfaceEnergy", "Energie moyenne de surface RBDY2", 0),
        ("RBDY2_GetBetai", "Betai des corps RBDY2", 0),
        ("RBDY2_GetBodyArea", "Aire des corps RBDY2", 0),
        ("RBDY2_GetBodyDensity", "Densite des corps RBDY2", 0),
        ("RBDY2_GetBodyInertia", "Inertie des corps RBDY2", 0),
        ("RBDY2_GetBodyMass", "Masse des corps RBDY2", 0),
        ("RBDY2_GetBodyVector", "Vecteur des corps RBDY2", 1),
        ("RBDY2_GetBulkBehavID", "ID du comportement massif RBDY2", 0),
        ("RBDY2_GetBulkBehavNumber", "Nombre de comportements massifs RBDY2", 0),
        ("RBDY2_GetContactorColor", "Couleur du contacteur RBDY2", 0),
        ("RBDY2_GetContactorType", "Type du contacteur RBDY2", 0),
        ("RBDY2_GetElectricalCurrent", "Courant electrique RBDY2", 0),
        ("RBDY2_GetElectricalPotential", "Potentiel electrique RBDY2", 0),
        ("RBDY2_GetNbContactor", "Nombre de contacteurs RBDY2", 0),
        ("RBDY2_GetNbRBDY2", "Nombre total de corps RBDY2", 0),
        ("RBDY2_GetPeriode", "Periode RBDY2", 0),
        ("RBDY2_GetPtrBodyVector", "Pointeur vers le vecteur des corps RBDY2", 0),
        ("RBDY2_GetPtrMass", "Pointeur vers la masse des corps RBDY2", 0),
        ("RBDY2_GetStress", "Contraintes RBDY2", 0),
        ("RBDY2_GetThermalValue", "Valeur thermique RBDY2", 0),
        ("RBDY2_GetVelocity", "Vitesse RBDY2", 1),
        # ---- RBDY2 corps ---------------------------------------------------
        ("PT2DL_GetBody",          "ID du corps RBDY2 parent du contacteur PT2DL i",         1),
        ("PT2DL_GetNbPT2DL",          "Nombre total de contacteurs PT2DL",                     0),
        ("PT2DL_GetNbPT2TL",          "Nombre total de contacteurs PT2TL",                     0),
        ("PT2Dx_GetNbPT2Dx",          "Nombre de noeuds contacteurs 2D (MAILx)",                0),
        ("PT2Dx_GetNbPointOutlines",  "Nombre de points d'outline du noeud 2D i",              1),
        ("PT2Dx_GetNbScalarFields",   "Nombre de champs scalaires du noeud 2D i",             1),
        ("PT2Dx_GetPtrPT2Dx2BDYTY",   "Index local du noeud 2D dans son corps RBDY2",         1),
    ]

    # ── Contacteurs 3D
    _INSP3D_FUNCS = [
        # ---- SPHER ---------------------------------------------------------
        ("SPHER_GetContactorCoor",    "Coordonnées du contacteur SPHER i",                     1),
        ("SPHER_GetContactorCoorb",   "Coordonnées du contacteur SPHER i (version b)",         1),
        ("SPHER_GetContactorRadius",  "Rayon du contacteur SPHER i",                          1),
        ("SPHER_GetNbPointOutlines",  "Nombre de points d'outline du contacteur SPHER i",      1),
        ("SPHER_GetNbSPHER",          "Nombre total de contacteurs SPHER (spheres)",           0),
        ("SPHER_GetNbScalarFields",   "Nombre de champs scalaires du contacteur SPHER i",      1),
        ("SPHER_GetPtrAllConnectivities", "Pointeur vers toutes les connectivités du contacteur SPHER i", 1),
        ("SPHER_GetPtrSPHER2BDYTY",   "Index local du contacteur SPHER dans son corps RBDY3",          1),
        ("SPHER_GetSPHER2BDYTY",      "Description de SPHER2BDYTY",                            1),

        # ---- POLYR ---------------------------------------------------------
        ("POLYR_GetNbPOLYR",          "Nombre total de contacteurs POLYR (polygones rigides)", 0),
        ("POLYR_GetContactorColor", "Couleur du contacteur POLYR i", 1),
        ("POLYR_GetNbPointOutlines", "Nombre de points d'outline du polygone rigide i", 1),
        ("POLYR_GetNbScalarFields", "Nombre de champs scalaires du polygone rigide i", 1),
        ("POLYR_GetPOLYR2BDYTY", "Description de POLYR2BDYTY", 1),
        ("POLYR_GetPtrAllConnectivities", "Pointeur vers toutes les connectivités du polygone rigide i", 1),
        ("POLYR_GetPtrConnectivity", "Pointeur vers la connectivité du polygone rigide i", 1),
        ("POLYR_GetPtrNormalTT", "Pointeur vers le vecteur normal du polygone rigide i", 1),
        ("POLYR_GetPtrPOLYR2BDYTY", "Index local du polygone rigide dans son corps RBDY2", 1),
        ("POLYR_GetPtrVertexRef", "Pointeur vers le sommet de référence du polygone rigide i", 1),
        ("POLYR_GetPtrVertexTT", "Pointeur vers le sommet du polygone rigide i", 1),
        ("POLYR_GetTopoData", "Données topologiques du polygone rigide i", 1),
        ("POLYR_GetVertex", "Coordonnées des sommets du polygone rigide i", 1),
        ("POLYR_GetWireframe", "Données du fil de fer du polygone rigide i", 1),  
        # ---- CYLND ---------------------------------------------------------
        ("CYLND_GetNbCYLND",          "Nombre total de contacteurs CYLND (cylindres)",         0),
        ("CYLND_GetNbPointOutlines",  "Nombre de points d'outline du cylindre i",              1),
        ("CYLND_GetNbScalarFields",   "Nombre de champs scalaires du cylindre i",             1),
        ("CYLND_GetPtrAllConnectivities", "Pointeur vers toutes les connectivités du cylindre i", 1),
        ("CYLND_GetPtrCYLND2BDYTY",   "Index local du cylindre dans son corps RBDY3",          1),
        ("CYLND_GetShape",            "Description de CYLND2BDYTY",                            1),
        # ---- PLANE 3D (parois planes) ----------------------------------------
        ("PLANx_GetNbPLANx",          "Nombre total de contacteurs PLANx (plans rigides 3D)",  0),
        ("PLANx_GetNbPointOutlines",  "Nombre de points d'outline du plan i",              1),
        ("PLANx_GetNbScalarFields",   "Nombre de champs scalaires du plan i",             1),
        ("PLANx_GetPtrAllConnectivities", "Pointeur vers toutes les connectivités du plan i", 1),
        ("PLANx_GetPtrPLANx2BDYTY",   "Index local du plan dans son corps RBDY3",          1),
        # ---- DNLYC (creux) -------------------------------------------------
        ("DNLYC_GetNbDNLYC",          "Nombre total de contacteurs DNLYC (lignes)",          0),
        ("DNLYC_GetNbPointOutlines",  "Nombre de points d'outline de la ligne i",              1),
        ("DNLYC_GetNbScalarFields",   "Nombre de champs scalaires de la ligne i",             1),
        ("DNLYC_GetPtrAllConnectivities", "Pointeur vers toutes les connectivités de la ligne i", 1),
        ("DNLYC_GetPtrDNLYC2BDYTY",   "Index local de la ligne dans son corps RBDY3",          1),
        
        # ---- RBDY3 corps ---------------------------------------------------
        ("RBDY3_GetAllBodyVector", "Vecteurs de tous les corps RBDY3", 0),
        ("RBDY3_GetAllInertia", "Inerties de tous les corps RBDY3", 0),
        ("RBDY3_GetAllMass", "Masses de tous les corps RBDY3", 0),
        ("RBDY3_GetAllRData", "Données de tous les corps RBDY3", 0),
        ("RBDY3_GetAllVolume", "Volumes de tous les corps RBDY3", 0),
        ("RBDY3_GetBehavior", "Comportement des corps RBDY3", 0),
        ("RBDY3_GetBodyDensity", "Densité des corps RBDY3", 0),
        ("RBDY3_GetBodyInertia", "Inertie des corps RBDY3", 0),
        ("RBDY3_GetBodyMatrix", "Matrice des corps RBDY3", 0),
        ("RBDY3_GetBodyVector", "Vecteur des corps RBDY3", 0),
        ("RBDY3_GetBulkBehavNumber", "Nombre de comportements massifs RBDY3", 0),
        ("RBDY3_GetContactorColor", "Couleur des contacteurs RBDY3", 0),
        ("RBDY3_GetContactorType", "Type des contacteurs RBDY3", 0),
        ("RBDY3_GetDofStatus", "Statut des degrés de liberté RBDY3", 0),
        ("RBDY3_GetGlobInertia", "Inertie globale RBDY3", 0),
        ("RBDY3_GetMass", "Masse des corps RBDY3", 0),
        ("RBDY3_GetNbContactor", "Nombre de contacteurs RBDY3", 0),
        ("RBDY3_GetNbRBDY3", "Nombre total de corps rigides 3D", 0),
        ("RBDY3_GetPtrBodyVector", "Pointeur vers le vecteur des corps RBDY3", 0),
        ("RBDY3_GetPtrMass", "Pointeur vers la masse des corps RBDY3", 0),
        ("RBDY3_GetThermalValue", "Valeur thermique RBDY3", 0),
        ("RBDY3_GetVelocity", "Vitesse des corps RBDY3", 0),
        ("RBDY3_GetVolume", "Volume des corps RBDY3", 0),
        # ---- PT3Dx noeuds MAILx 3D -------------------------------------------
        ("PT3Dx_GetNbPT3Dx",          "Nombre de noeuds contacteurs 3D (MAILx)",                0),
        ("PT3Dx_GetNbPointOutlines",  "Nombre de points d'outline du noeud 3D i",              1),
        ("PT3Dx_GetNbScalarFields",   "Nombre de champs scalaires du noeud 3D i",             1),
        ("PT3Dx_GetPtrAllConnectivities", "Pointeur vers toutes les connectivités du noeud 3D i", 1),
        ("PT3Dx_GetPtrPT3Dx2BDYTY",   "Index local du noeud 3D dans son corps RBDY3",          1),
    ]

    # ── Interactions (paires de contacteurs)
    _INSPI_FUNCS = [
        ("GetDimension", "Dimension du projet (2D ou 3D)", 0),
        ("timer_GetNewTimer", "Creer un nouveau timer", 0),
        ("TimeEvolution_GetStep", "Pas de temps de l'evolution temporelle", 0),
        ("TimeEvolution_GetTime", "Temps de l'evolution temporelle", 0),
        ("TimeEvolution_GetTimeStep", "Pas de temps de l'evolution temporelle", 0),
        # ---- DKDKx (Disque-Disque) -----------------------------------------
        ("DKDKx_GetCZMEnergy", "Energie de contact DKDKx i",                             1),
                ("PLPLx_GetCZMEnergy",        "Energie de contact PLPLx i",              1),
        # ---- PRPRx (polyhedre-polyhedre) ----------------------------------------
        ("PRPRx_GetF2f2Inters",        "Intersections F2f de la paire i",                       1),
        ("PRPRx_GetF2fAllIdata",       "Données d'interaction F2f de la paire i",                1),
        ("PRPRx_GetF2fCentralKernel",  "Noyau central F2f de la paire i",                        1),
        ("PRPRx_GetF2fOutlines",       "Contours F2f de la paire i",                            1),
        ("PRPRx_GetF2fStress",         "Contraintes F2f de la paire i",                         1),
        ("PRPRx_GetInteractionInternal", "Données internes d'interaction de la paire i",            1),
        ("PRPRx_GetInteractionInternalComment", "Commentaires sur les données internes d'interaction de la paire i", 1),
        ("PRPRx_GetInteractionVector", "Vecteur d'interaction de la paire i",                    1),
        ("PRPRx_GetNbF2f",            "Nombre d'intersections F2f de la paire i",              1),
        # ---- CLALp (Brique-Brique maconnerie) --------------------------------
        # ----  2D contacteurs ----------------------------------------------------
        ("ALpxx_GetAllConnec", "Liste des connectivites de tous les contacteurs ALpxx", 0),
        ("ALpxx_GetAllData", "Donnees de tous les contacteurs ALpxx", 0),
        # ----  ASPxx ----------------------------------------------------
        ("ASpxx_GetAllConnec", "Liste des connectivites de tous les contacteurs ASpxx", 0),
        ("ASpxx_GetAllData", "Donnees de tous les contacteurs ASpxx", 0),
        # ---- CLpxx ---------------------------------------------------------
        ("CLpxx_GetAllConnec", "Liste des connectivites de tous les contacteurs CLpxx", 0),
        ("CLpxx_GetAllData", "Donnees de tous les contacteurs CLpxx", 0),
        ("CLxxx_GetNbCLxxx", "Nombre total de contacteurs CLxxx", 0),
        # ---- CSPRx ---------------------------------------------------------
        ("CSPRx_GetInfo", "Informations sur le contacteur CSPRx", 0),
        ("CSpxx_GetAllConnec", "Liste des connectivites de tous les contacteurs CSpxx", 0),
        ("CSpxx_GetAllData", "Donnees de tous les contacteurs CSpxx", 0),
        # ---- CSxxx ---------------------------------------------------------
        ("CSxxx_GetNbCSxxx", "Nombre total de contacteurs CSxxx", 0),
        # ---- Déformables MAILx (2D et 3D) ----------------------------------------
        ("MAILx_GetCoordNodty", "Coordonnees des noeuds MAILx i", 1),
        ("MAILx_GetCoordsNodty", "Coordonnees des noeuds MAILx i", 1),
        ("MAILx_GetNbCell", "Nombre de cellules MAILx i", 1),
        ("MAILx_GetNbMAILx", "Nombre total de contacteurs MAILx", 0),
        ("MAILx_GetNbNodes", "Nombre de noeuds MAILx i", 1),
        # ---- Comportements massifs -------------------------------------------------
        ("bulk_behav_GetBulkBehav", "Comportement massif", 0),
        ("bulk_behav_GetGravity", "Gravite", 0),
        ("bulk_behav_GetNbBulkBehav", "Nombre de comportements massifs", 0),
        # ---- Post-traitement ---------------------------------------------------
        ("postpro_2D_GetKineticEnergy", "Énergie cinétique 2D", 1),
        ("postpro_3D_GetKineticEnergy", "Énergie cinétique 3D", 1),
        ("postpro_3D_GetRBDY3PrincStress", "Contraintes principales RBDY3 3D", 1),
        # ---- Comportements de contact ------------------------------------------
        ("tact_behav_GetInternalComment", "Commentaires sur les données internes de contact", 1),
        ("tact_behav_GetLawInternalComment", "Commentaires sur les lois de contact", 1),
        ("tact_behav_GetNbTactBehav", "Nombre de comportements de contact", 1),
        ("tact_behav_GetParam", "Paramètres du comportement de contact", 1),
        ("tact_behav_GetParamRankFromName", "Rang du paramètre du comportement de contact à partir de son nom", 1),
        ("tact_behav_GetTactBehav", "Comportement de contact", 1),
        ("tact_behav_GetTactBehavRankFromName", "Rang du comportement de contact à partir de son nom", 1),
        # --- MAILx thermique
        ("therMAILx_GetAll", "Toutes les données du MAILx thermique", 1),
        ("therMAILx_GetBodyVector", "Vecteur de corps du MAILx thermique", 1),
        ("therMAILx_GetConnectivity", "Connectivité du MAILx thermique", 1),
        ("therMAILx_GetCoor", "Coordonnées du MAILx thermique", 1),
        ("therMAILx_GetFlux", "Flux du MAILx thermique", 1),
        ("therMAILx_GetGpCoor", "Coordonnées des points d'intégration du MAILx thermique", 1),
        ("therMAILx_GetGpField", "Champ scalaire des points d'intégration du MAILx thermique", 1),
        ("therMAILx_GetGrad", "Gradients du MAILx thermique", 1),
        ("therMAILx_GetNbDofs", "Nombre de degrés de liberté du MAILx thermique", 1),
        ("therMAILx_GetNbElements", "Nombre d'éléments du MAILx thermique", 1),
        ("therMAILx_GetNbGp", "Nombre de points d'intégration du MAILx thermique", 1),
        ("therMAILx_GetNbGpByElem", "Nombre de points d'intégration par élément du MAILx thermique", 1),
        ("therMAILx_GetNbNodes", "Nombre de noeuds du MAILx thermique", 1),
        ("therMAILx_GetNbTherMAILx", "Nombre de MAILx thermiques", 1),
        ("therMAILx_GetScalarFieldRank", "Rang du champ scalaire du MAILx thermique", 1),
        ("therMAILx_GetVectorFieldRank", "Rang du champ vectoriel du MAILx thermique", 1),
        # --- POROx --------------------------------------------------------
        ("poroMAILx_GetAll", "Toutes les données du MAILx poro", 1),
        ("poroMAILx_GetBodyVector", "Vecteur de corps du MAILx poro", 1),
        ("poroMAILx_GetConnectivity", "Connectivité du MAILx poro", 1),
        ("poroMAILx_GetCoor", "Coordonnées du MAILx poro", 1),
        ("poroMAILx_GetFlux", "Flux du MAILx poro", 1),
        ("poroMAILx_GetGrad", "Gradients du MAILx poro", 1),
        ("poroMAILx_GetInternal", "Données internes du MAILx poro", 1),
        ("poroMAILx_GetMecaScalarFieldRank", "Rang du champ scalaire mécanique du MAILx poro", 1),
        ("poroMAILx_GetMecaVectorFieldRank", "Rang du champ vectoriel mécanique du MAILx poro", 1),
        ("poroMAILx_GetNbElements", "Nombre d'éléments du MAILx poro", 1),
        ("poroMAILx_GetNbGpByElem", "Nombre de points d'intégration par élément du MAILx poro", 1),
        ("poroMAILx_GetNbNodes", "Nombre de noeuds du MAILx poro", 1),
        ("poroMAILx_GetNbPoroMAILx", "Nombre de MAILx poro", 1),
        ("poroMAILx_GetStrain", "Déformations du MAILx poro", 1),
        ("poroMAILx_GetStress", "Contraintes du MAILx poro", 1),
        ("poroMAILx_GetTherScalarFieldRank", "Rang du champ scalaire thermique du MAILx poro", 1),
        ("poroMAILx_GetTherVectorFieldRank", "Rang du champ vectoriel thermique du MAILx poro", 1),
        # --- multiMAILx ------------------------------------------------------
        ("multiMAILx_GetAll", "Toutes les données du MAILx multi", 1),
        ("multiMAILx_GetBodyVector", "Vecteur de corps du MAILx multi", 1),
        ("multiMAILx_GetConnectivity", "Connectivité du MAILx multi", 1),
        ("multiMAILx_GetCoor", "Coordonnées du MAILx multi", 1),
        ("multiMAILx_GetDeformationEnergy", "Énergie de déformation du MAILx multi", 1),
        ("multiMAILx_GetElementsNeighbor", "Voisins des éléments du MAILx multi", 1),
        ("multiMAILx_GetElementsVolume", "Volume des éléments du MAILx multi", 1),
        ("multiMAILx_GetNb", "Nombre de MAILx multi", 1),
        ("multiMAILx_GetNbElements", "Nombre d'éléments du MAILx multi", 1),
        ("multiMAILx_GetNbNodes", "Nombre de noeuds du MAILx multi", 1),
        ("multiMAILx_GetPtrBoundaryElements", "Pointeurs vers les éléments de bord du MAILx multi", 1),
        ("multiMAILx_GetPtrElementsEnergy", "Pointeurs vers les énergies des éléments du MAILx multi", 1),
        ("multiMAILx_GetPtrElementsJacobian", "Pointeurs vers les Jacobiens des éléments du MAILx multi", 1),
        ("multiMAILx_GetPtrElementsVisibility", "Pointeurs vers la visibilité des éléments du MAILx multi", 1),
        ("multiMAILx_GetScalarFieldRank", "Rang du champ scalaire du MAILx multi", 1),
        ("multiMAILx_GetVectorFieldRank", "Rang du champ vectoriel du MAILx multi", 1),
        # ---  Mesh 2D (Q4) ------------------------------------------------------ 
        ("mesh2D_GetIndicesMeshQ4", "Indices du maillage 2D (Q4)", 1),
        ("mp_solver_GetBrancheValues", "Valeurs des branches du solveur mp", 1),
    ]

    _SET_FUNCS = [
        # --- CDCDx (Contacteur-Contacteur) ----------------------------------------
        ("CDCDx_SetContactRadius", "Rayon de contact du CDCDx", 1),
        ("CDCDx_SetNumberInterByContact", "Nombre d'interactions par contact du CDCDx", 1),
        ("CDCDx_SetXPeriodicCondition", "Condition périodique en X du CDCDx", 1),
        ("CDCDx_SetYPeriodicCondition", "Condition périodique en Y du CDCDx", 1),
        # --- CLALp ---
        ("CLALp_SetNonSymmetricDetection", "Détection de non-symétrie pour CLALp", 1),
        # --- CLxxx ---
        ("CLxxx_SetNbNodesByCLxxx", "Nombre de noeuds par CLxxx", 1),
        # --- CSASp ---
        ("CSASp_SetNonSymmetricDetection", "Détection de non-symétrie pour CSASp", 1),
        ("CSASp_SetTrimAngle", "Angle d'ajustement pour CSASp", 1),
        # --- CSxxx ---
        ("CSxxx_SetQuadrature", "Quadrature pour CSxxx", 1),
        ("CSxxx_SetShrink", "Réduction pour CSxxx", 1),
        # --- DKDKx --------
        ("DISKx_SetVdilation", "Dilation en V pour DISKx", 1),
        ("DISKx_SetXdilation", "Dilation en X pour DISKx", 1),

        ("DKDKL_SetPeriodicCondition", "Condition périodique pour DKDKL", 1),
        ("DKDKx_SetFrictionModel", "Modèle de frottement pour DKDKx", 1),
        ("DKDKx_SetPeriodicCondition", "Condition périodique pour DKDKx", 1),
        ("DKDKx_SetSurfaceSectors", " Secteurs de surface pour DKDKx", 1),
        ("DKJCx_SetFrictionModel", "Modèle de frottement pour DKJCx", 1),
        ("DKJCx_SetSurfaceSectors", " Secteurs de surface pour DKJCx", 1),
        ("DKKDx_SetSurfaceSectors", " Secteurs de surface pour DKKDx", 1),
        ("DKPLx_SetPeriodicCondition", "Condition périodique pour DKPLx", 1),
        # --- DKKDx ---
        ("Integrator_SetContactDetectionConfiguration", "Configuration de détection de contact pour l'intégrateur", 1),
        # --- MAILx ---
        ("MAILx_SetCoorRef", "Référentiel de coordonnées pour MAILx", 1),
        ("MAILx_SetNodalField", "Champ nodal pour MAILx", 1),
        # --- NewtonRaphson ---
        ("NewtonRaphson_SetBadIter", "Nombre d'itérations bad pour NewtonRaphson", 1),
        ("NewtonRaphson_SetFinalTime", "Temps final pour NewtonRaphson", 1),
        ("NewtonRaphson_SetGoodIter", "Nombre d'itérations good pour NewtonRaphson", 1),
        ("NewtonRaphson_SetIncPatience", "Incertitude de patience pour NewtonRaphson", 1),
        ("NewtonRaphson_SetMaxIter", "Nombre maximum d'itérations pour NewtonRaphson", 1),
        ("NewtonRaphson_SetMaxTimeStep", "Pas de temps maximum pour NewtonRaphson", 1),
        ("NewtonRaphson_SetMinTimeStep", "Pas de temps minimum pour NewtonRaphson", 1),
        # ----PLJCx (parois planes) ----------------------------------------    
        ("PLJCx_SetFrictionModel", "Modèle de frottement pour PLJCx", 1),
        ("PLPLx_SetBigPolygTolerance", "Tolérance pour PLPLx", 1),
        ("PLPLx_SetFrictionModel", "Modèle de frottement pour PLPLx", 1),
        ("PLPLx_SetPeriodicCondition", "Condition périodique pour PLPLx", 1),
        # ----POLYG (polygones) ----------------------------------------    
        ("POLYG_SetVdilation", "Dilation en V pour POLYG", 1),
        ("POLYG_SetXdilation", "Dilation en X pour POLYG", 1),
        ("POLYR_SetBigPolyr", "Polygone grand pour POLYR", 1),
        ("POLYR_SetNbBigPolyr", "Nombre de polygones grands pour POLYR", 1),
        ("POLYR_SetThresholdBigPolyr", "Seuil pour polygones grands pour POLYR", 1),
        # ----PRPRx (particules) ----------------------------------------    
        ("PRPRx_SetCundallNeighbor", "Voisin Cundall pour PRPRx", 1),
        ("PRPRx_SetF2fMinimalSurfaceSize", "Taille minimale de surface pour PRPRx", 1),
        ("PRPRx_SetInteractionInternal", "Interaction interne pour PRPRx", 1),
        ("PRPRx_SetInternalSurface", "Surface interne pour PRPRx", 1),
        ("PRPRx_SetReactionTrackingLength", "Longueur de suivi de réaction pour PRPRx", 1),
        ("PRPRx_SetTolRecupRloc", "Tolérance de récupération de Rloc pour PRPRx", 1),
        ("PRPRx_SetXPeriodicCondition", "Condition périodique en X pour PRPRx", 1),
        ("PRPRx_SetYPeriodicCondition", "Condition périodique en Y pour PRPRx", 1),
        # ---
        ("PT2Dx_SetDisplayRadius", "Rayon d'affichage pour PT2Dx", 1),
        ("PT3Dx_SetDisplayRadius", "Rayon d'affichage pour PT3Dx", 1),
        ("PTPT2_SetExplicitLocalFrame", "Cadre local explicite pour PTPT2", 1),
        ("PTPT2_SetTolerance", "Tolérance pour PTPT2", 1),
        ("PTPT3_SetExplicitLocalFrame", "Cadre local explicite pour PTPT3", 1),
        ("PTPT3_SetXPeriodicCondition", "Condition périodique en X pour PTPT3", 1),
        ("PTPT3_SetYPeriodicCondition", "Condition périodique en Y pour PTPT3", 1),
        # ----- RBDY2 corps ---------------------------------------------------
        ("RBDY2_SetBodiesInvisible", "Bodies invisibles pour RBDY2", 1),
        ("RBDY2_SetContactorColor", "Couleur du contacteur pour RBDY2", 1),
        ("RBDY2_SetEquilibriumNorm", "Norme d'équilibre pour RBDY2", 1),
        ("RBDY2_SetInvisible", "Invisible pour RBDY2", 1),
        ("RBDY2_SetInvisibleVlocyDrivenDof", "Degrés de liberté invisibles pour RBDY2", 1),
        ("RBDY2_SetPeriodicCondition", "Condition périodique pour RBDY2", 1),
        ("RBDY2_SetSurfaceSectors", "Secteurs de surface pour RBDY2", 1),
        ("RBDY2_SetVisible", "Visible pour RBDY2", 1),
        ("RBDY2_SetVisibleVlocyDrivenDof", "Degrés de liberté visibles pour RBDY2", 1),
        ("RBDY2_SetVlocyDrivenDof", "Degrés de liberté Vlocy pour RBDY2", 1),
        ("RBDY2_SetXmaxBoundary", "Limite X max pour RBDY2", 1),
        ("RBDY2_SetXminBoundary", "Limite X min pour RBDY2", 1),
        ("RBDY2_SetYmaxBoundary", "Limite Y max pour RBDY2", 1),
        ("RBDY2_SetYminBoundary", "Limite Y min pour RBDY2", 1),
        # ----- RBDY3 corps ---------------------------------------------------
        ("RBDY3_SetBodiesInvisible", "Bodies invisibles pour RBDY3", 1),
        ("RBDY3_SetContactorColor", "Couleur du contacteur pour RBDY3", 1),
        ("RBDY3_SetEquilibriumNorm", "Norme d'équilibre pour RBDY3", 1),
        ("RBDY3_SetInvisible", "Invisible pour RBDY3", 1),
        ("RBDY3_SetInvisibleSmallObjects", "Objets petits invisibles pour RBDY3", 1),
        ("RBDY3_SetXmaxBoundary", "Limite X max pour RBDY3", 1),
        ("RBDY3_SetXminBoundary", "Limite X min pour RBDY3", 1),
        ("RBDY3_SetYPeriodicCondition", "Condition périodique en Y pour RBDY3", 1),
        ("RBDY3_SetYmaxBoundary", "Limite Y max pour RBDY3", 1),
        ("RBDY3_SetYminBoundary", "Limite Y min pour RBDY3", 1),
        ("RBDY3_SetZmaxBoundary", "Limite Z max pour RBDY3", 1),
        ("RBDY3_SetZminBoundary", "Limite Z min pour RBDY3", 1),
        # --- SPHER (spheres) ----------------------------------------
        ("SPHER_SetRadiusCorrection", "Correction du rayon pour SPHER", 1),
        ("SPPRx_SetXPeriodicCondition", "Condition périodique en X pour SPPRx", 1),
        ("SPPRx_SetYPeriodicCondition", "Condition périodique en Y pour SPPRx", 1),
        ("SPSPx_SetContactRadius", "Rayon de contact pour SPSPx", 1),
        ("SPSPx_SetNumberInterByContact", "Nombre d'interactions par contact pour SPSPx", 1),
        ("SPSPx_SetXPeriodicCondition", "Condition périodique en X pour SPSPx", 1),
        ("SPSPx_SetYPeriodicCondition", "Condition périodique en Y pour SPSPx", 1),
        # -----
        ("SetContactRadius", "Rayon de contact", 1),
        ("SetDimension", "Dimension", 1),
        ("SetDomainBoundary", "Limite de domaine", 1),
        ("SetNumberInteractionByContact", "Nombre d'interactions par contact", 1),
        ("SetPeriodicCondition", "Condition périodique", 1),
        # --- TimeEvolution (évolution temporelle) --------------------------------
        ("TimeEvolution_SetInitialStep", "Pas de temps initial pour l'évolution temporelle", 1),
        ("TimeEvolution_SetInitialTime", "Temps initial pour l'évolution temporelle", 1),
        ("TimeEvolution_SetTimeStep", "Pas de temps pour l'évolution temporelle", 1),
        # --- Comportements massifs -------------------------------------------------
        ("bulk_behav_SetBiot", "Paramètre de Biot pour bulk_behav", 1),
        ("bulk_behav_SetCapacity", "Capacité pour bulk_behav", 1),
        ("bulk_behav_SetConductivity", "Conductivité pour bulk_behav", 1),
        ("bulk_behav_SetDensity", "Densité pour bulk_behav", 1),
        ("bulk_behav_SetExternalFlux", "Flux externe pour bulk_behav", 1),
        ("bulk_behav_SetGravity", "Gravité pour bulk_behav", 1),

        ("cpg_3D_SetCheckType", "Type de vérification pour cpg_3D", 1),
        ("cpg_3D_SetDiagonalPrecond", "Préconditionnement diagonal pour cpg_3D", 1),
        ("cpg_3D_SetFrictionless", "Sans frottement pour cpg_3D", 1),
        ("cpg_SetCheckType", "Type de vérification pour cpg", 1),
        ("cpg_SetDiagonalPrecond", "Préconditionnement diagonal pour cpg", 1),
        ("cpg_SetFrictionless", "Sans frottement pour cpg", 1),
        ("cpg_SetNoConjugaison", "Pas de conjugaison pour cpg", 1),
        # ----
        ("mecaMAILx_SetCoroAllBodies", "Corps tous pour mecaMAILx", 1),
        ("mecaMAILx_SetCoroBody", "Corps pour mecaMAILx", 1),
        ("mecaMAILx_SetEquilibriumNorm", "Norme d'équilibre pour mecaMAILx", 1),
        ("mecaMAILx_SetInvisible", "Invisible pour mecaMAILx", 1),
        ("mecaMAILx_SetInvisibleVlocyDrivenDof", "Invisible VlocyDrivenDof pour mecaMAILx", 1),
        ("mecaMAILx_SetPreconAllBodies", "Préconditionnement tous pour mecaMAILx", 1),
        ("mecaMAILx_SetPreconBody", "Préconditionnement pour mecaMAILx", 1),
        ("mecaMAILx_SetRVDrivenDofValue", "Valeur Dof RVDriven pour mecaMAILx", 1),
        ("mecaMAILx_SetRVDrivenDofs", "Dofs RVDriven pour mecaMAILx", 1),
        ("mecaMAILx_SetRigidAllBodies", "Corps rigides tous pour mecaMAILx", 1),
        ("mecaMAILx_SetRigidBody", "Corps rigide pour mecaMAILx", 1),
        ("mecaMAILx_SetScalarFieldByElement", "Champ scalaire par élément pour mecaMAILx", 1),
        ("mecaMAILx_SetScalarFieldByNode", "Champ scalaire par nœud pour mecaMAILx", 1),
        ("mecaMAILx_SetTolCoro", "Tolérance pour mecaMAILx", 1),
        ("mecaMAILx_SetVectorFieldByElement", "Champ vectoriel par élément pour mecaMAILx", 1),
        ("mecaMAILx_SetVectorFieldByNode", "Champ vectoriel par nœud pour mecaMAILx", 1),
        ("mecaMAILx_SetVisible", "Visible pour mecaMAILx", 1),
        ("mecaMAILx_SetVisibleVlocyDrivenDof", "Visible VlocyDrivenDof pour mecaMAILx", 1),
        ("mecaMAILx_SetVlocyDrivenDof", "Dof VlocyDriven pour mecaMAILx", 1),
        ("mecaMAILx_UseNewPPSet", "Utiliser le nouveau ensemble PP pour mecaMAILx", 1),
        # ----
        ("multiMAILx_SetScalarFieldByElement", "Champ scalaire par élément pour multiMAILx", 1),
        ("multiMAILx_SetScalarFieldByNode", "Champ scalaire par nœud pour multiMAILx", 1),
        ("multiMAILx_SetVectorFieldByElement", "Champ vectoriel par élément pour multiMAILx", 1),
        ("multiMAILx_SetVectorFieldByNode", "Champ vectoriel par nœud pour multiMAILx", 1),
        # ----
        ("nlgs_3D_SetCheckType", "Type de vérification pour nlgs_3D", 1),
        ("nlgs_3D_SetWithQuickScramble", "Avec mélange rapide pour nlgs_3D", 1),
        ("nlgs_3D_SetWithReverseContactOrder", "Avec ordre inverse des contacts pour nlgs_3D", 1),
        ("nlgs_SetCheckType", "Type de vérification pour nlgs", 1),
        ("nlgs_SetTemporaryVariable", "Variable temporaire pour nlgs", 1),
        ("nlgs_SetWithQuickScramble", "Avec mélange rapide pour nlgs", 1),

        ("overall_SetWorkingDirectory", "Répertoire de travail pour overall", 1),
        ("overall_SetWorkingFileName", "Nom de fichier de travail pour overall", 1),

        ("poroMAILx_SetCoroAllBodies", "Corps tous pour poroMAILx", 1),
        ("poroMAILx_SetCoroBody", "Corps pour poroMAILx", 1),
        ("poroMAILx_SetEquilibriumNorm", "Norme d'équilibre pour poroMAILx", 1),
        ("poroMAILx_SetInvisible", "Invisible pour poroMAILx", 1),
        ("poroMAILx_SetInvisibleVlocyDrivenDof", "Invisible VlocyDrivenDof pour poroMAILx", 1),
        ("poroMAILx_SetPreconAllBodies", "Préconditionnement tous pour poroMAILx", 1),
        ("poroMAILx_SetPreconBody", "Préconditionnement pour poroMAILx", 1),
        ("poroMAILx_SetRVDrivenDofValue", "Valeur Dof RVDriven pour poroMAILx", 1),
        ("poroMAILx_SetRVDrivenDofs", "Dofs RVDriven pour poroMAILx", 1),
        ("poroMAILx_SetRigidAllBodies", "Corps rigides tous pour poroMAILx", 1),
        ("poroMAILx_SetRigidBody", "Corps rigide pour poroMAILx", 1),
        ("poroMAILx_SetScalarFieldByElement", "Champ scalaire par élément pour poroMAILx", 1),
        ("poroMAILx_SetScalarFieldByNode", "Champ scalaire par nœud pour poroMAILx", 1),
        ("poroMAILx_SetTolCoro", "Tolérance pour poroMAILx", 1),
        ("poroMAILx_SetVectorFieldByElement", "Champ vectoriel par élément pour poroMAILx", 1),
        ("poroMAILx_SetVectorFieldByNode", "Champ vectoriel par nœud pour poroMAILx", 1),
        ("poroMAILx_SetVisible", "Visible pour poroMAILx", 1),
        ("poroMAILx_SetVisibleVlocyDrivenDof", "Visible VlocyDrivenDof pour poroMAILx", 1),
        ("poroMAILx_SetMecaScalarFieldByElement", "Champ mécanique scalaire par élément pour poroMAILx", 1),
        ("poroMAILx_SetMecaScalarFieldByNode", "Champ mécanique scalaire par nœud pour poroMAILx", 1),
        ("poroMAILx_SetMecaVectorFieldByElement", "Champ mécanique vectoriel par élément pour poroMAILx", 1),
        ("poroMAILx_SetMecaVectorFieldByNode", "Champ mécanique vectoriel par nœud pour poroMAILx", 1),
        ("poroMAILx_SetPreconAllBodies", "Préconditionnement tous pour poroMAILx", 1),
        ("poroMAILx_SetPreconBody", "Préconditionnement pour poroMAILx", 1),
        ("poroMAILx_SetRVDrivenDofValue", "Valeur Dof RVDriven pour poroMAILx", 1),
        ("poroMAILx_SetRVDrivenDofs", "Dofs RVDriven pour poroMAILx", 1),
        ("poroMAILx_SetRigidAllBodies", "Corps rigides tous pour poroMAILx", 1),
        ("poroMAILx_SetRigidBody", "Corps rigide pour poroMAILx", 1),
        ("poroMAILx_SetScalarFieldByElement", "Champ scalaire par élément pour poroMAILx", 1),
        ("poroMAILx_SetScalarFieldByNode", "Champ scalaire par nœud pour poroMAILx", 1),
        ("poroMAILx_SetTolCoro", "Tolérance pour poroMAILx", 1),
        ("poroMAILx_SetVectorFieldByElement", "Champ vectoriel par élément pour poroMAILx", 1),
        ("poroMAILx_SetVectorFieldByNode", "Champ vectoriel par nœud pour poroMAILx", 1),
        ("poroMAILx_SetVisible", "Visible pour poroMAILx", 1),
        ("poroMAILx_SetVisibleVlocyDrivenDof", "Visible VlocyDrivenDof pour poroMAILx", 1),
        ("poroMAILx_SetMecaScalarFieldByElement", "Champ mécanique scalaire par élément pour poroMAILx", 1),
        ("poroMAILx_SetMecaScalarFieldByNode", "Champ mécanique scalaire par nœud pour poroMAILx", 1),
        ("poroMAILx_SetMecaVectorFieldByElement", "Champ mécanique vectoriel par élément pour poroMAILx", 1),
        ("poroMAILx_SetMecaVectorFieldByNode", "Champ mécanique vectoriel par nœud pour poroMAILx", 1),
        ("poroMAILx_SetPreconAllBodies", "Préconditionnement tous pour poroMAILx", 1),
        ("poroMAILx_SetPreconBody", "Préconditionnement pour poroMAILx", 1),
        ("poroMAILx_SetRVDrivenDofValue", "Valeur Dof RVDriven pour poroMAILx", 1),
        ("poroMAILx_SetRVDrivenDofs", "Dofs RVDriven pour poroMAILx", 1),
        ("poroMAILx_SetRigidAllBodies", "Corps rigides tous pour poroMAILx", 1),
        ("poroMAILx_SetRigidBody", "Corps rigide pour poroMAILx", 1),
        ("poroMAILx_SetTherScalarFieldByElement", "Champ thermique scalaire par élément pour poroMAILx", 1),    
        ("poroMAILx_SetTherScalarFieldByElement", "Champ thermique scalaire par élément pour poroMAILx", 1),
        ("poroMAILx_SetTherScalarFieldByNode", "Champ thermique scalaire par nœud pour poroMAILx", 1),
        ("poroMAILx_SetTherVectorFieldByElement", "Champ thermique vectoriel par élément pour poroMAILx", 1),
        ("poroMAILx_SetTherVectorFieldByNode", "Champ thermique vectoriel par nœud pour poroMAILx", 1),
        ("poroMAILx_SetVlocyDrivenDof", "Dof VlocyDriven pour poroMAILx", 1),

        ("postpro_SetCircularSelectionZone", "Zone de sélection circulaire pour postpro", 1),
        ("postpro_SetRectangularSelectionZone", "Zone de sélection rectangulaire pour postpro", 1),
        ("postpro_SetSelectionZone", "Zone de sélection pour postpro", 1),

        ("tact_behav_SetCohesionParameters", "Paramètres de cohésion pour tact_behav", 1),
        ("tact_behav_SetDampingParameters", "Paramètres d'amortissement pour tact_behav", 1),
        ("tact_behav_SetElasticityParameters", "Paramètres d'élasticité pour tact_behav", 1),
        ("tact_behav_SetFrictionParameters", "Paramètres de frottement pour tact_behav", 1),
        ("tact_behav_SetLawInternalComment", "Commentaires internes sur la loi pour tact_behav", 1),
        ("tact_behav_SetLawName", "Nom de la loi pour tact_behav", 1),
        ("tact_behav_SetLawParameters", "Paramètres de la loi pour tact_behav", 1),
        ("tact_behav_SetLawType", "Type de loi pour tact_behav", 1),
        ("tact_behav_SetLawVersion", "Version de la loi pour tact_behav", 1),
        ("tact_behav_SetNbLawParameters", "Nombre de paramètres de la loi pour tact_behav", 1),
        ("tact_behav_SetNbTactBehav", "Nombre de comportements de contact pour tact_behav", 1),
        ("tact_behav_SetNormalDampingParameters", "Paramètres d'amortissement normal pour tact_behav", 1),
        ("tact_behav_SetNormalElasticityParameters", "Paramètres d'élasticité normale pour tact_behav", 1),
        ("tact_behav_SetNormalFrictionParameters", "Paramètres de frottement normal pour tact_behav", 1),
        ("tact_behav_SetNormalLawParameters", "Paramètres de la loi normale pour tact_behav", 1),
        ("tact_behav_SetNormalLawType", "Type de loi normale pour tact_behav", 1),
        ("tact_behav_SetNormalLawVersion", "Version de la loi normale pour tact_behav", 1),
        ("tact_behav_SetNormalNbLawParameters", "Nombre de paramètres de la loi normale pour tact_behav", 1),
        ("tact_behav_SetNormalStiffnessParameters", "Paramètres de raideur normale pour tact_behav", 1),
        ("tact_behav_SetParam", "Paramètre pour tact_behav", 1),
        ("tact_behav_SetPressureParameters", "Paramètres de pression pour tact_behav", 1),
        ("tact_behav_SetRNcap", "Capacité RN pour tact_behav", 1),
        ("tact_behav_SetTangentialDampingParameters", "Paramètres d'amortissement tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialElasticityParameters", "Paramètres d'élasticité tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialFrictionParameters", "Paramètres de frottement tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialLawParameters", "Paramètres de la loi tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialLawType", "Type de loi tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialLawVersion", "Version de la loi tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialNbLawParameters", "Nombre de paramètres de la loi tangentiels pour tact_behav", 1),
        ("tact_behav_SetTangentialStiffnessParameters", "Paramètres de raideur tangentiels pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFriction", "CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFrictionParameters", "Paramètres de CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFrictionLawParameters", "Paramètres de la loi CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFrictionLawType", "Type de loi CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFrictionLawVersion", "Version de la loi CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFrictionNbLawParameters", "Nombre de paramètres de la loi CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetCZMwithInitialFrictionStiffnessParameters", "Paramètres de raideur CZM avec frottement initial pour tact_behav", 1),
        ("tact_behav_SetDilatancyParameters", "Paramètres de dilatance pour tact_behav", 1),
        ("tact_behav_SetParam", "Paramètre pour tact_behav", 1),
        ("tact_behav_SetPressureParameters", "Paramètres de pression pour tact_behav", 1),
        ("tact_behav_SetRNcap", "Capacité RN pour tact_behav", 1),
        
        ("therMAILx_SetScalarFieldByElement", "Champ scalaire par élément pour therMAILx", 1),
        ("therMAILx_SetScalarFieldByNode", "Champ scalaire par nœud pour therMAILx", 1),
        ("therMAILx_SetVectorFieldByElement", "Champ vectoriel par élément pour therMAILx", 1),
        ("therMAILx_SetVectorFieldByNode", "Champ vectoriel par nœud pour therMAILx", 1),
        
        ("xKSID_SetVdilation", "Dilatation V pour xKSID", 1),
        ("xKSID_SetXdilation", "Dilatation X pour xKSID", 1),

    ]

    def _make_insp_tab(
        self,
        dim_label: str,
        funcs_catalog: list,
        rows_list_attr: str,
        rows_layout_attr: str,
        add_cb_label: str,
    ) -> "QWidget":
        """
        Construit un onglet d'inspection generique.
        Parametres :
            dim_label        : "2D", "3D" "SET" ou "INT",
            funcs_catalog    : liste de tuples (nom_func, description, nb_params)
            rows_list_attr   : nom de l'attribut self._insp??_rows
            rows_layout_attr : nom de l'attribut self._insp??_rows_layout
            add_cb_label     : texte du bouton "Ajouter"
        """
        w = QWidget()
        vb = QVBoxLayout(w)
        vb.setSpacing(6)

        # ── Explication ──────────────────────────────────────────────────────
        note_text = {
            "2D":  ("Fonctions chipy pour inspecter les contacteurs 2D : "
                    "DISKx, JONCx, POLYR, xKSID, PT2Dx, RBDY2. "
                    "Les fonctions sans ID (GetNb...) s'appellent sans argument."),
            "3D":  ("Fonctions chipy pour inspecter les contacteurs 3D : "
                    "SPHER, POLYH, CYLND, PLANE, PT3Dx, RBDY3. "
                    "Les fonctions sans ID (GetNb...) s'appellent sans argument."),
            "SET": ("Fonctions chipy de modification (Set). Les IDs ou le groupe "
                    "permettent d'appliquer l'action à chaque avatar ciblé. "
                    "Avec un groupe, utilisez _id dans les arguments pour passer "
                    "l'ID avec d'autres valeurs. "
                    "La variable Python stocke le résultat de l'appel."),
            "INT": ("Fonctions chipy pour inspecter les interactions (paires de contacteurs) : "
                    "DKDKx, DKJCx, DKKDx, PLPLx, CLALp, ALpALp, "
                    "SPSPx, SPCDx, SPPLx, CDCDx, CDPLx, PRPRx, "
                    "DKMECAx, ALpMECAx, SPMECAx. "
                    "ID = index de la paire dans la liste chipy (1-based)."),
        }.get(dim_label, "")
        note_lbl = QLabel(note_text)
        note_lbl.setWordWrap(True)
        note_lbl.setStyleSheet(
            "background:#e8f5e9; padding:6px; border-radius:4px; font-size:8pt;"
        )
        vb.addWidget(note_lbl)

        # ── En-tete colonnes ─────────────────────────────────────────────────
        hdr = QHBoxLayout()
        columns = ([
                ("Fonction chipy", 230),
                ("IDs (paires/contacteurs)", 145),
                ("Groupe", 110),
                ("Mode / Timing", 200),
                ("Var. Python", 110),
            ]
        )
        for lbl_txt, lbl_w in columns:
            lbl = QLabel("<b>{}</b>".format(lbl_txt))
            lbl.setFixedWidth(lbl_w)
            hdr.addWidget(lbl)
        hdr.addStretch()
        vb.addLayout(hdr)

        # ── Zone de lignes scrollable ─────────────────────────────────────────
        rows_widget = QWidget()
        rows_layout = QVBoxLayout(rows_widget)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(2)

        setattr(self, rows_list_attr,   [])
        setattr(self, rows_layout_attr, rows_layout)

        vb.addWidget(rows_widget)

        # ── Bouton Ajouter ────────────────────────────────────────────────────
        btn_add = QPushButton(add_cb_label)
        btn_add.clicked.connect(
            lambda checked=False, d=dim_label: self._add_insp_row(d)
        )
        vb.addWidget(btn_add)
        vb.addStretch()
        return _scroll(w)

    def _tab_insp_2d(self) -> "QWidget":
        """Onglet inspection contacteurs 2D."""
        return self._make_insp_tab(
            dim_label        = "2D",
            funcs_catalog    = self._INSP2D_FUNCS,
            rows_list_attr   = "_insp2d_rows",
            rows_layout_attr = "_insp2d_rows_layout",
            add_cb_label     = "+ Ajouter une inspection 2D",
        )

    def _tab_insp_3d(self) -> "QWidget":
        """Onglet inspection contacteurs 3D."""
        return self._make_insp_tab(
            dim_label        = "3D",
            funcs_catalog    = self._INSP3D_FUNCS,
            rows_list_attr   = "_insp3d_rows",
            rows_layout_attr = "_insp3d_rows_layout",
            add_cb_label     = "+ Ajouter une inspection 3D",
        )

    def _tab_insp_int(self) -> "QWidget":
        """Onglet inspection interactions (paires)."""
        return self._make_insp_tab(
            dim_label        = "INT",
            funcs_catalog    = self._INSPI_FUNCS,
            rows_list_attr   = "_inspi_rows",
            rows_layout_attr = "_inspi_rows_layout",
            add_cb_label     = "+ Ajouter une inspection interaction",
        )

    def _tab_set_actions(self) -> QWidget:
        """Onglet SET construit avec le même générateur de lignes d'inspection."""
        return self._make_insp_tab(
            dim_label="SET",
            funcs_catalog=self._SET_FUNCS,
            rows_list_attr="_set_rows",
            rows_layout_attr="_set_rows_layout",
            add_cb_label="+ Ajouter une action SET",
        )

    @staticmethod
    def _validate_set_action(entry: dict, index: int) -> Optional[str]:
        func = entry.get("func", "")
        args = entry.get("args", "")
        if (
            not func
            or not func.isidentifier()
            or keyword.iskeyword(func)
            or "Set" not in func
        ):
            return (
                "Action SET {} : indiquez un nom de fonction chipy valide "
                "contenant « Set ».".format(index)
            )
        try:
            ast.parse("chipy.{}({})".format(func, args), mode="eval")
        except SyntaxError as exc:
            return "Action SET {} : arguments Python invalides ({})".format(
                index, exc.msg
            )
        return None

    def _get_catalog_for_dim(self, dim: str) -> list:
        return {
            "2D":  self._INSP2D_FUNCS,
            "3D":  self._INSP3D_FUNCS,
            "INT": self._INSPI_FUNCS,
            "SET": self._SET_FUNCS,
        }.get(dim, self._INSP2D_FUNCS)

    def _add_insp_row(self, dim: str, entry: dict = None):
        """
        Ajoute une ligne d'inspection dans l'onglet dim.
        entry : dict optionnel {"func": str, "ids": str, "group": str,
                                "in_loop": bool, "freq": int, "store": str}
        """
        entry = entry or {}
        catalog = self._get_catalog_for_dim(dim)
        func_names = [f[0] for f in catalog]

        _row_attrs = {
            "2D": ("_insp2d_rows", "_insp2d_rows_layout"),
            "3D": ("_insp3d_rows", "_insp3d_rows_layout"),
            "INT": ("_inspi_rows", "_inspi_rows_layout"),
            "SET": ("_set_rows", "_set_rows_layout"),
        }
        rows_list_attr, rows_layout_attr = _row_attrs.get(
            dim, _row_attrs["2D"]
        )
        rows_list = getattr(self, rows_list_attr)
        rows_layout = getattr(self, rows_layout_attr)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        # ── ComboBox fonction ─────────────────────────────────────────────────
        combo_func = QComboBox()
        combo_func.setFixedWidth(230)
        for fname, fdesc, _ in catalog:
            combo_func.addItem(fname)
            combo_func.setItemData(
                combo_func.count() - 1, fdesc, 3  # Qt.ToolTipRole = 3
            )
        if entry.get("func") in func_names:
            combo_func.setCurrentText(entry["func"])

        def _update_tip(idx, cb=combo_func, cat=catalog):
            if 0 <= idx < len(cat):
                cb.setToolTip("{} -- {}".format(cat[idx][0], cat[idx][1]))
        combo_func.currentIndexChanged.connect(_update_tip)
        _update_tip(combo_func.currentIndex())
        row_layout.addWidget(combo_func)

        # ── IDs ───────────────────────────────────────────────────────────────
        edit_ids = QLineEdit()
        edit_ids.setFixedWidth(100)
        edit_ids.setPlaceholderText("args, _id" if dim == "SET" else "1, 3, 5")
        edit_ids.setText(
            entry.get("args", entry.get("ids", ""))
            if dim == "SET" else entry.get("ids", "")
        )
        edit_ids.setToolTip(
            "Arguments Python séparés par des virgules."
            if dim == "SET" else
            "IDs (1-based) des contacteurs ou paires a inspecter. "
            "Laisser vide si la fonction ne prend pas d'ID (GetNb...)."
        )

        btn_pick = QPushButton("...")
        btn_pick.setFixedWidth(36)
        btn_pick.setToolTip("Choisir depuis la liste du projet.")
        pick_dim = "2D" if dim in ("2D", "INT", "SET") else "3D"
        def _make_pick(e=edit_ids, d=pick_dim):
            return lambda: self._pick_avatar_ids(e, d)
        btn_pick.clicked.connect(_make_pick())
        row_layout.addWidget(edit_ids)
        row_layout.addWidget(btn_pick)

        # ── Groupe ────────────────────────────────────────────────────────────
        combo_grp = QComboBox()
        combo_grp.setFixedWidth(110)
        combo_grp.setEditable(True)
        combo_grp.addItem("")
        groups = list(
            (getattr(getattr(self, "controller", None), "state", None)
             and getattr(self.controller.project, "avatar_groups", {}) or {}).keys()
        )
        combo_grp.addItems(groups)
        if entry.get("group"):
            idx_g = combo_grp.findText(entry["group"])
            if idx_g >= 0:
                combo_grp.setCurrentIndex(idx_g)
            else:
                combo_grp.setCurrentText(entry["group"])
        combo_grp.setToolTip(
            "Groupe d'avatars. Si vide, les IDs ci-contre sont utilises. "
            "Les IDs du groupe sont resolus au moment de la generation du script."
        )
        row_layout.addWidget(combo_grp)

        # ── Mode d'execution (timing) ──────────────────────────────────────
        _tc_i, _combo_mode_i, _spin_val_i = self._make_timing_widget(entry, default_mode="all")
        row_layout.addWidget(_tc_i)

        # ── Variable de stockage ─────────────────────────────────────────────
        edit_store = QLineEdit()
        edit_store.setFixedWidth(110)
        edit_store.setPlaceholderText("ex: res_Rn")
        edit_store.setText(entry.get("store", ""))
        edit_store.setToolTip(
            "Nom de variable Python pour stocker le resultat. "
            "Ex: res_Rn  =>  res_Rn = chipy.DKDKx_GetRlocTT(i). "
            "Laisser vide si le resultat n'est pas utilise."
        )
        row_layout.addWidget(edit_store)

        # ── Bouton supprimer ─────────────────────────────────────────────────
        btn_del = QPushButton("x")
        btn_del.setFixedWidth(36)
        row_data = {
            "widget":     row_widget,
            "combo_func": combo_func,
            "edit_ids":   edit_ids,
            "combo_grp":  combo_grp,
            "combo_mode": _combo_mode_i,
            "spin_val":   _spin_val_i,
            "edit_store": edit_store,
            "dim":        dim,
        }
        def _make_del(rd=row_data, rl=rows_list, rlay=rows_layout):
            def _do():
                rl.remove(rd)
                rlay.removeWidget(rd["widget"])
                rd["widget"].deleteLater()
            return _do
        btn_del.clicked.connect(_make_del())
        row_layout.addWidget(btn_del)
        row_layout.addStretch()

        rows_layout.addWidget(row_widget)
        rows_list.append(row_data)

    def _read_insp_row(self, row: dict) -> dict:
        """Lit une ligne d'inspection et retourne un dict serialisable."""
        _mode = row["combo_mode"].currentData()
        values = {
            "func":      row["combo_func"].currentText(),
            "step_mode": _mode,
            "step_val":  row["spin_val"].value(),
            # compat ascendante
            "in_loop":   _mode not in ("before", "after"),
            "freq":      row["spin_val"].value() if _mode == "every_n" else 1,
        }

        values["ids"] = row["edit_ids"].text().strip()
        values["group"] = row["combo_grp"].currentText().strip()
        values["store"] = row["edit_store"].text().strip()
        if row["dim"] == "SET":
            values["args"] = values["ids"]

        return values

    # =========================================================================
    # Chargement initial des widgets depuis _params
    # =========================================================================

    def _load(self):
        p = self._params

        # Modele
        {1: self._rb_cp, 2: self._rb_dp}.get(p["mhyp"], self._rb_3d).setChecked(True)
        self._cb_deformable.setChecked(p["deformable"])
        self._combo_phys.setCurrentIndex(
            {"MECAx": 0, "THERx": 1, "POROx": 2, "THMx": 3}.get(p["physics"], 0)
        )
        self._dspin_rloc.setValue(p["Rloc_tol"])

        # Routines (mapping attr -> cle)
        for attr, key in {
            "_cb_RBDY2":    "use_RBDY2",    "_cb_RBDY3":    "use_RBDY3",
            "_cb_DKDKx":    "use_DKDKx",    "_cb_DKJCx":    "use_DKJCx",
            "_cb_DKKDx":    "use_DKKDx",    "_cb_PLPLx":    "use_PLPLx",
            "_cb_CLALp":    "use_CLALp",    "_cb_ALpALp":   "use_ALpALp",
            "_cb_SPSPx":    "use_SPSPx",    "_cb_SPCDx":    "use_SPCDx",
            "_cb_SPPLx":    "use_SPPLx",    "_cb_CDCDx":    "use_CDCDx",
            "_cb_CDPLx":    "use_CDPLx",    "_cb_PRPRx":    "use_PRPRx",
            "_cb_mecaMAILx":  "use_mecaMAILx",  "_cb_therMAILx":  "use_therMAILx",
            "_cb_poroMAILx":  "use_poroMAILx",
            "_cb_DKMECAx":  "use_DKMECAx",  "_cb_ALpMECAx": "use_ALpMECAx",
            "_cb_SPMECAx":  "use_SPMECAx",
            "_cb_PT2Dx":    "use_PT2Dx",    "_cb_PT3Dx":    "use_PT3Dx",
            "_cb_NODES":    "use_NODES",    "_cb_bulk":     "use_bulk_behav",
        }.items():
            getattr(self, attr).setChecked(p.get(key, False))

        for key, checkbox in self._advanced_checks.items():
            checkbox.setChecked(p.get(key, False))
        for key, edit in self._advanced_edits.items():
            edit.setText(p.get(key, edit.text()))
        self._refresh_advanced_routine_controls()

        # Extraction — cases simples
        for attr, key in {
            "_cb_disable_log":  "disable_log",
            "_cb_vRBDY2":       "visu_RBDY2",     "_cb_vRBDY3":    "visu_RBDY3",
            "_cb_vMeca":        "visu_mecaMAILx",   "_cb_vTher":     "visu_therMAILx",
            "_cb_vHydr":        "visu_poroMAILx",   "_cb_disp_loop": "display_in_loop",
            # visibilite : gestion separee via QLineEdit
            "_cb_Rnod":         "extract_Rnod",   "_cb_Vloc":      "extract_Vloc",
            "_cb_Rloc":         "extract_Rloc",   "_cb_energy":    "extract_energy",
            "_cb_KE":           "extract_KE",     "_cb_fields":    "extract_fields",
            "_cb_internal":     "extract_internal",
        }.items():
            getattr(self, attr).setChecked(p.get(key, False))

        # Visibilite — lignes dynamiques
        self._vis_rows.clear()
        while self._vis_rows_layout.count():
            _wv = self._vis_rows_layout.takeAt(0).widget()
            if _wv: _wv.deleteLater()
        for _ve in p.get("vis_entries", []):
            self._add_vis_row(_ve)

        # Inspection 2D / 3D / Interactions — charger les entrees
        self._insp2d_rows.clear()
        while self._insp2d_rows_layout.count():
            w2 = self._insp2d_rows_layout.takeAt(0).widget()
            if w2: w2.deleteLater()
        for entry in p.get("insp2d_entries", []):
            self._add_insp_row("2D", entry)

        self._insp3d_rows.clear()
        while self._insp3d_rows_layout.count():
            w3 = self._insp3d_rows_layout.takeAt(0).widget()
            if w3: w3.deleteLater()
        for entry in p.get("insp3d_entries", []):
            self._add_insp_row("3D", entry)
        
        self._inspi_rows.clear()
        while self._inspi_rows_layout.count():
            wi = self._inspi_rows_layout.takeAt(0).widget()
            if wi: wi.deleteLater()
        for entry in p.get("inspi_entries", []):
            self._add_insp_row("INT", entry)

        # Actions SET configurables
        self._set_rows.clear()
        while self._set_rows_layout.count():
            sw = self._set_rows_layout.takeAt(0).widget()
            if sw:
                sw.deleteLater()
        for entry in p.get("set_entries", []):
            self._add_insp_row("SET", entry)

        # GetBodyVector RBDY2/3 — charger les entrees depuis _params
        self._gbv2_rows.clear()
        while self._gbv2_rows_layout.count():
            w = self._gbv2_rows_layout.takeAt(0).widget()
            if w: w.deleteLater()
        for entry in p.get("gbv2_entries", []):
            self._add_gbv_row("2D", entry)
        self._gbv3_rows.clear()
        while self._gbv3_rows_layout.count():
            w = self._gbv3_rows_layout.takeAt(0).widget()
            if w: w.deleteLater()
        for entry in p.get("gbv3_entries", []):
            self._add_gbv_row("3D", entry)

        # Pilotage
        self._cb_restart.setChecked(p["use_restart"])
        self._spin_rs_step.setValue(p["restart_step"])
        self._spin_rs_step.setEnabled(p["use_restart"])
        self._cb_stop.setChecked(p["use_stop_crit"])
        self._combo_stop_type.setCurrentIndex(
            {"energy": 0, "disp_max": 1, "force_res": 2}.get(p["stop_crit_type"], 0)
        )
        self._combo_stop_type.setEnabled(p["use_stop_crit"])
        self._dspin_stop_val.setValue(p["stop_crit_val"])
        self._dspin_stop_val.setEnabled(p["use_stop_crit"])
        self._spin_stop_freq.setValue(p["stop_crit_freq"])
        self._spin_stop_freq.setEnabled(p["use_stop_crit"])
        self._cb_multi.setChecked(p["use_multi_step"])
        self._spin_mp_nb.setValue(p["multi_step_nb"])
        self._spin_mp_nb.setEnabled(p["use_multi_step"])
        self._edit_mp_sizes.setText(p["multi_step_sizes"])
        self._edit_mp_sizes.setEnabled(p["use_multi_step"])

        self._refresh_info()

    # =========================================================================
    # Connexions des signaux
    # =========================================================================

    def _wire(self):
        self._cb_restart.toggled.connect(self._spin_rs_step.setEnabled)
        self._cb_stop.toggled.connect(self._on_stop_toggled)
        self._cb_multi.toggled.connect(self._on_multi_toggled)
        self._rb_3d.toggled.connect(self._on_3d_toggled)
        self._cb_deformable.toggled.connect(self._on_deformable_toggled)
        self._combo_phys.currentIndexChanged.connect(self._on_phys_changed)
        for checkbox in (
            self._cb_mecaMAILx, self._cb_therMAILx, self._cb_poroMAILx
        ):
            checkbox.toggled.connect(
                lambda _checked: self._refresh_advanced_routine_controls()
            )

    def _on_stop_toggled(self, v: bool):
        self._combo_stop_type.setEnabled(v)
        self._dspin_stop_val.setEnabled(v)
        self._spin_stop_freq.setEnabled(v)

    def _on_multi_toggled(self, v: bool):
        self._spin_mp_nb.setEnabled(v)
        self._edit_mp_sizes.setEnabled(v)

    def _on_3d_toggled(self, is3d: bool):
        self._rb_cp.setEnabled(not is3d)
        self._rb_dp.setEnabled(not is3d)
        for c in (self._cb_DKDKx, self._cb_DKJCx, self._cb_DKKDx,
                  self._cb_PLPLx, self._cb_CLALp, self._cb_ALpALp):
            c.setEnabled(not is3d)
        for c in (self._cb_SPSPx, self._cb_SPCDx, self._cb_SPPLx,
                  self._cb_CDCDx, self._cb_CDPLx, self._cb_PRPRx):
            c.setEnabled(is3d)

    def _on_deformable_toggled(self, v: bool):
        if v:
            self._on_phys_changed(self._combo_phys.currentIndex())
        self._refresh_advanced_routine_controls()

    def _on_phys_changed(self, idx: int):
        if not self._cb_deformable.isChecked():
            return
        self._cb_mecaMAILx.setChecked(idx == 0)
        self._cb_therMAILx.setChecked(idx == 1)
        self._cb_poroMAILx.setChecked(idx in (2, 3))
        self._cb_vMeca.setChecked(idx == 0)
        self._cb_vTher.setChecked(idx == 1)
        self._cb_vHydr.setChecked(idx in (2, 3))
        self._refresh_advanced_routine_controls()

    # =========================================================================
    # Auto-detection depuis le projet courant
    # =========================================================================

    # =========================================================================
    # Gestion des lignes GetBodyVector (ajout / lecture)
    # =========================================================================

    _GBV_VECS = [
        "Coor0", "Coor_", "Coorb", "Coorm",
        "X____", "V____", "Vbeg_", "Vfree",
        "Fext",  "Fint_", "Reac",  "Ireac",
    ]

    def _add_vis_row(self, entry: dict = None):
        """
        Ajoute une ligne de visibilite dans la section Visibilite.
        entry : dict {"action": str, "dim": str, "ids": str, "group": str,
                      "step_mode": str, "step_val": int}
        """
        entry = entry or {}

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        # ── Action : SetVisible / SetInvisible ────────────────────────────
        combo_action = QComboBox()
        combo_action.setFixedWidth(110)
        combo_action.addItem("SetVisible",   "visible")
        combo_action.addItem("SetInvisible", "invisible")
        combo_action.setToolTip(
            "SetVisible   : chipy.RBDY2_SetVisible(id)\n"
            "SetInvisible : chipy.RBDY2_SetInvisible(id)"
        )
        if entry.get("action") == "invisible":
            combo_action.setCurrentIndex(1)
        row_layout.addWidget(combo_action)

        # ── Dimension 2D / 3D ─────────────────────────────────────────────
        combo_dim = QComboBox()
        combo_dim.setFixedWidth(55)
        combo_dim.addItem("2D", "2D")
        combo_dim.addItem("3D", "3D")
        combo_dim.setToolTip("RBDY2 (2D) ou RBDY3 (3D)")
        if entry.get("dim") == "3D":
            combo_dim.setCurrentIndex(1)
        row_layout.addWidget(combo_dim)

        # ── IDs ───────────────────────────────────────────────────────────
        edit_ids = QLineEdit()
        edit_ids.setFixedWidth(100)
        edit_ids.setPlaceholderText("1, 3, 5")
        edit_ids.setText(entry.get("ids", ""))
        edit_ids.setToolTip(
            "IDs des avatars (1-based). "
            "Prioritaire sur le groupe si les deux sont remplis."
        )
        btn_pick = QPushButton("...")
        btn_pick.setFixedWidth(28)
        btn_pick.setToolTip("Choisir depuis la liste des avatars du projet.")
        def _make_pick(e=edit_ids, cb=combo_dim):
            return lambda: self._pick_avatar_ids(e, cb.currentData())
        btn_pick.clicked.connect(_make_pick())
        row_layout.addWidget(edit_ids)
        row_layout.addWidget(btn_pick)

        # ── Groupe ────────────────────────────────────────────────────────
        combo_grp = QComboBox()
        combo_grp.setFixedWidth(110)
        combo_grp.setEditable(True)
        combo_grp.addItem("")
        _groups = list(
            (getattr(getattr(self, "controller", None), "state", None)
             and getattr(self.controller.project, "avatar_groups", {}) or {}).keys()
        )
        combo_grp.addItems(_groups)
        if entry.get("group"):
            idx_g = combo_grp.findText(entry["group"])
            if idx_g >= 0:
                combo_grp.setCurrentIndex(idx_g)
            else:
                combo_grp.setCurrentText(entry["group"])
        combo_grp.setToolTip(
            "Groupe d'avatars. Si vide, les IDs ci-contre sont utilises. "
            "Si les deux sont remplis, les IDs ont la priorite."
        )
        row_layout.addWidget(combo_grp)

        # ── Mode / Timing (défaut : avant la boucle pour la visibilité) ──
        _tc, _combo_mode, _spin_val = self._make_timing_widget(entry, default_mode="before")
        row_layout.addWidget(_tc)

        # ── Bouton supprimer ──────────────────────────────────────────────
        btn_del = QPushButton("x")
        btn_del.setFixedWidth(24)
        btn_del.setToolTip("Supprimer cette ligne.")
        row_data = {
            "widget":       row_widget,
            "combo_action": combo_action,
            "combo_dim":    combo_dim,
            "edit_ids":     edit_ids,
            "combo_grp":    combo_grp,
            "combo_mode":   _combo_mode,
            "spin_val":     _spin_val,
        }
        def _make_del(rd=row_data):
            def _do():
                self._vis_rows.remove(rd)
                self._vis_rows_layout.removeWidget(rd["widget"])
                rd["widget"].deleteLater()
            return _do
        btn_del.clicked.connect(_make_del())
        row_layout.addWidget(btn_del)
        row_layout.addStretch()

        self._vis_rows_layout.addWidget(row_widget)
        self._vis_rows.append(row_data)

    def _read_vis_row(self, row: dict) -> dict:
        """Lit une ligne de visibilite et retourne un dict serialisable."""
        _mode = row["combo_mode"].currentData()
        return {
            "action":    row["combo_action"].currentData(),
            "dim":       row["combo_dim"].currentData(),
            "ids":       row["edit_ids"].text().strip(),
            "group":     row["combo_grp"].currentText().strip(),
            "step_mode": _mode,
            "step_val":  row["spin_val"].value(),
            "in_loop":   _mode not in ("before", "after"),
        }

    @staticmethod
    def _make_timing_widget(entry: dict, default_mode: str = "all"):
        """
        [ComboBox mode] [SpinBox valeur]
        step_mode : "before" | "all" | "every_n" | "at_k" | "after"
        """
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)

        combo = QComboBox()
        combo.setFixedWidth(120)
        combo.addItem("Avant la boucle", "before")
        combo.addItem("Tous les pas",    "all")
        combo.addItem("Tous les N pas",  "every_n")
        combo.addItem("Au pas k =",      "at_k")
        combo.addItem("Apres boucle",    "after")
        combo.setToolTip(
            "Avant la boucle : appel unique avant for k.\n"
            "Tous les pas    : appel a chaque iteration.\n"
            "Tous les N pas  : appel si k % N == 0.\n"
            "Au pas k =      : appel seulement si k == valeur.\n"
            "Apres boucle    : appel unique apres la boucle."
        )

        spin = QSpinBox()
        spin.setRange(1, 9_999_999)
        spin.setFixedWidth(72)
        spin.setToolTip("N (frequence) ou k (indice du pas, debutant a 0)")

        mode = entry.get("step_mode", default_mode)
        # Compat ascendante
        if "step_mode" not in entry:
            if not entry.get("in_loop", True):
                mode = "after"
            elif entry.get("freq", 1) > 1:
                mode = "every_n"
            else:
                mode = default_mode
        # Anciennes entrées vis avec step_mode vide → "before"
        if mode in ("", None):
            mode = "before"
        val = entry.get("step_val", entry.get("freq", 1))

        order = ["before", "all", "every_n", "at_k", "after"]
        combo.setCurrentIndex(order.index(mode) if mode in order else order.index(default_mode))
        if mode == "at_k":
            spin.setMinimum(0)
        spin.setValue(int(val))

        def _on_mode(i, s=spin):
            s.setMinimum(0 if i == 3 else 1)
            s.setEnabled(i in (2, 3))  # every_n, at_k
        combo.currentIndexChanged.connect(_on_mode)
        _on_mode(combo.currentIndex())

        lay.addWidget(combo)
        lay.addWidget(spin)
        return container, combo, spin

    def _add_gbv_row(self, dim: str, entry: dict = None):
        """\n        Ajoute une ligne de configuration GetBodyVector.        dim    : "2D" ou "3D"        entry  : dict optionnel pour pre-remplir la ligne                 {"vec": str, "ids": str, "group": str,                  "in_loop": bool, "freq": int}        """
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem

        entry = entry or {}
        rows_list   = self._gbv2_rows   if dim == "2D" else self._gbv3_rows
        rows_layout = self._gbv2_rows_layout if dim == "2D" else self._gbv3_rows_layout

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        # ── Vecteur ──────────────────────────────────────────────────────────
        combo_vec = QComboBox()
        combo_vec.addItems(self._GBV_VECS)
        combo_vec.setFixedWidth(110)
        if entry.get("vec") in self._GBV_VECS:
            combo_vec.setCurrentText(entry["vec"])
        combo_vec.setToolTip(
            "Vecteur d'etat a extraire.\n"
            "Coor0=pos init, Coor_=pos courante, X____=coord gen, "
            "V____=vitesses gen, Vfree=vitesses libres, "
            "Fext=forces ext, Fint_=forces int, "
            "Reac=reaction contact, Ireac=impulsion contact."
        )
        row_layout.addWidget(combo_vec)

        # ── IDs avatars ───────────────────────────────────────────────────────
        edit_ids = QLineEdit()
        edit_ids.setFixedWidth(120)
        edit_ids.setPlaceholderText("Ex : 1, 3, 5")
        edit_ids.setText(entry.get("ids", ""))
        edit_ids.setToolTip(
            "IDs des avatars (numerotation 1-based, ordre de creation). "
            "Prioritaire sur le groupe si les deux sont remplis."
        )
        btn_pick = QPushButton("...")
        btn_pick.setFixedWidth(28)
        btn_pick.setToolTip("Choisir les avatars depuis la liste du projet.")
        def _make_pick(e=edit_ids, d=dim):
            return lambda: self._pick_avatar_ids(e, d)
        btn_pick.clicked.connect(_make_pick())
        row_layout.addWidget(edit_ids)
        row_layout.addWidget(btn_pick)

        # ── Groupe ────────────────────────────────────────────────────────────
        combo_grp = QComboBox()
        combo_grp.setFixedWidth(110)
        combo_grp.setEditable(True)
        combo_grp.addItem("")          # vide = pas de groupe
        groups = list(
            (getattr(getattr(self, "controller", None),
                     "state", None) and
             getattr(self.controller.project, "avatar_groups", {}) or {}).keys()
        )
        combo_grp.addItems(groups)
        if entry.get("group"):
            idx = combo_grp.findText(entry["group"])
            if idx >= 0:
                combo_grp.setCurrentIndex(idx)
            else:
                combo_grp.setCurrentText(entry["group"])
        combo_grp.setToolTip(
            "Groupe d'avatars a extraire. "
            "Si vide, les IDs ci-contre sont utilises. "
            "Si les deux sont remplis, les IDs ont la priorite."
        )
        row_layout.addWidget(combo_grp)

        # ── Mode d'execution (timing) ──────────────────────────────────────
        _tc, _combo_mode, _spin_val = self._make_timing_widget(entry, default_mode="all")
        row_layout.addWidget(_tc)

        # ── Bouton supprimer ──────────────────────────────────────────────────
        btn_del = QPushButton("x")
        btn_del.setFixedWidth(24)
        btn_del.setToolTip("Supprimer cette ligne.")
        row_data = {
            "widget":     row_widget,
            "combo_vec":  combo_vec,
            "edit_ids":   edit_ids,
            "combo_grp":  combo_grp,
            "combo_mode": _combo_mode,
            "spin_val":   _spin_val,
            "dim":        dim,
        }
        def _make_del(rd=row_data, rl=rows_list, rlay=rows_layout):
            def _do_del():
                rl.remove(rd)
                rlay.removeWidget(rd["widget"])
                rd["widget"].deleteLater()
            return _do_del
        btn_del.clicked.connect(_make_del())
        row_layout.addWidget(btn_del)
        row_layout.addStretch()

        rows_layout.addWidget(row_widget)
        rows_list.append(row_data)

    def _read_gbv_row(self, row: dict) -> dict:
        """Lit les valeurs d'une ligne GBV et retourne un dict serialisable."""
        _mode = row["combo_mode"].currentData()
        return {
            "vec":       row["combo_vec"].currentText(),
            "ids":       row["edit_ids"].text().strip(),
            "group":     row["combo_grp"].currentText().strip(),
            "step_mode": _mode,
            "step_val":  row["spin_val"].value(),
            # compat ascendante
            "in_loop":   _mode not in ("before", "after"),
            "freq":      row["spin_val"].value() if _mode == "every_n" else 1,
        }

    def _pick_avatar_ids(self, target_edit: "QLineEdit", dim: str):
        """\n        Ouvre un dialogue de selection d'avatars du projet.        Insere les IDs selectionnes (1-bases) dans target_edit.        dim : "2D" ou "3D" pour filtrer les avatars affichables.        """
        if self.controller is None:
            QMessageBox.information(
                self,
                "Aucun projet",
                "Ouvrez un projet pour pouvoir selectionner les avatars.",
            )
            return

        from PyQt6.QtWidgets import QListWidget, QListWidgetItem

        avatars = self.controller.project.avatars
        # Filtrer selon la dimension
        _3D_TYPES = {
            "rigidSphere", "rigidPlan", "rigidCylinder",
            "rigidPolyhedron", "roughWall3D", "granuloRoughWall3D",
            "emptyAvatar", "mesh",
        }
        _2D_TYPES = {
            "rigidDisk", "rigidJonc", "rigidPolygon", "rigidOvoid",
            "rigidDiscrete", "rigidCluster",
            "roughWall", "fineWall", "smoothWall", "granuloWall",
            "emptyAvatar", "mesh",
        }
        filter_set = _3D_TYPES if dim == "3D" else _2D_TYPES

        # Construire la liste : (id_1based, label)
        items = []
        for i, av in enumerate(avatars, start=1):
            av_type_val = getattr(
                getattr(av, "avatar_type", None), "value", ""
            )
            if av_type_val in filter_set:
                label = "{}  [{}]  type: {}".format(
                    i,
                    getattr(av, "color", ""),
                    av_type_val,
                )
                items.append((i, label))

        if not items:
            QMessageBox.information(
                self,
                "Aucun avatar {}".format(dim),
                "Le projet ne contient aucun avatar de type {}.".format(dim),
            )
            return

        # Dialogue de selection
        dlg = QDialog(self)
        dlg.setWindowTitle("Selectionner les avatars {}".format(dim))
        dlg.resize(420, 380)
        lay = QVBoxLayout(dlg)

        lay.addWidget(_note(
            "Selectionnez un ou plusieurs avatars (Ctrl+clic ou Maj+clic). "
            "L'ID est le numero 1-base dans l'ordre de creation du projet."
        ))

        lw = QListWidget()
        lw.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        for av_id, label in items:
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, av_id)
            lw.addItem(it)

        # Pre-selectionner les IDs deja presents dans le champ
        existing_ids = set()
        for tok in target_edit.text().split(","):
            tok = tok.strip()
            if tok.isdigit():
                existing_ids.add(int(tok))
        for row in range(lw.count()):
            it = lw.item(row)
            if it.data(Qt.ItemDataRole.UserRole) in existing_ids:
                it.setSelected(True)

        lay.addWidget(lw, stretch=1)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected_ids = sorted(
                it.data(Qt.ItemDataRole.UserRole)
                for it in lw.selectedItems()
            )
            target_edit.setText(
                ", ".join(str(i) for i in selected_ids)
            )

    def _auto_detect(self):
        if self.controller is None:
            self._lbl_info.setText("(aucun projet charge)")
            return

        from lmgc90_core.compute_script import infer_chipy_contact_routines

        st = self.controller.project
        dim = st.dimension
        inferred_routines = infer_chipy_contact_routines(st)

        if dim == 3:
            self._rb_3d.setChecked(True)
            self._cb_RBDY2.setChecked(False)
            self._cb_RBDY3.setChecked(True)
        else:
            self._rb_cp.setChecked(True)
            self._cb_RBDY2.setChecked(True)
            self._cb_RBDY3.setChecked(False)

        detector_widgets = {
            "_cb_DKDKx": "use_DKDKx",
            "_cb_DKJCx": "use_DKJCx",
            "_cb_DKKDx": "use_DKKDx",
            "_cb_PLPLx": "use_PLPLx",
            "_cb_CLALp": "use_CLALp",
            "_cb_ALpALp": "use_ALpALp",
            "_cb_SPSPx": "use_SPSPx",
            "_cb_SPCDx": "use_SPCDx",
            "_cb_SPPLx": "use_SPPLx",
            "_cb_CDCDx": "use_CDCDx",
            "_cb_CDPLx": "use_CDPLx",
            "_cb_PRPRx": "use_PRPRx",
            "_cb_DKMECAx": "use_DKMECAx",
            "_cb_ALpMECAx": "use_ALpMECAx",
            "_cb_SPMECAx": "use_SPMECAx",
            "_cb_PT2Dx": "use_PT2Dx",
            "_cb_PT3Dx": "use_PT3Dx",
        }
        dimension_specific = {
            2: {
                "use_SPSPx", "use_SPCDx", "use_SPPLx", "use_CDCDx",
                "use_CDPLx", "use_PRPRx", "use_SPMECAx", "use_PT3Dx",
            },
            3: {
                "use_DKDKx", "use_DKJCx", "use_DKKDx", "use_PLPLx",
                "use_CLALp", "use_ALpALp", "use_DKMECAx", "use_ALpMECAx",
                "use_PT2Dx",
            },
        }
        for attr, key in detector_widgets.items():
            widget = getattr(self, attr)
            if inferred_routines[key]:
                widget.setChecked(True)
            elif key in dimension_specific[dim]:
                widget.setChecked(False)

        has_def = any(
            av.avatar_type.value == "mesh" for av in st.avatars
        )
        if has_def:
            self._cb_deformable.setChecked(True)
            self._on_phys_changed(self._combo_phys.currentIndex())

        has_masonry = bool(getattr(st, "masonry_patterns", {})) or any(
            getattr(av, "wall_params", None) for av in st.avatars
        )
        if has_masonry:
            self._cb_CLALp.setChecked(True)

        pt_laws  = {"ELASTIC_WIRE", "BRITTLE_ELASTIC_WIRE",
                    "ELASTIC_ROD", "VOIGT_ROD"}
        dof_laws = {"COUPLED_DOF", "NORMAL_COUPLED_DOF"}
        law_types = {
            cl.law_type.value for cl in getattr(st, "contact_laws", [])
        }
        if law_types & pt_laws:
            (self._cb_PT2Dx if dim == 2 else self._cb_PT3Dx).setChecked(True)
        if law_types & dof_laws:
            self._cb_NODES.setChecked(True)

        self._refresh_info()

    def _refresh_info(self):
        if self.controller is None:
            return
        st = self.controller.project
        n_av  = len(st.avatars)
        n_def = sum(1 for av in st.avatars if av.avatar_type.value == "mesh")
        n_mat = len(getattr(st, "materials", []))
        n_mod = len(getattr(st, "models", []))
        n_cl  = len(getattr(st, "contact_laws", []))
        groups = list((getattr(st, "avatar_groups", {}) or {}).keys())
        grp_str = (
            ", ".join(groups[:6]) + ("..." if len(groups) > 6 else "")
        ) if groups else "(aucun)"
        has_mas = bool(getattr(st, "masonry_patterns", {})) or any(
            getattr(av, "wall_params", None) for av in st.avatars
        )
        law_names = [cl.law_type.value for cl in getattr(st, "contact_laws", [])]
        self._lbl_info.setText(
            "Projet       : {}\n"
            "Dimension    : {}D\n"
            "Avatars      : {}  (dont {} deformable(s))\n"
            "Materiaux    : {}   Modeles : {}   Lois contact : {}\n"
            "Maconnerie   : {}\n"
            "Lois actives : {}{}\n"
            "Groupes      : {}".format(
                st.name,
                st.dimension,
                n_av, n_def,
                n_mat, n_mod, n_cl,
                "oui" if has_mas else "non",
                ", ".join(law_names[:5]) or "(aucune)",
                "..." if len(law_names) > 5 else "",
                grp_str,
            )
        )

    # =========================================================================
    # Collecte des parametres
    # =========================================================================

    def get_params(self) -> Dict[str, Any]:
        """\n        Retourne le dict complet des parametres configures.        Fusionnable avec ComputeTab.get_parameters().        """
        p: Dict[str, Any] = {}

        # Modele
        p["mhyp"] = (
            3 if self._rb_3d.isChecked()
            else (2 if self._rb_dp.isChecked() else 1)
        )
        p["deformable"] = self._cb_deformable.isChecked()
        p["physics"] = ["MECAx", "THERx", "POROx", "THMx"][
            self._combo_phys.currentIndex()
        ]
        p["Rloc_tol"] = self._dspin_rloc.value()

        # Routines
        for attr, key in {
            "_cb_RBDY2":    "use_RBDY2",    "_cb_RBDY3":    "use_RBDY3",
            "_cb_DKDKx":    "use_DKDKx",    "_cb_DKJCx":    "use_DKJCx",
            "_cb_DKKDx":    "use_DKKDx",    "_cb_PLPLx":    "use_PLPLx",
            "_cb_CLALp":    "use_CLALp",    "_cb_ALpALp":   "use_ALpALp",
            "_cb_SPSPx":    "use_SPSPx",    "_cb_SPCDx":    "use_SPCDx",
            "_cb_SPPLx":    "use_SPPLx",    "_cb_CDCDx":    "use_CDCDx",
            "_cb_CDPLx":    "use_CDPLx",    "_cb_PRPRx":    "use_PRPRx",
            "_cb_mecaMAILx":  "use_mecaMAILx",  "_cb_therMAILx":  "use_therMAILx",
            "_cb_poroMAILx":  "use_poroMAILx",
            "_cb_DKMECAx":  "use_DKMECAx",  "_cb_ALpMECAx": "use_ALpMECAx",
            "_cb_SPMECAx":  "use_SPMECAx",
            "_cb_PT2Dx":    "use_PT2Dx",    "_cb_PT3Dx":    "use_PT3Dx",
            "_cb_NODES":    "use_NODES",    "_cb_bulk":     "use_bulk_behav",
        }.items():
            p[key] = getattr(self, attr).isChecked()

        # Extraction — cases simples
        for attr, key in {
            "_cb_disable_log":  "disable_log",
            "_cb_vRBDY2":       "visu_RBDY2",     "_cb_vRBDY3":    "visu_RBDY3",
            "_cb_vMeca":        "visu_mecaMAILx",   "_cb_vTher":     "visu_therMAILx",
            "_cb_vHydr":        "visu_poroMAILx",   "_cb_disp_loop": "display_in_loop",
            # visibilite : gestion separee via QLineEdit
            "_cb_Rnod":         "extract_Rnod",   "_cb_Vloc":      "extract_Vloc",
            "_cb_Rloc":         "extract_Rloc",   "_cb_energy":    "extract_energy",
            "_cb_KE":           "extract_KE",     "_cb_fields":    "extract_fields",
            "_cb_internal":     "extract_internal",
        }.items():
            p[key] = getattr(self, attr).isChecked()

        # Visibilite — lignes dynamiques
        p["vis_entries"] = [self._read_vis_row(r) for r in self._vis_rows]

        # Inspection
        p["insp2d_entries"] = [self._read_insp_row(r) for r in self._insp2d_rows]
        p["insp3d_entries"] = [self._read_insp_row(r) for r in self._insp3d_rows]
        p["inspi_entries"]  = [self._read_insp_row(r) for r in self._inspi_rows]
        p["set_entries"] = [self._read_insp_row(r) for r in self._set_rows]
        for key, checkbox in self._advanced_checks.items():
            p[key] = checkbox.isChecked()
        for key, edit in self._advanced_edits.items():
            p[key] = edit.text().strip()

        # GetBodyVector RBDY2/3 — collecter toutes les entrees
        p["gbv2_entries"] = [self._read_gbv_row(r) for r in self._gbv2_rows]
        p["gbv3_entries"] = [self._read_gbv_row(r) for r in self._gbv3_rows]

        # Pilotage
        p["use_restart"]      = self._cb_restart.isChecked()
        p["restart_step"]     = self._spin_rs_step.value()
        p["use_stop_crit"]    = self._cb_stop.isChecked()
        p["stop_crit_type"]   = ["energy", "disp_max", "force_res"][
            self._combo_stop_type.currentIndex()
        ]
        p["stop_crit_val"]    = self._dspin_stop_val.value()
        p["stop_crit_freq"]   = self._spin_stop_freq.value()
        p["use_multi_step"]   = self._cb_multi.isChecked()
        p["multi_step_nb"]    = self._spin_mp_nb.value()
        p["multi_step_sizes"] = self._edit_mp_sizes.text().strip()

        return p

    # =========================================================================
    # Validation a l'acceptation
    # =========================================================================

    def _on_accept(self):
        p = self.get_params()
        errors = []

        if p["use_multi_step"]:
            try:
                sizes = [float(x) for x in p["multi_step_sizes"].split(",")]
                if len(sizes) != p["multi_step_nb"]:
                    errors.append(
                        "{} phases declarees mais {} valeur(s) de dt fournies.".format(
                            p["multi_step_nb"], len(sizes)
                        )
                    )
                if any(s <= 0 for s in sizes):
                    errors.append("Multi-pas : tous les dt doivent etre > 0.")
            except ValueError:
                errors.append(
                    "Multi-pas : format invalide pour les dt "
                    "(exemple valide : 1e-3, 1e-4, 1e-5)."
                )

        if p["deformable"] and not any(
            p.get(k) for k in ("use_mecaMAILx", "use_therMAILx", "use_poroMAILx")
        ):
            errors.append(
                "Corps deformables actives mais aucune routine MAILx "
                "(mecaMAILx / therMAILx / poroMAILx) n'est cochee dans l'onglet Routines."
            )

        advanced_setters = (
            ("advanced_set_contact_radius", "SetContactRadius",
             "advanced_set_contact_radius_args"),
            ("advanced_set_domain_boundary", "SetDomainBoundary",
             "advanced_set_domain_boundary_args"),
            ("advanced_set_number_interaction", "SetNumberInteractionByContact",
             "advanced_set_number_interaction_args"),
            ("advanced_set_periodic_condition", "SetPeriodicCondition",
             "advanced_set_periodic_condition_args"),
        )
        for option, function, args_key in advanced_setters:
            if p[option]:
                args = p[args_key]
                if not args:
                    error = "{} : indiquez les arguments requis.".format(function)
                else:
                    error = self._validate_set_action(
                        {"func": function, "args": args}, function
                    )
                if error:
                    errors.append(error)

        for index, entry in enumerate(p["set_entries"], start=1):
            error = self._validate_set_action(entry, index)
            if error:
                errors.append(error)

        if p["advanced_hdf5"] and not p["advanced_hdf5_filename"]:
            errors.append("HDF5 : indiquez un nom de fichier de sortie.")
        if p["advanced_hdf5"] and any(p[key] for key in (
            "advanced_write_out_dof", "advanced_write_out_gpv",
            "advanced_write_out_mp_values", "advanced_write_out_rnod",
            "advanced_write_out_vloc_rloc",
        )):
            errors.append(
                "HDF5 utilise WriteOut pour ecrire les donnees. "
                "Decochez les sorties ASCII individuelles."
            )
        if p["advanced_add_dof2"] and not p["advanced_write_bodies"]:
            errors.append(
                "AddDof2InBodies n'est utile qu'avec WriteBodies : cochez aussi WriteBodies."
            )

        if p["advanced_circular_selection"]:
            args = p["advanced_circular_selection_args"]
            if not args:
                errors.append("CircularSelection : indiquez les arguments (x, y, r).")
            else:
                try:
                    ast.parse(
                        "chipy.CircularSelection({})".format(args),
                        mode="eval",
                    )
                except SyntaxError as exc:
                    errors.append(
                        "CircularSelection : arguments Python invalides ({}).".format(
                            exc.msg
                        )
                    )

        if p["advanced_fd_select_prox"] and self.controller is not None:
            pairs = {
                (rule.candidate_contactor, rule.antagonist_contactor)
                for rule in self.controller.project.visibility
            }
            if not pairs or any(pair != ("SPHER", "SPHER") for pair in pairs):
                errors.append(
                    "FdSelectProxTactors est reserve aux projets dont tous les "
                    "contacts sont SPHER/SPHER."
                )

        if errors:
            QMessageBox.warning(
                self,
                "Parametres invalides",
                "Les erreurs suivantes ont ete detectees :\n\n"
                + "\n".join("- {}".format(e) for e in errors)
                + "\n\nCorrigez-les avant de valider.",
            )
            return

        self.accept()

    # =========================================================================
    # Restauration des valeurs par defaut
    # =========================================================================

    def _on_restore_defaults(self):
        reply = QMessageBox.question(
            self,
            "Restaurer les valeurs par defaut",
            "Reinitialiser toutes les options chipy aux valeurs par defaut ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._params = dict(self.DEFAULTS)
            self._load()

    # =========================================================================
    # Apercu du script genere
    # =========================================================================

    def _show_preview(self):

        from lmgc90_core import emit_chipy
        preview_params = {
            "dt": 1e-3, "nb_steps": 100, "theta": 0.5,
            "tol": 1.666e-4, "relax": 1.0, "norm": "Quad ",
            "gs_it1": 50, "gs_it2": 1000,
            "solver_type": "Stored_Delassus_Loops         ",
            "freq_write": 10, "freq_display": 10,
        }
        preview_params.update(self.get_params())

        if self.controller is None:
            script = (
                "# Apercu non disponible : aucun projet charge.\n"
                "# Ouvrez ou creez un projet, puis relancez l'apercu.\n"
            )
        else:
            try:
                script = emit_chipy(self.controller.project, **preview_params)
            except Exception as exc:
                import traceback as _tb
                script = (
                    "# Erreur lors de la generation du script :\n"
                    "# {}\n\n".format(exc)
                    + "".join(
                        "# {}\n".format(line)
                        for line in _tb.format_exc().splitlines()
                    )
                )

        dlg = QDialog(self)
        dlg.setWindowTitle("Apercu -- command.py")
        dlg.resize(740, 580)
        lay = QVBoxLayout(dlg)

        te = QTextEdit()
        te.setReadOnly(True)
        te.setFont(QFont("Courier New", 9))
        te.setStyleSheet("background:#1e1e1e; color:#d4d4d4;")
        te.setPlainText(script)
        lay.addWidget(te)

        lbl = QLabel(
            "{} lignes  --  "
            "parametres numeriques indicatifs (apercu uniquement)".format(
                script.count("\n")
            )
        )
        lbl.setStyleSheet("color:#888; font-size:8pt;")
        lay.addWidget(lbl)

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(dlg.reject)
        lay.addWidget(btn)
        dlg.exec()