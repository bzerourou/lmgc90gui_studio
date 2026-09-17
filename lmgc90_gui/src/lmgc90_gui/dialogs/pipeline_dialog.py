"""Pipeline / SLURM export dialog."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_pipeline_dialog(controller: "ProjectController", parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
        QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTextEdit,
        QVBoxLayout,
    )
    from lmgc90_core import Pipeline, render_sbatch

    class PipelineDialog(QDialog):
        def __init__(self, controller: "ProjectController", parent=None):
            super().__init__(parent)
            self.controller = controller
            self.setWindowTitle("Pipeline / SLURM")
            self.resize(640, 520)
            layout = QVBoxLayout(self)

            form = QFormLayout()
            self.backend = QComboBox()
            self.backend.addItems(["local", "slurm"])
            self.job_name = QLineEdit(controller.project.name.replace(" ", "_")[:40])
            self.partition = QLineEdit("cpu")
            self.account = QLineEdit()
            self.account.setPlaceholderText("optional account")
            self.time = QLineEdit("04:00:00")
            self.ntasks = QSpinBox(); self.ntasks.setRange(1, 1024); self.ntasks.setValue(1)
            self.cpus = QSpinBox(); self.cpus.setRange(1, 128); self.cpus.setValue(1)
            self.mem = QLineEdit("8G")
            self.python = QLineEdit(controller.prefs.python_executable)
            self.modules = QLineEdit("python/3.11")
            self.modules.setPlaceholderText("space-separated module names")
            for label, w in (
                ("Backend", self.backend),
                ("Job name", self.job_name),
                ("Partition", self.partition),
                ("Account", self.account),
                ("Time", self.time),
                ("ntasks", self.ntasks),
                ("cpus-per-task", self.cpus),
                ("Memory", self.mem),
                ("Python", self.python),
                ("Modules", self.modules),
            ):
                form.addRow(label, w)
            layout.addLayout(form)

            self.preview = QTextEdit()
            self.preview.setReadOnly(True)
            self.preview.setFontFamily("Consolas")
            layout.addWidget(self.preview)

            row = QHBoxLayout()
            btn_preview = QPushButton("Preview sbatch")
            btn_export = QPushButton("Export sbatch + scripts…")
            btn_preview.clicked.connect(self._preview)
            btn_export.clicked.connect(self._export)
            row.addWidget(btn_preview)
            row.addWidget(btn_export)
            layout.addLayout(row)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
            layout.addWidget(buttons)
            self._preview()

        def _modules_tuple(self) -> tuple:
            parts = [m.strip() for m in self.modules.text().split() if m.strip()]
            return tuple(parts) if parts else ("python/3.11",)

        def _sbatch_text(self) -> str:
            return render_sbatch(
                self.controller.project,
                job_name=self.job_name.text().strip() or None,
                partition=self.partition.text().strip() or "cpu",
                account=self.account.text().strip() or None,
                time=self.time.text().strip() or "04:00:00",
                ntasks=self.ntasks.value(),
                cpus_per_task=self.cpus.value(),
                mem=self.mem.text().strip() or "8G",
                module_load=self._modules_tuple(),
                python=self.python.text().strip() or "python",
            )

        def _preview(self) -> None:
            pipe = Pipeline.standard(
                dt=self.controller.prefs.dt,
                nb_steps=self.controller.prefs.nb_steps,
                backend=self.backend.currentText(),  # type: ignore[arg-type]
            )
            text = "# Pipeline steps:\n"
            for s in pipe.steps:
                text += f"#  - {s.name} {s.params}\n"
            text += "\n" + self._sbatch_text()
            self.preview.setPlainText(text)

        def _export(self) -> None:
            path = QFileDialog.getExistingDirectory(self, "Export directory")
            if not path:
                return
            out = Path(path)
            try:
                # scripts with current prefs
                self.controller.prepare_run_directory(out)
                sbatch_path = out / "run.sbatch"
                sbatch_path.write_text(self._sbatch_text(), encoding="utf-8")
                pipe = Pipeline.standard(
                    dt=self.controller.prefs.dt,
                    nb_steps=self.controller.prefs.nb_steps,
                    backend=self.backend.currentText(),  # type: ignore[arg-type]
                )
                (out / "pipeline.json").write_text(
                    __import__("json").dumps(pipe.to_dict(), indent=2), encoding="utf-8",
                )
                self.controller.journal.info(f"Pipeline exported to {out}")
                QMessageBox.information(
                    self, "Pipeline",
                    f"Written:\n  pre.py\n  command.py\n  run.sbatch\n  pipeline.json\n→ {out}",
                )
            except Exception as exc:
                self.controller.journal.exception("pipeline export", exc)
                QMessageBox.critical(self, "Pipeline", str(exc))

    return PipelineDialog(controller, parent)
