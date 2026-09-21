"""DOFTab — QTreeWidget CRUD for DOF / kinematic operations.

- Law: combobox (rotate, translate, imposeDrivenDof, imposeInitValue)
- Target type: avatar | group | color
- Target value: combobox auto-filled from project (avatars / groups / colors)
"""
from __future__ import annotations

import ast
import re
from typing import Any

from lmgc90_core import DOFOperation, ValidationError

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree

_LAWS = (
    "imposeDrivenDof",
    "imposeInitValue",
    "translate",
    "rotate",
)

_DEFAULT_PARAMS = {
    "imposeDrivenDof": "component=[1, 2, 3], dofty='vlocy', ct=0.0",
    "imposeInitValue": "component=[1, 2, 3], dofty='vlocy', values=[0.0, 0.0, 0.0]",
    "translate": "dx=0.0, dy=0.0, dz=0.0",
    "rotate": "description='axis', axis=[0, 0, 1], alpha=0.0",
}


def _parse_params(text: str) -> dict[str, Any]:
    """Parse ``key=val, key=val`` into a dict (safe-ish literals)."""
    text = (text or "").strip()
    if not text:
        return {}
    # Wrap as dict literal
    try:
        # allow single quotes
        expr = "{" + text + "}"
        expr = expr.replace("'", '"') if False else expr
        # Use ast on a fake call kwargs form: f(component=[1], dofty='vlocy')
        fake = f"f({text})"
        tree = ast.parse(fake, mode="eval")
        if not isinstance(tree.body, ast.Call):
            raise ValueError("expected key=value list")
        out: dict[str, Any] = {}
        for kw in tree.body.keywords:
            if kw.arg is None:
                continue
            out[kw.arg] = ast.literal_eval(kw.value)
        return out
    except Exception:
        # fallback: simple split
        out = {}
        for part in re.split(r",(?![^\[]*\])", text):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            k, v = k.strip(), v.strip()
            try:
                out[k] = ast.literal_eval(v)
            except Exception:
                out[k] = v.strip("'\"")
        return out


def _format_params(params: dict[str, Any] | None) -> str:
    if not params:
        return ""
    parts = []
    for k, v in params.items():
        parts.append(f"{k}={v!r}")
    return ", ".join(parts)


def create_dof_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
        QPushButton, QVBoxLayout, QWidget,
    )

    class DOFTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_index: int | None = None
            self._suppress_law_default = False

            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "Conditions aux limites / DOF — sélectionnez pour modifier. "
                "Target value se remplit selon target type (avatars, groupes, couleurs)."
            ))
            self.tree = create_entity_tree(
                ["#", "Law", "Target type", "Target value", "Params"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)

            form = QFormLayout()
            self.law_combo = QComboBox()
            self.law_combo.addItems(list(_LAWS))
            self.law_combo.currentTextChanged.connect(self._on_law_changed)

            self.target_type = QComboBox()
            self.target_type.addItems(["avatar", "group", "color"])
            self.target_type.currentTextChanged.connect(self._refill_target_values)

            self.target_value = QComboBox()
            self.target_value.setEditable(True)  # allow paste id not yet listed
            self.target_value.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

            self.params_edit = QLineEdit(_DEFAULT_PARAMS["imposeDrivenDof"])
            self.params_edit.setPlaceholderText("component=[1], dofty='vlocy', ct=0.0")

            form.addRow("Law", self.law_combo)
            form.addRow("Target type", self.target_type)
            form.addRow("Target value", self.target_value)
            form.addRow("Params", self.params_edit)
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

        # ------------------------------------------------------------------ fill target value
        def _avatar_choices(self) -> list[str]:
            if self.controller is None:
                return []
            items = []
            for av in self.controller.project.avatars:
                label = f"{av.avatar_id[:12]}… | ({av.avatar_type.value})"
                items.append((av.avatar_id, label))
            return items  # type: ignore[return-value]

        def _group_choices(self) -> list[str]:
            if self.controller is None:
                return []
            groups = getattr(self.controller.project, "avatar_groups", None) or {}
            return sorted(groups.keys())

        def _color_choices(self) -> list[str]:
            if self.controller is None:
                return []
            colors = set()
            for av in self.controller.project.avatars:
                if av.color:
                    colors.add(av.color)
            for pop in self.controller.project.populations:
                if getattr(pop, "color", None):
                    colors.add(pop.color)
            # common LMGC defaults
            for c in ("BLUEx", "REEDx", "GRAYx", "CYANx", "GREENx", "YELLO", "ORANG", "WHITEx"):
                colors.add(c)
            return sorted(colors)

        def _refill_target_values(self, *_args) -> None:
            ttype = self.target_type.currentText().strip()
            prev = self.target_value.currentText().strip()
            self.target_value.blockSignals(True)
            self.target_value.clear()

            if ttype == "avatar":
                pairs = []
                if self.controller is not None:
                    for av in self.controller.project.avatars:
                        short = av.avatar_id[:12]
                        pairs.append((av.avatar_id, f"{short}… | {av.avatar_type.value}"))
                if not pairs:
                    self.target_value.addItem("(aucun avatar)", "")
                else:
                    for aid, label in pairs:
                        self.target_value.addItem(label, aid)
            elif ttype == "group":
                names = self._group_choices()
                if not names:
                    self.target_value.addItem("(aucun groupe)", "")
                else:
                    for g in names:
                        self.target_value.addItem(g, g)
            else:  # color
                for c in self._color_choices():
                    self.target_value.addItem(c, c)

            # restore previous if possible
            if prev:
                idx = self.target_value.findData(prev)
                if idx < 0:
                    idx = self.target_value.findText(prev)
                if idx < 0:
                    # try match avatar id in data
                    for i in range(self.target_value.count()):
                        if self.target_value.itemData(i) == prev:
                            idx = i
                            break
                if idx >= 0:
                    self.target_value.setCurrentIndex(idx)
                else:
                    self.target_value.setEditText(prev)
            self.target_value.blockSignals(False)

        def _selected_target_value(self) -> str:
            data = self.target_value.currentData()
            if data is not None and data != "":
                return str(data)
            return self.target_value.currentText().strip()

        def _on_law_changed(self, law: str) -> None:
            if self._suppress_law_default:
                return
            # only replace params if empty or still a known default
            cur = self.params_edit.text().strip()
            if not cur or cur in _DEFAULT_PARAMS.values():
                self.params_edit.setText(_DEFAULT_PARAMS.get(law, ""))

        # ------------------------------------------------------------------ state
        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            self._refill_target_values()
            sel = self.tree.selected_payload()
            self.tree.clear_rows()
            for i, op in enumerate(self.controller.project.operations):
                params = _format_params(op.parameters)
                self.tree.add_row(
                    [
                        str(i),
                        op.operation_type,
                        op.target_type,
                        str(op.target_value),
                        params[:48],
                    ],
                    payload=i,
                )
            self.tree.resize_columns()
            if sel is not None:
                self.tree.select_payload(sel)

        def _load_selected(self, index: int) -> None:
            if self.controller is None:
                return
            ops = self.controller.project.operations
            if not (0 <= index < len(ops)):
                return
            op = ops[index]
            self._editing_index = index
            self._suppress_law_default = True
            idx = self.law_combo.findText(op.operation_type)
            if idx < 0:
                self.law_combo.addItem(op.operation_type)
                idx = self.law_combo.findText(op.operation_type)
            self.law_combo.setCurrentIndex(max(0, idx))
            self._suppress_law_default = False

            tidx = self.target_type.findText(op.target_type)
            self.target_type.setCurrentIndex(tidx if tidx >= 0 else 0)
            self._refill_target_values()
            # select target value
            tv = str(op.target_value)
            found = self.target_value.findData(tv)
            if found < 0:
                found = self.target_value.findText(tv)
            if found >= 0:
                self.target_value.setCurrentIndex(found)
            else:
                self.target_value.setEditText(tv)
            self.params_edit.setText(_format_params(op.parameters) or _DEFAULT_PARAMS.get(op.operation_type, ""))

        def _clear_form(self) -> None:
            self._editing_index = None
            self.tree.clearSelection()
            self.law_combo.setCurrentIndex(0)
            self.params_edit.setText(_DEFAULT_PARAMS[self.law_combo.currentText()])
            self._refill_target_values()

        def _build(self) -> DOFOperation:
            law = self.law_combo.currentText().strip()
            ttype = self.target_type.currentText().strip()
            tval = self._selected_target_value()
            if not tval or tval.startswith("("):
                raise ValueError(
                    f"Choisissez une cible valide pour target_type={ttype!r}"
                )
            params = _parse_params(self.params_edit.text())
            return DOFOperation(
                operation_type=law,
                target_type=ttype,
                target_value=tval,
                parameters=params,
            )

        def _on_add(self) -> None:
            if self.controller is None:
                return
            try:
                self.controller.add_dof(self._build())
                self._clear_form()
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "DOF", str(e))

        def _on_update(self) -> None:
            if self.controller is None:
                return
            if self._editing_index is None:
                QMessageBox.information(self, "DOF", "Sélectionnez une ligne")
                return
            try:
                self.controller.update_dof(self._editing_index, self._build())
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "DOF", str(e))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            idx = self.tree.selected_payload()
            if idx is None:
                idx = self._editing_index
            if idx is not None:
                self.controller.remove_dof(int(idx))
                self._clear_form()

    return DOFTab(parent)
