"""VisibilityTab — see tables as QTreeWidget CRUD."""
from __future__ import annotations

from lmgc90_core import ValidationError, VisibilityRule, pre

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree


def create_visibility_tab(parent=None):
    from PyQt6.QtWidgets import (
        QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
        QPushButton, QVBoxLayout, QWidget, QDoubleSpinBox,
    )

    class VisibilityTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_index: int | None = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("See tables — sélectionnez pour modifier"))
            self.tree = create_entity_tree(
                ["#", "Cand body", "Cand shape", "Cand color", "Ant body", "Ant shape", "Ant color", "Law", "Alert"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)
            form = QFormLayout()
            self.c_body = QLineEdit("RBDY2")
            self.c_shape = QLineEdit("DISKx")
            self.c_color = QLineEdit("BLUEx")
            self.a_body = QLineEdit("RBDY2")
            self.a_shape = QLineEdit("DISKx")
            self.a_color = QLineEdit("BLUEx")
            self.behav = QLineEdit("IQS")
            self.alert = QDoubleSpinBox(); self.alert.setRange(0, 1e3); self.alert.setDecimals(6); self.alert.setValue(0.02)
            for lab, w in (
                ("Corps candidat", self.c_body), ("Shape candidat", self.c_shape),
                ("Color candidat", self.c_color), ("Corps antagoniste", self.a_body),
                ("Shape antagoniste", self.a_shape), ("Color antagoniste", self.a_color),
                ("Law (behav)", self.behav), ("Alert", self.alert),
            ):
                form.addRow(lab, w)
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
            for i, r in enumerate(self.controller.project.visibility):
                self.tree.add_row(
                    [str(i), r.candidate_body, r.candidate_contactor, r.candidate_color,
                     r.antagonist_body, r.antagonist_contactor, r.antagonist_color,
                     r.behavior_name, str(r.alert)],
                    i,
                )
            self.tree.resize_columns()
            if sel is not None:
                self.tree.select_payload(sel)

        def _load_selected(self, index: int) -> None:
            if self.controller is None:
                return
            if not (0 <= index < len(self.controller.project.visibility)):
                return
            r = self.controller.project.visibility[index]
            self._editing_index = index
            self.c_body.setText(r.candidate_body)
            self.c_shape.setText(r.candidate_contactor)
            self.c_color.setText(r.candidate_color)
            self.a_body.setText(r.antagonist_body)
            self.a_shape.setText(r.antagonist_contactor)
            self.a_color.setText(r.antagonist_color)
            self.behav.setText(r.behavior_name)
            self.alert.setValue(float(r.alert))

        def _clear_form(self) -> None:
            self._editing_index = None
            self.tree.clearSelection()

        def _build(self) -> VisibilityRule:
            return pre.see_table(
                CorpsCandidat=self.c_body.text().strip(),
                candidat=self.c_shape.text().strip(),
                colorCandidat=self.c_color.text().strip(),
                CorpsAntagoniste=self.a_body.text().strip(),
                antagoniste=self.a_shape.text().strip(),
                colorAntagoniste=self.a_color.text().strip(),
                behav=self.behav.text().strip(),
                alert=self.alert.value(),
            )

        def _on_add(self) -> None:
            try:
                self.controller.add_visibility(self._build())
                self._clear_form()
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "Visibility", str(e))

        def _on_update(self) -> None:
            if self._editing_index is None:
                QMessageBox.information(self, "Visibility", "Sélectionnez une ligne")
                return
            try:
                self.controller.update_visibility(self._editing_index, self._build())
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "Visibility", str(e))

        def _on_remove(self) -> None:
            idx = self.tree.selected_payload()
            if idx is None:
                idx = self._editing_index
            if idx is not None:
                self.controller.remove_visibility(int(idx))
                self._clear_form()

    return VisibilityTab(parent)
