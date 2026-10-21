"""LoopTab — geometric loops (circle / grid / line / spiral) from a template avatar."""
from __future__ import annotations

from lmgc90_core import Loop, ValidationError
from lmgc90_core.types import LOOP_ALIASES

from .base_tab import BaseTab
from ...utils.naming import suggest_group_name

_KINDS = ("circle", "grid", "line", "spiral")


def create_loop_tab(parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QFormLayout, QHBoxLayout,
        QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
        QVBoxLayout, QWidget,
    )
    from PyQt6.QtCore import Qt

    class LoopTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.list = QListWidget()
            layout.addWidget(self.list)
            self.list.currentItemChanged.connect(self._update_remove_button)

            form = QFormLayout()
            self.kind_combo = QComboBox()
            self.kind_combo.addItems(_KINDS)
            self.template_combo = QComboBox()
            self.count_spin = QLineEdit("8")
            self.radius_spin = QLineEdit("0.5")
            self.step_spin = QLineEdit("0.2")
            self.ox = QLineEdit("0"); self.oy = QLineEdit("0"); self.oz = QLineEdit("0")
            self.spiral = QLineEdit("0.1")
            for field in (
                self.count_spin, self.radius_spin, self.step_spin, self.ox,
                self.oy, self.oz, self.spiral,
            ):
                field.setPlaceholderText("nombre ou expression")
                self.mark_expr_field(field)
            self.invert = QCheckBox("Invert axis (line)")
            self.group_edit = QLineEdit()
            self.group_edit.setPlaceholderText("optional group name")
            # default filled on state change

            form.addRow("Type", self.kind_combo)
            form.addRow("Template avatar", self.template_combo)
            form.addRow("Count", self.count_spin)
            form.addRow("Radius (circle/spiral)", self.radius_spin)
            form.addRow("Step (grid/line)", self.step_spin)
            form.addRow("Offset X", self.ox)
            form.addRow("Offset Y", self.oy)
            form.addRow("Offset Z", self.oz)
            form.addRow("Spiral factor", self.spiral)
            form.addRow("", self.invert)
            form.addRow("Group", self.group_edit)
            layout.addLayout(form)
            layout.addWidget(QLabel(
                "Each generated body is an individual Avatar (AoS), cloned from the template."
            ))

            row = QHBoxLayout()
            btn_run = QPushButton("Apply loop")
            btn_run.clicked.connect(self._on_apply)
            row.addWidget(btn_run)
            self.btn_remove = QPushButton("Delete selected loop")
            self.btn_remove.setEnabled(False)
            self.btn_remove.clicked.connect(self._on_remove)
            row.addWidget(self.btn_remove)
            layout.addLayout(row)

        def _update_remove_button(self, current, _previous) -> None:
            self.btn_remove.setEnabled(current is not None)

        def _suggest_group(self) -> None:
            if self.controller is None:
                return
            existing = list(self.controller.project.avatar_groups.keys())
            suggested = suggest_group_name("loop", existing)
            cur = self.group_edit.text().strip()
            if not cur or getattr(self, "_last_auto_group", "") == cur:
                self.group_edit.setText(suggested)
                self._last_auto_group = suggested

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.list.clear()
            for lp in p.loops:
                item = QListWidgetItem(
                    f"{lp.loop_type}  n={lp.count}  template={lp.model_avatar_id[:8]}…  "
                    f"generated={len(lp.generated_ids)}  group={lp.group_name or '—'}"
                )
                item.setData(Qt.ItemDataRole.UserRole, lp.loop_id)
                self.list.addItem(item)
            self._update_remove_button(self.list.currentItem(), None)
            cur = self.template_combo.currentData()
            self.template_combo.clear()
            for a in p.avatars:
                self.template_combo.addItem(
                    f"{a.avatar_id[:8]}… {a.avatar_type.value} r={a.radius}",
                    a.avatar_id,
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
                QMessageBox.warning(self, "Loop", "Select a template avatar first")
                return
            kind = self.kind_combo.currentText()
            try:
                loop = Loop(
                    loop_type=kind,
                    model_avatar_id=tid,
                    count=self.eval_int(self.count_spin.text(), 8, "count"),
                    radius=self.eval_float(self.radius_spin.text(), 0.5, "radius"),
                    step=self.eval_float(self.step_spin.text(), 0.2, "step"),
                    offset_x=self.eval_float(self.ox.text(), 0.0, "offset X"),
                    offset_y=self.eval_float(self.oy.text(), 0.0, "offset Y"),
                    offset_z=self.eval_float(self.oz.text(), 0.0, "offset Z"),
                    spiral_factor=self.eval_float(self.spiral.text(), 0.1, "spiral factor"),
                    invert_axis=self.invert.isChecked(),
                    group_name=self.group_edit.text().strip() or None,
                )
                generated = self.controller.apply_loop(loop)
                QMessageBox.information(
                    self, "Loop",
                    f"Created {len(generated)} avatars ({kind})",
                )
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Loop", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            item = self.list.currentItem()
            if item is None:
                return
            loop_id = item.data(Qt.ItemDataRole.UserRole)
            answer = QMessageBox.question(
                self,
                "Delete loop",
                "Delete this loop and all avatars generated by it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                self.controller.remove_loop(loop_id)
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Loop", str(exc))

    return LoopTab(parent)
