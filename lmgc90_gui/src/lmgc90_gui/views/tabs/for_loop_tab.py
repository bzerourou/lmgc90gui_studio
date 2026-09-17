"""ForLoopTab — generic parametric loop with safe arithmetic expressions."""
from __future__ import annotations

from lmgc90_core import ForLoop, ValidationError

from .base_tab import BaseTab
from ...utils.naming import suggest_group_name


def create_for_loop_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
        QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class ForLoopTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.var_edit = QLineEdit("i")
            self.start = QDoubleSpinBox(); self.stop = QDoubleSpinBox(); self.step = QDoubleSpinBox()
            for s, v in ((self.start, 0.0), (self.stop, 8.0), (self.step, 1.0)):
                s.setRange(-1e9, 1e9); s.setDecimals(6); s.setValue(v)
            self.template_combo = QComboBox()
            self.expr_x = QLineEdit("i * 0.15")
            self.expr_y = QLineEdit("0.2")
            self.expr_z = QLineEdit("0.0")
            self.expr_r = QLineEdit("")
            self.expr_r.setPlaceholderText("optional — leave empty to keep template radius")
            self.group_edit = QLineEdit()
            form.addRow("Variable", self.var_edit)
            form.addRow("Start", self.start)
            form.addRow("Stop (exclusive)", self.stop)
            form.addRow("Step", self.step)
            form.addRow("Template avatar", self.template_combo)
            form.addRow("expr center X", self.expr_x)
            form.addRow("expr center Y", self.expr_y)
            form.addRow("expr center Z", self.expr_z)
            form.addRow("expr radius", self.expr_r)
            form.addRow("Group", self.group_edit)
            layout.addLayout(form)
            layout.addWidget(QLabel(
                "Expressions may use the variable, pi, sin, cos, sqrt, abs.\n"
                "Example: X = 0.5*cos(i*pi/8)  Y = 0.5*sin(i*pi/8)"
            ))

            row = QHBoxLayout()
            btn = QPushButton("Apply ForLoop")
            btn.clicked.connect(self._on_apply)
            row.addWidget(btn)
            layout.addLayout(row)

        def _suggest_group(self) -> None:
            if self.controller is None:
                return
            existing = list(self.controller.project.avatar_groups.keys())
            suggested = suggest_group_name("for_loop", existing)
            cur = self.group_edit.text().strip()
            if not cur or getattr(self, "_last_auto_group", "") == cur:
                self.group_edit.setText(suggested)
                self._last_auto_group = suggested

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.list.clear()
            for fl in getattr(p, "for_loops", []):
                self.list.addItem(
                    f"{fl.var_name}=[{fl.start}:{fl.stop}:{fl.step}]  "
                    f"n≈{len(fl.generated_ids)}  template={fl.model_avatar_id[:8]}…"
                )
            cur = self.template_combo.currentData()
            self.template_combo.clear()
            for a in p.avatars:
                self.template_combo.addItem(
                    f"{a.avatar_id[:8]}… {a.avatar_type.value}", a.avatar_id,
                )
            if cur is not None:
                idx = self.template_combo.findData(cur)
                if idx >= 0:
                    self.template_combo.setCurrentIndex(idx)
            self._suggest_group()

        def _on_apply(self) -> None:
            if self.controller is None:
                return
            tid = self.template_combo.currentData()
            if not tid:
                QMessageBox.warning(self, "ForLoop", "Select a template avatar")
                return
            fl = ForLoop(
                var_name=self.var_edit.text().strip() or "i",
                start=self.start.value(),
                stop=self.stop.value(),
                step=self.step.value(),
                model_avatar_id=tid,
                expr_x=self.expr_x.text().strip() or "0",
                expr_y=self.expr_y.text().strip() or "0",
                expr_z=self.expr_z.text().strip() or "0",
                expr_radius=(self.expr_r.text().strip() or None),
                group_name=self.group_edit.text().strip() or None,
            )
            try:
                generated = self.controller.apply_for_loop(fl)
                QMessageBox.information(self, "ForLoop", f"Created {len(generated)} avatars")
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "ForLoop", str(exc))

    return ForLoopTab(parent)
