"""DynamicVarsDialog — manage project.dynamic_vars (name → expression)."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_dynamic_vars_dialog(controller: "ProjectController", parent=None):
    from PyQt6.QtWidgets import (
        QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
        QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
        QVBoxLayout,
    )
    from ..utils.eval_context import build_eval_context, resolve_dynamic_vars
    from ..utils.safe_eval import safe_eval

    class DynamicVarsDialog(QDialog):
        def __init__(self, controller: "ProjectController", parent=None):
            super().__init__(parent)
            self.controller = controller
            self.setWindowTitle("Variables dynamiques")
            self.resize(720, 480)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "Expressions Python sûres, évaluées dans l'ordre. "
                "Utilisables dans les champs numériques des onglets."
            ))

            form = QFormLayout()
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText("thickness, r_min, wall_width…")
            self.expr_edit = QLineEdit()
            self.expr_edit.setPlaceholderText("0.05  ou  lx + joint  ou  avatar[0].radius")
            self.preview = QLabel("—")
            form.addRow("Nom", self.name_edit)
            form.addRow("Expression", self.expr_edit)
            form.addRow("Aperçu", self.preview)
            layout.addLayout(form)
            self.expr_edit.textChanged.connect(self._preview)
            self.name_edit.textChanged.connect(self._preview)

            row = QHBoxLayout()
            btn_add = QPushButton("Add / Update")
            btn_del = QPushButton("Delete")
            btn_ref = QPushButton("Refresh")
            btn_add.clicked.connect(self._on_add)
            btn_del.clicked.connect(self._on_del)
            btn_ref.clicked.connect(self._refresh_table)
            row.addWidget(btn_add)
            row.addWidget(btn_del)
            row.addWidget(btn_ref)
            layout.addLayout(row)

            self.table = QTableWidget(0, 4)
            self.table.setHorizontalHeaderLabels(["Name", "Expression", "Value", "Type"])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.cellClicked.connect(self._on_row)
            layout.addWidget(self.table)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
            layout.addWidget(buttons)
            self._refresh_table()

        def _preview(self, *_a):
            expr = self.expr_edit.text().strip()
            if not expr:
                self.preview.setText("—")
                self.preview.setStyleSheet("")
                return
            try:
                ctx = build_eval_context(self.controller.project)
                # include pending name → try without self if defining
                val = safe_eval(expr, ctx)
                self.preview.setText(repr(val))
                self.preview.setStyleSheet("color: green;")
            except Exception as exc:
                self.preview.setText(str(exc))
                self.preview.setStyleSheet("color: red;")

        def _refresh_table(self):
            p = self.controller.project
            resolved = resolve_dynamic_vars(p)
            self.table.setRowCount(0)
            for name, expr in p.dynamic_vars.items():
                row = self.table.rowCount()
                self.table.insertRow(row)
                val = resolved.get(name, "?")
                self.table.setItem(row, 0, QTableWidgetItem(str(name)))
                self.table.setItem(row, 1, QTableWidgetItem(str(expr)))
                self.table.setItem(row, 2, QTableWidgetItem(repr(val)))
                self.table.setItem(row, 3, QTableWidgetItem(type(val).__name__))
            self._preview()

        def _on_row(self, row: int, _col: int):
            self.name_edit.setText(self.table.item(row, 0).text())
            self.expr_edit.setText(self.table.item(row, 1).text())

        def _on_add(self):
            name = self.name_edit.text().strip()
            expr = self.expr_edit.text().strip()
            if not name.isidentifier():
                QMessageBox.warning(self, "Variables", "Nom d'identifiant Python requis")
                return
            if not expr:
                QMessageBox.warning(self, "Variables", "Expression requise")
                return
            # validate
            try:
                ctx = build_eval_context(self.controller.project)
                safe_eval(expr, ctx)
            except Exception as exc:
                QMessageBox.warning(self, "Variables", f"Expression invalide :\n{exc}")
                return
            self.controller.set_dynamic_var(name, expr)
            self._refresh_table()

        def _on_del(self):
            name = self.name_edit.text().strip()
            if not name:
                row = self.table.currentRow()
                if row >= 0:
                    name = self.table.item(row, 0).text()
            if name:
                self.controller.remove_dynamic_var(name)
                self.name_edit.clear()
                self.expr_edit.clear()
                self._refresh_table()

    return DynamicVarsDialog(controller, parent)
