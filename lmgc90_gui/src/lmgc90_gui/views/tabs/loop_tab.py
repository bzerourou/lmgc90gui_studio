"""LoopTab — geometric loops (circle / grid / line / spiral) from a template avatar."""
from __future__ import annotations

from lmgc90_core import Loop, ValidationError
from lmgc90_core.types import LOOP_ALIASES

from .base_tab import BaseTab
from ...utils.naming import suggest_group_name

_KINDS = ("circle", "grid", "line", "spiral")


def create_loop_tab(parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
        QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox,
        QVBoxLayout, QWidget,
    )

    class LoopTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.kind_combo = QComboBox()
            self.kind_combo.addItems(_KINDS)
            self.template_combo = QComboBox()
            self.count_spin = QSpinBox()
            self.count_spin.setRange(1, 100_000)
            self.count_spin.setValue(8)
            self.radius_spin = QDoubleSpinBox()
            self.radius_spin.setRange(0.0, 1e6)
            self.radius_spin.setValue(0.5)
            self.radius_spin.setDecimals(4)
            self.step_spin = QDoubleSpinBox()
            self.step_spin.setRange(0.0, 1e6)
            self.step_spin.setValue(0.2)
            self.step_spin.setDecimals(4)
            self.ox = QDoubleSpinBox(); self.oy = QDoubleSpinBox(); self.oz = QDoubleSpinBox()
            for s in (self.ox, self.oy, self.oz):
                s.setRange(-1e6, 1e6)
                s.setDecimals(4)
            self.spiral = QDoubleSpinBox()
            self.spiral.setRange(0.0, 10.0)
            self.spiral.setValue(0.1)
            self.spiral.setDecimals(4)
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
            layout.addLayout(row)

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
                self.list.addItem(
                    f"{lp.loop_type}  n={lp.count}  template={lp.model_avatar_id[:8]}…  "
                    f"generated={len(lp.generated_ids)}  group={lp.group_name or '—'}"
                )
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
            loop = Loop(
                loop_type=kind,
                model_avatar_id=tid,
                count=self.count_spin.value(),
                radius=self.radius_spin.value(),
                step=self.step_spin.value(),
                offset_x=self.ox.value(),
                offset_y=self.oy.value(),
                offset_z=self.oz.value(),
                spiral_factor=self.spiral.value(),
                invert_axis=self.invert.isChecked(),
                group_name=self.group_edit.text().strip() or None,
            )
            try:
                generated = self.controller.apply_loop(loop)
                QMessageBox.information(
                    self, "Loop",
                    f"Created {len(generated)} avatars ({kind})",
                )
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Loop", str(exc))

    return LoopTab(parent)
