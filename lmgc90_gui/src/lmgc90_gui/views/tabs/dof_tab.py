"""DOFTab — QTreeWidget CRUD for DOF operations."""
from __future__ import annotations

from lmgc90_core import DOFOperation, ValidationError, pre

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree


def create_dof_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
        QPushButton, QVBoxLayout, QWidget,
    )

    class DOFTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_index: int | None = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Conditions aux limites / DOF — sélectionnez pour modifier"))
            self.tree = create_entity_tree(
                ["#", "Law", "Target", "Value", "Params"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)
            form = QFormLayout()
            self.law_edit = QLineEdit("imposedDrivenDof")
            self.target_type = QComboBox()
            self.target_type.addItems(["avatar", "group", "color"])
            self.target_value = QLineEdit()
            self.params_edit = QLineEdit("component=[1], dofty='vlocy', ct=0.0")
            form.addRow("Law", self.law_edit)
            form.addRow("Target type", self.target_type)
            form.addRow("Target value", self.target_value)
            form.addRow("Params", self.params_edit)
            layout.addLayout(form)
            row = QHBoxLayout()
            for text, slot in (
                ("➕ Add", self._on_add), ("💾 Update", self._on_update),
                ("🗑️ Delete", self._on_remove), ("Clear form", self._clear_form),
            ):
                b = QPushButton(text); b.clicked.connect(slot); row.addWidget(b)
            layout.addLayout(row)

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            sel = self.tree.selected_payload()
            self.tree.clear_rows()
            for i, op in enumerate(self.controller.project.operations):
                params = ", ".join(f"{k}={v}" for k, v in (op.parameters or {}).items())
                self.tree.add_row(
                    [str(i), op.operation_type, f"{op.target_type}:{op.target_value}",
                     str(getattr(op, "value", "")), params[:40]],
                    i,
                )
            self.tree.resize_columns()
            if sel is not None:
                self.tree.select_payload(sel)

        def _load_selected(self, index: int) -> None:
            ops = self.controller.project.operations
            if not (0 <= index < len(ops)):
                return
            op = ops[index]
            self._editing_index = index
            self.law_edit.setText(op.operation_type)
            i = self.target_type.findText(op.target_type)
            if i >= 0:
                self.target_type.setCurrentIndex(i)
            self.target_value.setText(str(op.target_value))
            self.params_edit.setText(
                ", ".join(f"{k}={v!r}" if isinstance(v, str) else f"{k}={v}"
                          for k, v in (op.parameters or {}).items())
            )

        def _clear_form(self) -> None:
            self._editing_index = None
            self.tree.clearSelection()

        def _build(self) -> DOFOperation:
            params = self.eval_dict(self.params_edit.text(), "DOF params")
            return DOFOperation(
                operation_type=self.law_edit.text().strip(),
                target_type=self.target_type.currentText(),
                target_value=self.target_value.text().strip(),
                parameters=params,
            )

        def _on_add(self) -> None:
            try:
                self.controller.add_dof(self._build())
                self._clear_form()
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "DOF", str(e))

        def _on_update(self) -> None:
            if self._editing_index is None:
                QMessageBox.information(self, "DOF", "Sélectionnez une opération")
                return
            try:
                self.controller.update_dof(self._editing_index, self._build())
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "DOF", str(e))

        def _on_remove(self) -> None:
            idx = self.tree.selected_payload()
            if idx is None:
                idx = self._editing_index
            if idx is not None:
                self.controller.remove_dof(int(idx))
                self._clear_form()

    return DOFTab(parent)
