"""Preferences dialog — computation, environment, paths, autosave, performance.

Port of useful legacy LMGC90_GUI preferences into Studio.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.preferences import Preferences


def create_preferences_dialog(prefs: "Preferences", parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
        QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
        QSpinBox, QTabWidget, QVBoxLayout, QWidget,
    )

    class PreferencesDialog(QDialog):
        def __init__(self, prefs: "Preferences", parent=None):
            super().__init__(parent)
            self.setWindowTitle("Préférences")
            self.resize(520, 560)
            self.prefs = prefs
            layout = QVBoxLayout(self)
            tabs = QTabWidget()
            layout.addWidget(tabs)

            # ── Calcul ──────────────────────────────────────────────────
            comp = QWidget()
            cf = QFormLayout(comp)
            self.dt = QDoubleSpinBox(); self.dt.setRange(1e-12, 10); self.dt.setDecimals(8); self.dt.setValue(prefs.dt)
            self.nb_steps = QSpinBox(); self.nb_steps.setRange(1, 10_000_000); self.nb_steps.setValue(prefs.nb_steps)
            self.theta = QDoubleSpinBox(); self.theta.setRange(0, 1); self.theta.setDecimals(4); self.theta.setValue(prefs.theta)
            self.tol = QDoubleSpinBox(); self.tol.setRange(0, 1); self.tol.setDecimals(10); self.tol.setValue(prefs.tol)
            self.relax = QDoubleSpinBox(); self.relax.setRange(0, 2); self.relax.setDecimals(4); self.relax.setValue(prefs.relax)
            self.gs_it1 = QSpinBox(); self.gs_it1.setRange(1, 100000); self.gs_it1.setValue(prefs.gs_it1)
            self.gs_it2 = QSpinBox(); self.gs_it2.setRange(1, 100000); self.gs_it2.setValue(prefs.gs_it2)
            self.freq_write = QSpinBox(); self.freq_write.setRange(1, 100000); self.freq_write.setValue(prefs.freq_write)
            self.freq_display = QSpinBox(); self.freq_display.setRange(1, 100000); self.freq_display.setValue(prefs.freq_display)
            self.solver = QLineEdit(prefs.solver_type)
            self.deformable = QCheckBox("Modèle déformable (chipy)"); self.deformable.setChecked(prefs.deformable)
            self.disable_log = QCheckBox("Désactiver log chipy verbeux"); self.disable_log.setChecked(prefs.disable_log)
            for label, w in (
                ("dt", self.dt), ("nb_steps", self.nb_steps), ("theta", self.theta),
                ("tol", self.tol), ("relax", self.relax),
                ("gs_it1", self.gs_it1), ("gs_it2", self.gs_it2),
                ("freq_write", self.freq_write), ("freq_display", self.freq_display),
                ("solver_type", self.solver),
            ):
                cf.addRow(label, w)
            cf.addRow("", self.deformable)
            cf.addRow("", self.disable_log)
            tabs.addTab(comp, "Calcul")

            # ── Chemins / environnement (legacy Paths) ──────────────────
            env = QWidget()
            ef = QFormLayout(env)
            self.python = QLineEdit(prefs.python_executable)
            self.workdir = QLineEdit(prefs.work_directory)
            self.workdir.setPlaceholderText("dossier d'export par défaut")
            self.projdir = QLineEdit(prefs.projects_directory)
            self.projdir.setPlaceholderText("dossier Open / Save par défaut")
            btn_w = QPushButton("Parcourir…")
            btn_w.clicked.connect(lambda: self._browse(self.workdir))
            btn_p = QPushButton("Parcourir…")
            btn_p.clicked.connect(lambda: self._browse(self.projdir))
            row_w = QHBoxLayout(); row_w.addWidget(self.workdir); row_w.addWidget(btn_w)
            row_p = QHBoxLayout(); row_p.addWidget(self.projdir); row_p.addWidget(btn_p)
            wrap_w = QWidget(); wrap_w.setLayout(row_w)
            wrap_p = QWidget(); wrap_p.setLayout(row_p)

            self.auto_datbox = QCheckBox("DATBOX live si pylmgc90 disponible")
            self.auto_datbox.setChecked(prefs.auto_write_datbox)
            self.confirm_run = QCheckBox("Confirmer avant Run computation")
            self.confirm_run.setChecked(prefs.confirm_run)
            self.journal_file = QCheckBox("Écrire aussi le journal dans un fichier")
            self.journal_file.setChecked(prefs.journal_to_file)
            self.journal_path = QLineEdit(prefs.journal_path)
            self.dim = QSpinBox(); self.dim.setRange(2, 3); self.dim.setValue(prefs.default_dimension)
            self.units = QComboBox(); self.units.addItems(["SI", "CGS"])
            self.units.setCurrentText(prefs.units if prefs.units in ("SI", "CGS") else "SI")
            self.units.setToolTip("Métadonnée d'affichage (conversion non appliquée partout)")
            self.language = QComboBox(); self.language.addItems(["fr", "en"])
            self.language.setCurrentText(prefs.language if prefs.language in ("fr", "en") else "fr")

            ef.addRow("Interpréteur Python", self.python)
            ef.addRow("Dossier de travail", wrap_w)
            ef.addRow("Dossier projets (Open/Save)", wrap_p)
            ef.addRow("", self.auto_datbox)
            ef.addRow("", self.confirm_run)
            ef.addRow("", self.journal_file)
            ef.addRow("Fichier journal", self.journal_path)
            ef.addRow("Dimension par défaut", self.dim)
            ef.addRow("Unités", self.units)
            ef.addRow("Langue UI", self.language)
            tabs.addTab(env, "Chemins")

            # ── Sauvegarde auto + récents (legacy) ──────────────────────
            save = QWidget()
            sf = QFormLayout(save)
            self.auto_save = QCheckBox("Sauvegarde automatique périodique")
            self.auto_save.setChecked(prefs.auto_save)
            self.auto_save_interval = QSpinBox()
            self.auto_save_interval.setRange(1, 120)
            self.auto_save_interval.setValue(int(prefs.auto_save_interval_min))
            self.auto_save_interval.setSuffix(" min")
            self.auto_save_quit = QCheckBox("Sauvegarder à la fermeture (si projet nommé)")
            self.auto_save_quit.setChecked(prefs.auto_save_on_quit)
            self.recent_max = QSpinBox()
            self.recent_max.setRange(0, 30)
            self.recent_max.setValue(int(prefs.recent_max))
            sf.addRow("", self.auto_save)
            sf.addRow("Intervalle", self.auto_save_interval)
            sf.addRow("", self.auto_save_quit)
            sf.addRow("Nb projets récents", self.recent_max)
            sf.addRow(QLabel(
                f"<i>{len(prefs.recent_projects or [])} entrée(s) en mémoire</i>"
            ))
            tabs.addTab(save, "Sauvegarde")

            # ── Performance (legacy) ────────────────────────────────────
            perf = QWidget()
            pf = QFormLayout(perf)
            self.show_tree = QCheckBox("Afficher les avatars dans l'arbre modèle")
            self.show_tree.setChecked(prefs.show_avatars_in_tree)
            self.show_tree.setToolTip(
                "Désactiver améliore les perfs sur les gros projets (> milliers d'avatars)."
            )
            self.show_granulo = QCheckBox("Lister les grains granulo individuellement (AoS)")
            self.show_granulo.setChecked(prefs.show_granulo_individually)
            self.create_pylmgc = QCheckBox("Créer objets pylmgc à la génération massive")
            self.create_pylmgc.setChecked(prefs.create_pylmgc_on_generate)
            self.max_tree = QSpinBox()
            self.max_tree.setRange(100, 1_000_000)
            self.max_tree.setValue(int(prefs.max_tree_avatars))
            self.script_loop = QCheckBox("pre.py : boucles compactes (script_use_loop)")
            self.script_loop.setChecked(prefs.script_use_loop)
            self.auto_view = QCheckBox("Rafraîchir le viewer automatiquement")
            self.auto_view.setChecked(prefs.auto_refresh_viewer)
            self.dof_def = QCheckBox("Viewer : case DOF cochée par défaut")
            self.dof_def.setChecked(prefs.viewer_show_dof_default)
            self.laws_def = QCheckBox("Viewer : case Lois cochée par défaut")
            self.laws_def.setChecked(prefs.viewer_show_laws_default)
            pf.addRow("", self.show_tree)
            pf.addRow("", self.show_granulo)
            pf.addRow("", self.create_pylmgc)
            pf.addRow("Limite soft arbre", self.max_tree)
            pf.addRow("", self.script_loop)
            pf.addRow("", self.auto_view)
            pf.addRow("", self.dof_def)
            pf.addRow("", self.laws_def)
            tabs.addTab(perf, "Performance")

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def _browse(self, line: QLineEdit) -> None:
            path = QFileDialog.getExistingDirectory(self, "Choisir un dossier", line.text() or "")
            if path:
                line.setText(path)

        def apply_to(self, prefs: "Preferences") -> "Preferences":
            prefs.dt = self.dt.value()
            prefs.nb_steps = self.nb_steps.value()
            prefs.theta = self.theta.value()
            prefs.tol = self.tol.value()
            prefs.relax = self.relax.value()
            prefs.gs_it1 = self.gs_it1.value()
            prefs.gs_it2 = self.gs_it2.value()
            prefs.freq_write = self.freq_write.value()
            prefs.freq_display = self.freq_display.value()
            prefs.solver_type = self.solver.text()
            prefs.deformable = self.deformable.isChecked()
            prefs.disable_log = self.disable_log.isChecked()
            prefs.python_executable = self.python.text().strip() or "python"
            prefs.work_directory = self.workdir.text().strip()
            prefs.projects_directory = self.projdir.text().strip()
            prefs.auto_write_datbox = self.auto_datbox.isChecked()
            prefs.confirm_run = self.confirm_run.isChecked()
            prefs.journal_to_file = self.journal_file.isChecked()
            prefs.journal_path = self.journal_path.text().strip()
            prefs.default_dimension = self.dim.value()
            prefs.units = self.units.currentText()
            prefs.language = self.language.currentText()
            prefs.auto_save = self.auto_save.isChecked()
            prefs.auto_save_interval_min = self.auto_save_interval.value()
            prefs.auto_save_on_quit = self.auto_save_quit.isChecked()
            prefs.recent_max = self.recent_max.value()
            prefs.show_avatars_in_tree = self.show_tree.isChecked()
            prefs.show_granulo_individually = self.show_granulo.isChecked()
            prefs.create_pylmgc_on_generate = self.create_pylmgc.isChecked()
            prefs.max_tree_avatars = self.max_tree.value()
            prefs.script_use_loop = self.script_loop.isChecked()
            prefs.auto_refresh_viewer = self.auto_view.isChecked()
            prefs.viewer_show_dof_default = self.dof_def.isChecked()
            prefs.viewer_show_laws_default = self.laws_def.isChecked()
            # trim recent list if max lowered
            prefs.recent_projects = list(prefs.recent_projects or [])[: prefs.recent_max]
            return prefs

    return PreferencesDialog(prefs, parent)
