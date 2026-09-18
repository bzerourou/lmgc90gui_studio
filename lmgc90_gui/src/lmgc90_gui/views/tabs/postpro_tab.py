"""PostProTab — post-processing commands."""
from __future__ import annotations

from lmgc90_core import PostProCommand, ValidationError

from .base_tab import BaseTab

_COMMON = (
    "SOLVER INFORMATIONS",
    "BODY TRACKING",
    "TORQUE EVOLUTION",
    "KINETIC ENERGY",
    "COORDINATE",
    "VAN_DER_WAALS",
)


def create_postpro_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QListWidget, QMessageBox,
        QPushButton, QSpinBox, QVBoxLayout, QWidget,
    )

    class PostProTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.name_combo = QComboBox()
            self.name_combo.setEditable(True)
            self.name_combo.addItems(_COMMON)
            self.step_spin = QSpinBox()
            self.step_spin.setRange(1, 1_000_000)
            self.step_spin.setValue(1)
            self.target_type = QComboBox()
            self.target_type.addItems(["global", "avatar", "group"])
            self.target_value = QComboBox()
            self.target_value.setEditable(True)
            form.addRow("Command", self.name_combo)
            form.addRow("Step", self.step_spin)
            form.addRow("Target type", self.target_type)
            form.addRow("Target", self.target_value)
            layout.addLayout(form)

            self.target_type.currentTextChanged.connect(self._refresh_targets)

            row = QHBoxLayout()
            btn_add = QPushButton("Add")
            btn_rm = QPushButton("Remove")
            btn_add.clicked.connect(self._on_add)
            btn_rm.clicked.connect(self._on_remove)
            row.addWidget(btn_add)
            row.addWidget(btn_rm)
            layout.addLayout(row)

        def _refresh_targets(self, *_a) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.target_value.clear()
            tt = self.target_type.currentText()
            if tt == "avatar":
                for a in p.avatars:
                    self.target_value.addItem(f"{a.avatar_id[:12]}…|{a.avatar_type.value}")
            elif tt == "group":
                self.target_value.addItems(list(p.avatar_groups.keys()))

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            self.list.clear()
            for i, cmd in enumerate(self.controller.project.postpro):
                tgt = ""
                if cmd.target_type != "global" and cmd.target_value is not None:
                    tgt = f"  {cmd.target_type}={cmd.target_value}"
                self.list.addItem(f"[{i}] {cmd.name}  step={cmd.step}{tgt}")
            self._refresh_targets()

        def _on_add(self) -> None:
            if self.controller is None:
                return
            tt = self.target_type.currentText()
            data = self.target_value.currentData()
            tv = data if data is not None else (self.target_value.currentText().strip() or None)
            if tt == "global":
                tv = None
            try:
                cmd = PostProCommand(
                    name=self.name_combo.currentText().strip(),
                    step=self.step_spin.value(),
                    target_type=tt,
                    target_value=tv,
                )
                self.controller.add_postpro(cmd)
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Post-pro", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            row = self.list.currentRow()
            if row < 0:
                return
            self.controller.remove_postpro(row)

    return PostProTab(parent)
