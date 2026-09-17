"""VisibilityTab — see tables as QTreeWidget CRUD.

Corps candidat / antagoniste : combobox selon la dimension du projet
  2D → RBDY2, MAILx, MBS2D
  3D → RBDY3, MAILx, MBS3D
  (+ toutes les valeurs pour compat. import)
"""
from __future__ import annotations

from lmgc90_core import ValidationError, VisibilityRule, pre

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree

# LMGC90 body-type codes (see tables)
_BODY_2D = ("RBDY2", "MAILx", "MBS2D")
_BODY_3D = ("RBDY3", "MAILx", "MBS3D")
_BODY_ALL = ("RBDY2", "RBDY3", "MAILx", "MBS2D", "MBS3D")


def create_visibility_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
        QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class VisibilityTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_index: int | None = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "See tables — Corps candidat / antagoniste selon la dimension "
                "(RBDY2/MBS2D en 2D, RBDY3/MBS3D en 3D, MAILx toujours)"
            ))
            self.tree = create_entity_tree(
                ["#", "Cand body", "Cand shape", "Cand color",
                 "Ant body", "Ant shape", "Ant color", "Law", "Alert"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)

            form = QFormLayout()
            self.c_body = QComboBox()
            self.c_body.setEditable(False)
            self.a_body = QComboBox()
            self.a_body.setEditable(False)
            self._refill_body_combos(default_dim=2)

            self.c_shape = QLineEdit("DISKx")
            self.c_color = QLineEdit("BLUEx")
            self.a_shape = QLineEdit("DISKx")
            self.a_color = QLineEdit("BLUEx")
            self.behav = QLineEdit("IQS")
            self.alert = QDoubleSpinBox()
            self.alert.setRange(0, 1e3)
            self.alert.setDecimals(6)
            self.alert.setValue(0.02)

            for lab, w in (
                ("Corps candidat", self.c_body),
                ("Shape candidat", self.c_shape),
                ("Color candidat", self.c_color),
                ("Corps antagoniste", self.a_body),
                ("Shape antagoniste", self.a_shape),
                ("Color antagoniste", self.a_color),
                ("Law (behav)", self.behav),
                ("Alert", self.alert),
            ):
                form.addRow(lab, w)
            layout.addLayout(form)

            row = QHBoxLayout()
            for text, slot in (
                ("➕ Add", self._on_add),
                ("💾 Update", self._on_update),
                ("🗑️ Delete", self._on_remove),
                ("Clear form", self._clear_form),
            ):
                b = QPushButton(text)
                b.clicked.connect(slot)
                row.addWidget(b)
            layout.addLayout(row)

        # ------------------------------------------------------------------ helpers
        def _project_dim(self) -> int:
            if self.controller is None:
                return 2
            return int(getattr(self.controller.project, "dimension", 2) or 2)

        def _body_choices(self, dim: int | None = None) -> tuple[str, ...]:
            d = self._project_dim() if dim is None else int(dim)
            return _BODY_2D if d == 2 else _BODY_3D

        def _default_body(self, dim: int | None = None) -> str:
            d = self._project_dim() if dim is None else int(dim)
            return "RBDY2" if d == 2 else "RBDY3"

        def _refill_body_combos(self, default_dim: int | None = None) -> None:
            choices = list(self._body_choices(default_dim))
            # Keep full list available but prefer dimension defaults at top
            for extra in _BODY_ALL:
                if extra not in choices:
                    choices.append(extra)
            default = self._default_body(default_dim)
            for combo in (self.c_body, self.a_body):
                current = combo.currentText() if combo.count() else default
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(choices)
                # restore selection if still valid, else default
                idx = combo.findText(current)
                if idx < 0:
                    idx = combo.findText(default)
                combo.setCurrentIndex(max(0, idx))
                combo.blockSignals(False)

        def _set_combo(self, combo, value: str) -> None:
            value = (value or "").strip()
            if not value:
                return
            idx = combo.findText(value)
            if idx < 0:
                # value from file not in list → insert once
                combo.addItem(value)
                idx = combo.findText(value)
            combo.setCurrentIndex(idx)

        def _body_text(self, combo) -> str:
            return combo.currentText().strip()

        # ------------------------------------------------------------------ state
        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            self._refill_body_combos()
            sel = self.tree.selected_payload()
            self.tree.clear_rows()
            for i, r in enumerate(self.controller.project.visibility):
                self.tree.add_row(
                    [str(i), r.candidate_body, r.candidate_contactor, r.candidate_color,
                     r.antagonist_body, r.antagonist_contactor, r.antagonist_color,
                     r.behavior_name, f"{r.alert:g}"],
                    payload=i,
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
            self._set_combo(self.c_body, r.candidate_body)
            self.c_shape.setText(r.candidate_contactor)
            self.c_color.setText(r.candidate_color)
            self._set_combo(self.a_body, r.antagonist_body)
            self.a_shape.setText(r.antagonist_contactor)
            self.a_color.setText(r.antagonist_color)
            self.behav.setText(r.behavior_name)
            self.alert.setValue(float(r.alert))

        def _clear_form(self) -> None:
            self._editing_index = None
            self.tree.clearSelection()
            d = self._default_body()
            self._set_combo(self.c_body, d)
            self._set_combo(self.a_body, d)

        def _build(self) -> VisibilityRule:
            return pre.see_table(
                CorpsCandidat=self._body_text(self.c_body),
                candidat=self.c_shape.text().strip(),
                colorCandidat=self.c_color.text().strip(),
                CorpsAntagoniste=self._body_text(self.a_body),
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
