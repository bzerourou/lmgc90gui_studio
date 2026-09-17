"""ComputeTab — configuration + pilotage du calcul chipy.

Paramètres temporels / solveur / I/O, détection auto depuis le modèle
(dimension, déformables, résumés lois/visibilité), préparation DATBOX + run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .base_tab import BaseTab


def create_compute_tab(parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox,
        QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
        QScrollArea, QTextEdit, QVBoxLayout, QWidget,
    )

    class ComputeTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._runner = None
            self._log_dialog = None

            root = QVBoxLayout(self)
            root.setContentsMargins(4, 4, 4, 4)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            body = QWidget()
            layout = QVBoxLayout(body)

            layout.addWidget(QLabel("<h2>⚙️ Configuration du calcul</h2>"))

            # ── Model summary ─────────────────────────────────────────
            self.model_lbl = QLabel("Modèle : —")
            self.model_lbl.setWordWrap(True)
            self.model_lbl.setStyleSheet(
                "background:#1a2332;color:#cde;padding:8px;border-radius:6px;"
            )
            layout.addWidget(self.model_lbl)

            # ── Time ──────────────────────────────────────────────────
            time_g = QGroupBox("⏱️ Paramètres temporels")
            tf = QFormLayout(time_g)
            self.dt_input = QLineEdit("1e-3")
            self.nb_steps_input = QLineEdit("1000")
            self.theta_input = QLineEdit("0.5")
            tf.addRow("Pas de temps (dt)", self.dt_input)
            tf.addRow("Nombre d'itérations", self.nb_steps_input)
            tf.addRow("Theta intégrateur", self.theta_input)
            layout.addWidget(time_g)

            # ── Solver ────────────────────────────────────────────────
            sol_g = QGroupBox("🔧 Solveur de contact")
            sf = QFormLayout(sol_g)
            self.tol_input = QLineEdit("1.666e-4")
            self.relax_input = QLineEdit("1.0")
            self.norm_combo = QComboBox()
            self.norm_combo.addItems(["Quad ", "QM   ", "Maxim"])
            self.gs_it1_input = QLineEdit("50")
            self.gs_it2_input = QLineEdit("1000")
            self.solver_combo = QComboBox()
            self.solver_combo.addItems([
                "Stored_Delassus_Loops         ",
                "Exchange_Local_Global         ",
                "Conjugate_Gradient            ",
            ])
            sf.addRow("Tolérance", self.tol_input)
            sf.addRow("Relaxation", self.relax_input)
            sf.addRow("Norme", self.norm_combo)
            sf.addRow("Itérations GS1", self.gs_it1_input)
            sf.addRow("Itérations GS2", self.gs_it2_input)
            sf.addRow("Type de solveur", self.solver_combo)
            layout.addWidget(sol_g)

            # ── I/O ───────────────────────────────────────────────────
            io_g = QGroupBox("💾 Sorties")
            iof = QFormLayout(io_g)
            self.freq_write_input = QLineEdit("50")
            self.freq_display_input = QLineEdit("50")
            self.disable_log_check = QCheckBox("Disable chipy log messages")
            self.disable_log_check.setChecked(True)
            self.deformable_check = QCheckBox("ReadDatbox(deformable=True)")
            iof.addRow("Fréquence WriteOut", self.freq_write_input)
            iof.addRow("Fréquence Display", self.freq_display_input)
            iof.addRow(self.disable_log_check)
            iof.addRow(self.deformable_check)
            layout.addWidget(io_g)

            # ── Chipy routines (legacy dialog) ─────────────────────────
            chipy_g = QGroupBox("🔧 Routines chipy (modèle, contacteurs, extraction, pilotage)")
            chipy_l = QHBoxLayout(chipy_g)
            self._chipy_params: dict = {}
            self.btn_chipy = QPushButton("Configurer les routines chipy…")
            self.btn_chipy.setToolTip(
                "Ouvre le dialogue multi-onglets : Modèle, Routines, Extraction, Pilotage, Inspecteurs."
            )
            self.btn_chipy.clicked.connect(self._open_chipy_dialog)
            self._chipy_summary = QLabel("<i>valeurs par défaut — cliquez pour configurer</i>")
            self._chipy_summary.setWordWrap(True)
            chipy_l.addWidget(self.btn_chipy)
            chipy_l.addWidget(self._chipy_summary, stretch=1)
            layout.addWidget(chipy_g)

            # ── Work dir ──────────────────────────────────────────────
            work_g = QGroupBox("📁 Répertoire de calcul")
            wl = QHBoxLayout(work_g)
            self.work_edit = QLineEdit()
            self.work_edit.setPlaceholderText("Dossier contenant DATBOX / command.py")
            btn_browse = QPushButton("Parcourir…")
            btn_browse.clicked.connect(self._browse_work)
            wl.addWidget(self.work_edit, stretch=1)
            wl.addWidget(btn_browse)
            layout.addWidget(work_g)

            # ── Actions ───────────────────────────────────────────────
            act = QHBoxLayout()
            self.btn_from_prefs = QPushButton("📥 Charger préférences")
            self.btn_to_prefs = QPushButton("💾 Sauver → préférences")
            self.btn_prepare = QPushButton("📦 Préparer DATBOX / scripts")
            self.btn_run = QPushButton("▶️ Lancer le calcul (F5)")
            self.btn_stop = QPushButton("⏹️ Stop")
            self.btn_stop.setEnabled(False)
            for b, slot in (
                (self.btn_from_prefs, self._load_from_prefs),
                (self.btn_to_prefs, self._save_to_prefs),
                (self.btn_prepare, self._prepare),
                (self.btn_run, self._run),
                (self.btn_stop, self._stop),
            ):
                b.clicked.connect(slot)
                act.addWidget(b)
            layout.addLayout(act)

            self.status_lbl = QLabel("Prêt.")
            self.status_lbl.setStyleSheet("color:#8cf;")
            layout.addWidget(self.status_lbl)

            self.log_view = QTextEdit()
            self.log_view.setReadOnly(True)
            self.log_view.setMinimumHeight(160)
            self.log_view.setPlaceholderText("Journal du calcul…")
            layout.addWidget(self.log_view, stretch=1)

            scroll.setWidget(body)
            root.addWidget(scroll)

        # ------------------------------------------------------------------ model-driven defaults
        def on_state_changed(self) -> None:
            self._refresh_model_summary()

        def _refresh_model_summary(self) -> None:
            if self.controller is None:
                self.model_lbl.setText("Modèle : (pas de projet)")
                return
            p = self.controller.project
            dim = int(p.dimension)
            n_av = len(p.avatars)
            n_pop = sum(len(x) for x in p.populations)
            n_law = len(p.laws)
            n_see = len(p.visibility)
            n_dof = len(p.operations)
            types = {}
            has_mesh = False
            from lmgc90_core.types import AvatarType
            for av in p.avatars:
                t = av.avatar_type.value
                types[t] = types.get(t, 0) + 1
                if av.avatar_type == AvatarType.MESH_DEFORMABLE:
                    has_mesh = True
            rbdy = "RBDY2" if dim == 2 else "RBDY3"
            type_s = ", ".join(f"{k}×{v}" for k, v in sorted(types.items())[:8])
            self.model_lbl.setText(
                f"<b>Projet</b> {p.name!r} — <b>{dim}D</b> — corps {rbdy}<br>"
                f"Avatars AoS: {n_av} — Populations SoA: {n_pop} particules<br>"
                f"Lois contact: {n_law} — See tables: {n_see} — DOF ops: {n_dof}<br>"
                f"Types: {type_s or '—'}<br>"
                f"Déformable détecté: {'oui' if has_mesh else 'non'}"
            )
            if has_mesh:
                self.deformable_check.setChecked(True)
            # work dir from prefs
            if self.controller.prefs.work_directory and not self.work_edit.text().strip():
                self.work_edit.setText(self.controller.prefs.work_directory)

        def bind_controller(self, controller) -> None:
            super().bind_controller(controller)
            self._load_from_prefs()
            self._refresh_model_summary()

        # ------------------------------------------------------------------ params I/O
        def get_parameters(self) -> dict[str, Any]:
            dim = 2
            if self.controller is not None:
                dim = int(self.controller.project.dimension)
            base = {
                "dt": float(self.dt_input.text().replace(",", ".")),
                "nb_steps": int(float(self.nb_steps_input.text().replace(",", "."))),
                "theta": float(self.theta_input.text().replace(",", ".")),
                "tol": float(self.tol_input.text().replace(",", ".")),
                "relax": float(self.relax_input.text().replace(",", ".")),
                "norm": self.norm_combo.currentText(),
                "gs_it1": int(self.gs_it1_input.text()),
                "gs_it2": int(self.gs_it2_input.text()),
                "solver_type": self.solver_combo.currentText(),
                "freq_write": int(self.freq_write_input.text()),
                "freq_display": int(self.freq_display_input.text()),
                "disable_log": self.disable_log_check.isChecked(),
                "deformable": self.deformable_check.isChecked(),
                "dimension": dim,
            }
            # overlay full chipy routines dialog params
            base.update(getattr(self, "_chipy_params", {}) or {})
            # form fields win for the classic solver/time keys
            base.update({
                "dt": float(self.dt_input.text().replace(",", ".")),
                "nb_steps": int(float(self.nb_steps_input.text().replace(",", "."))),
                "theta": float(self.theta_input.text().replace(",", ".")),
                "tol": float(self.tol_input.text().replace(",", ".")),
                "relax": float(self.relax_input.text().replace(",", ".")),
                "norm": self.norm_combo.currentText(),
                "gs_it1": int(self.gs_it1_input.text()),
                "gs_it2": int(self.gs_it2_input.text()),
                "solver_type": self.solver_combo.currentText(),
                "freq_write": int(self.freq_write_input.text()),
                "freq_display": int(self.freq_display_input.text()),
                "disable_log": self.disable_log_check.isChecked(),
                "deformable": self.deformable_check.isChecked() or bool((self._chipy_params or {}).get("deformable")),
                "dimension": dim,
            })
            return base

        def _apply_params_to_form(self, d: dict[str, Any]) -> None:
            def _s(key, widget, cast=str):
                if key in d and d[key] is not None:
                    widget.setText(str(d[key]))

            _s("dt", self.dt_input)
            _s("nb_steps", self.nb_steps_input)
            _s("theta", self.theta_input)
            _s("tol", self.tol_input)
            _s("relax", self.relax_input)
            _s("gs_it1", self.gs_it1_input)
            _s("gs_it2", self.gs_it2_input)
            _s("freq_write", self.freq_write_input)
            _s("freq_display", self.freq_display_input)
            if "norm" in d:
                i = self.norm_combo.findText(str(d["norm"]))
                if i >= 0:
                    self.norm_combo.setCurrentIndex(i)
            if "solver_type" in d:
                i = self.solver_combo.findText(str(d["solver_type"]))
                if i < 0:
                    # try strip match
                    for j in range(self.solver_combo.count()):
                        if self.solver_combo.itemText(j).strip() == str(d["solver_type"]).strip():
                            i = j
                            break
                if i >= 0:
                    self.solver_combo.setCurrentIndex(i)
            if "disable_log" in d:
                self.disable_log_check.setChecked(bool(d["disable_log"]))
            if "deformable" in d:
                self.deformable_check.setChecked(bool(d["deformable"]))

        def _load_from_prefs(self) -> None:
            if self.controller is None:
                return
            pr = self.controller.prefs
            self._apply_params_to_form(pr.chipy_params())
            if pr.work_directory:
                self.work_edit.setText(pr.work_directory)
            self.status_lbl.setText("Paramètres chargés depuis les préférences.")

        def _save_to_prefs(self) -> None:
            if self.controller is None:
                return
            try:
                p = self.get_parameters()
            except Exception as e:
                QMessageBox.warning(self, "Compute", f"Paramètres invalides : {e}")
                return
            pr = self.controller.prefs
            pr.dt = p["dt"]
            pr.nb_steps = p["nb_steps"]
            pr.theta = p["theta"]
            pr.tol = p["tol"]
            pr.relax = p["relax"]
            pr.gs_it1 = p["gs_it1"]
            pr.gs_it2 = p["gs_it2"]
            pr.freq_write = p["freq_write"]
            pr.freq_display = p["freq_display"]
            pr.solver_type = p["solver_type"]
            if hasattr(pr, "norm"):
                pr.norm = p["norm"]
            if hasattr(pr, "deformable"):
                pr.deformable = p["deformable"]
            if hasattr(pr, "disable_log"):
                pr.disable_log = p["disable_log"]
            pr.work_directory = self.work_edit.text().strip()
            try:
                self.controller.save_preferences()
                self.status_lbl.setText("Préférences enregistrées.")
            except Exception as e:
                QMessageBox.warning(self, "Compute", str(e))

        def _browse_work(self) -> None:
            start = self.work_edit.text().strip() or str(Path.cwd())
            path = QFileDialog.getExistingDirectory(self, "Répertoire de calcul", start)
            if path:
                self.work_edit.setText(path)

        def _work_dir(self) -> Optional[Path]:
            text = self.work_edit.text().strip()
            if text:
                return Path(text)
            path = QFileDialog.getExistingDirectory(
                self, "Choisir le répertoire de calcul", str(Path.cwd())
            )
            if not path:
                return None
            self.work_edit.setText(path)
            return Path(path)

        # ------------------------------------------------------------------ prepare / run
        def _prepare(self) -> None:
            if self.controller is None:
                return
            work = self._work_dir()
            if work is None:
                return
            try:
                params = self.get_parameters()
            except Exception as e:
                QMessageBox.warning(self, "Compute", f"Paramètres invalides : {e}")
                return
            # push into prefs so prepare_run_directory / workers see them
            self._save_to_prefs()
            self.status_lbl.setText("Préparation en cours…")
            self.log_view.append(f"→ prepare {work}")
            try:
                # write scripts with explicit chipy params
                work.mkdir(parents=True, exist_ok=True)
                pre_path = work / "pre.py"
                self.controller.emit_pre_script(pre_path)
                cmd_path = work / "command.py"
                self.controller.emit_chipy_script(cmd_path, **params)
                paths = {"pre": str(pre_path), "command": str(cmd_path)}
                if self.controller.prefs.auto_write_datbox and self.controller.pylmgc_available():
                    self.controller.materialize(force=True)
                    db = self.controller.write_datbox(work / "DATBOX")
                    paths["datbox"] = str(db)
                self.log_view.append("Written:\n  " + "\n  ".join(f"{k}: {v}" for k, v in paths.items()))
                self.status_lbl.setText("Scripts / DATBOX prêts.")
                QMessageBox.information(
                    self, "Préparer",
                    "Écrit :\n" + "\n".join(f"  {k}: {v}" for k, v in paths.items()),
                )
            except Exception as exc:
                self.controller.journal.exception("compute prepare", exc)
                self.status_lbl.setText("Échec préparation.")
                QMessageBox.critical(self, "Préparer", str(exc))

        def _run(self) -> None:
            if self.controller is None:
                return
            work = self._work_dir()
            if work is None:
                return
            if not (work / "command.py").is_file():
                r = QMessageBox.question(
                    self, "Compute",
                    f"Pas de command.py dans\n{work}\n\nPréparer maintenant ?",
                )
                if r != QMessageBox.StandardButton.Yes:
                    return
                self._prepare()
                if not (work / "command.py").is_file():
                    return

            if self.controller.prefs.confirm_run:
                r = QMessageBox.question(
                    self, "Lancer le calcul",
                    f"Exécuter dans :\n{work}\n\n"
                    f"{self.controller.prefs.python_executable} command.py",
                )
                if r != QMessageBox.StandardButton.Yes:
                    return

            from ...workers.compute_worker import create_compute_worker

            self.log_view.clear()
            self.log_view.append(f"▶ {self.controller.prefs.python_executable} command.py")
            self.log_view.append(f"  cwd = {work}")
            self.btn_run.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.status_lbl.setText("Calcul en cours…")

            runner = create_compute_worker(
                work,
                python_executable=self.controller.prefs.python_executable,
            )
            self._runner = runner

            def on_line(line: str):
                self.log_view.append(line)
                self.controller.journal.info(line)

            def on_finished(rc: int):
                self.btn_run.setEnabled(True)
                self.btn_stop.setEnabled(False)
                self.status_lbl.setText(f"Terminé (rc={rc})")
                self.log_view.append(f"— finished rc={rc}")
                self.controller.journal.info(f"Computation finished rc={rc}")

            def on_failed(msg: str):
                self.btn_run.setEnabled(True)
                self.btn_stop.setEnabled(False)
                self.status_lbl.setText("Échec")
                self.log_view.append(f"ERROR: {msg}")
                self.controller.journal.error(msg)
                QMessageBox.critical(self, "Compute", msg)

            runner.worker.line_out.connect(on_line)
            runner.worker.finished.connect(on_finished)
            runner.worker.failed.connect(on_failed)
            runner.start()
            self.controller.journal.info(f"Starting computation in {work}")

        def _stop(self) -> None:
            if self._runner is not None:
                try:
                    self._runner.worker.stop()
                except Exception:
                    pass
            self.status_lbl.setText("Arrêt demandé…")
            self.btn_stop.setEnabled(False)

        def _open_chipy_dialog(self) -> None:
            from ...dialogs.chipy_routines_dialog import ChipyRoutinesDialog
            dlg = ChipyRoutinesDialog(
                current_params=dict(self._chipy_params),
                controller=self.controller,
                parent=self,
            )
            if dlg.exec():
                self._chipy_params = dlg.get_params()
                self._update_chipy_summary()
                # sync deformable checkbox
                if self._chipy_params.get("deformable"):
                    self.deformable_check.setChecked(True)

        def _update_chipy_summary(self) -> None:
            p = self._chipy_params or {}
            parts = []
            if p.get("deformable"):
                parts.append(f"Déformable ({p.get('physics', 'MECAx')})")
            mhyp = p.get("mhyp", 1)
            parts.append(f"mhyp={mhyp}")
            tacts = [t for t in (
                "DKDKx", "DKJCx", "DKKDx", "PLPLx", "CLALp", "ALpALp",
                "SPSPx", "SPCDx", "SPPLx", "CDCDx", "CDPLx", "PRPRx",
                "DKMECAx", "ALpMECAx", "SPMECAx", "PT2Dx", "PT3Dx", "NODES",
            ) if p.get(f"use_{t}")]
            if tacts:
                parts.append("Détecteurs: " + ", ".join(tacts[:5]) + ("…" if len(tacts) > 5 else ""))
            bodies = []
            if p.get("use_RBDY2"):
                bodies.append("RBDY2")
            if p.get("use_RBDY3"):
                bodies.append("RBDY3")
            if bodies:
                parts.append("Corps: " + "+".join(bodies))
            extras = []
            if p.get("use_restart"):
                extras.append("restart")
            if p.get("use_stop_crit"):
                extras.append("critère arrêt")
            if p.get("use_multi_step"):
                extras.append("multi-pas")
            if extras:
                parts.append(", ".join(extras))
            self._chipy_summary.setText(
                "<b>Routines chipy :</b> " + ("  |  ".join(parts) if parts else "valeurs par défaut")
            )

        def run_computation(self) -> None:
            """Public API for F5 / menu."""
            self._run()

        def prepare_scripts(self) -> None:
            self._prepare()

    return ComputeTab(parent)
