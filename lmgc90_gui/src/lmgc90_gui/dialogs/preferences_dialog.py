"""Preferences dialog — computation defaults + environment."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..utils.preferences import Preferences


def create_preferences_dialog(prefs: "Preferences", parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
        QGroupBox, QLineEdit, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
    )

    class PreferencesDialog(QDialog):
        def __init__(self, prefs: "Preferences", parent=None):
            super().__init__(parent)
            self.setWindowTitle("Preferences")
            self.resize(480, 520)
            self.prefs = prefs
            layout = QVBoxLayout(self)
            tabs = QTabWidget()
            layout.addWidget(tabs)

            # --- computation ---
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
            for label, w in (
                ("dt", self.dt), ("nb_steps", self.nb_steps), ("theta", self.theta),
                ("tol", self.tol), ("relax", self.relax),
                ("gs_it1", self.gs_it1), ("gs_it2", self.gs_it2),
                ("freq_write", self.freq_write), ("freq_display", self.freq_display),
                ("solver_type", self.solver),
            ):
                cf.addRow(label, w)
            tabs.addTab(comp, "Computation")

            # --- environment ---
            env = QWidget()
            ef = QFormLayout(env)
            self.python = QLineEdit(prefs.python_executable)
            self.workdir = QLineEdit(prefs.work_directory)
            self.workdir.setPlaceholderText("empty = use chosen export folder")
            self.auto_datbox = QCheckBox("Try live DATBOX when pylmgc90 available")
            self.auto_datbox.setChecked(prefs.auto_write_datbox)
            self.confirm_run = QCheckBox("Confirm before Run computation")
            self.confirm_run.setChecked(prefs.confirm_run)
            self.journal_file = QCheckBox("Also write journal to file")
            self.journal_file.setChecked(prefs.journal_to_file)
            self.journal_path = QLineEdit(prefs.journal_path)
            self.dim = QSpinBox(); self.dim.setRange(2, 3); self.dim.setValue(prefs.default_dimension)
            ef.addRow("Python executable", self.python)
            ef.addRow("Default work directory", self.workdir)
            ef.addRow("", self.auto_datbox)
            ef.addRow("", self.confirm_run)
            ef.addRow("", self.journal_file)
            ef.addRow("Journal file path", self.journal_path)
            ef.addRow("Default dimension", self.dim)
            tabs.addTab(env, "Environment")

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

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
            prefs.python_executable = self.python.text().strip() or "python"
            prefs.work_directory = self.workdir.text().strip()
            prefs.auto_write_datbox = self.auto_datbox.isChecked()
            prefs.confirm_run = self.confirm_run.isChecked()
            prefs.journal_to_file = self.journal_file.isChecked()
            prefs.journal_path = self.journal_path.text().strip()
            prefs.default_dimension = self.dim.value()
            return prefs

    return PreferencesDialog(prefs, parent)
