"""ModelTab — QTreeWidget CRUD."""
from __future__ import annotations

from lmgc90_core import Model, ValidationError
from lmgc90_core.types import ELEMENTS_BY_PHYSICS

from .base_tab import BaseTab
from ...utils.naming import suggest_model_name
from ..widgets.entity_tree import create_entity_tree


def create_model_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
        QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class ModelTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_name: str | None = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Liste des modèles — sélectionnez pour modifier"))
            self.tree = create_entity_tree(
                ["Name", "Physics", "Element", "Dim"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)

            form = QFormLayout()
            self.name_edit = QLineEdit()
            self.name_edit.setMaxLength(5)
            self.physics_combo = QComboBox()
            self.physics_combo.addItems(list(ELEMENTS_BY_PHYSICS.keys()) if ELEMENTS_BY_PHYSICS else ["MECAx", "THERx", "POROx", "MULTI"])
            self.element_combo = QComboBox()
            self.dim_label = QLabel("—")
            form.addRow("Name", self.name_edit)
            form.addRow("Physics", self.physics_combo)
            form.addRow("Element", self.element_combo)
            form.addRow("Dimension (project)", self.dim_label)
            layout.addLayout(form)
            self.physics_combo.currentTextChanged.connect(self._refresh_elements)
            self.physics_combo.currentTextChanged.connect(self._suggest_name)
            self.element_combo.currentTextChanged.connect(self._suggest_name)

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

        def _refresh_elements(self, *_a) -> None:
            phys = self.physics_combo.currentText()
            dim = self.controller.project.dimension if self.controller else 2
            elems = []
            table = ELEMENTS_BY_PHYSICS.get(phys) or ELEMENTS_BY_PHYSICS.get("MECAx") or {}
            if isinstance(table, dict):
                elems = list(table.get(dim) or table.get(str(dim)) or ())
            elif isinstance(table, (list, tuple)):
                elems = list(table)
            # fallback from types
            if not elems:
                try:
                    from lmgc90_core.types import elements_for
                    elems = list(elements_for(phys, dim))
                except Exception:
                    elems = ["Rxx2D", "T3xxx"] if dim == 2 else ["Rxx3D", "TE4xx"]
            cur = self.element_combo.currentText()
            self.element_combo.blockSignals(True)
            self.element_combo.clear()
            self.element_combo.addItems([str(e) for e in elems])
            if cur:
                i = self.element_combo.findText(cur)
                if i >= 0:
                    self.element_combo.setCurrentIndex(i)
            self.element_combo.blockSignals(False)

        def _suggest_name(self, *_a) -> None:
            if self.controller is None or self._editing_name:
                return
            existing = [m.name for m in self.controller.project.models]
            suggested = suggest_model_name(
                self.physics_combo.currentText(),
                self.element_combo.currentText(),
                existing,
            )
            cur = self.name_edit.text().strip()
            if not cur or getattr(self, "_last_auto_name", "") == cur:
                self.name_edit.setText(suggested)
                self._last_auto_name = suggested

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            sel = self.tree.selected_payload()
            dim = self.controller.project.dimension
            self.dim_label.setText(f"{dim}D")
            self.tree.clear_rows()
            for m in self.controller.project.models:
                self.tree.add_row(
                    [m.name, m.physics, m.element, str(m.dimension)],
                    m.name,
                )
            self.tree.resize_columns()
            self._refresh_elements()
            if sel:
                self.tree.select_payload(sel)
            if not self._editing_name:
                self._suggest_name()

        def _load_selected(self, name: str) -> None:
            if self.controller is None:
                return
            mod = next((m for m in self.controller.project.models if m.name == name), None)
            if not mod:
                return
            self._editing_name = mod.name
            self.name_edit.setText(mod.name)
            i = self.physics_combo.findText(mod.physics)
            if i >= 0:
                self.physics_combo.setCurrentIndex(i)
            self._refresh_elements()
            j = self.element_combo.findText(mod.element)
            if j >= 0:
                self.element_combo.setCurrentIndex(j)

        def _clear_form(self) -> None:
            self._editing_name = None
            self.name_edit.clear()
            self._last_auto_name = ""
            self._suggest_name()
            self.tree.clearSelection()

        def _build(self) -> Model:
            name = self.name_edit.text().strip()
            if not name:
                raise ValidationError("Name required")
            dim = self.controller.project.dimension
            return Model(
                name=name,
                physics=self.physics_combo.currentText(),
                element=self.element_combo.currentText(),
                dimension=dim,
            )

        def _on_add(self) -> None:
            if self.controller is None:
                return
            try:
                mod = self._build()
                if any(m.name == mod.name for m in self.controller.project.models):
                    raise ValidationError(f"Model {mod.name!r} exists — use Update")
                self.controller.add_model(mod)
                self._clear_form()
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Model", str(exc))

        def _on_update(self) -> None:
            if self.controller is None or not self._editing_name:
                QMessageBox.information(self, "Model", "Sélectionnez un modèle")
                return
            try:
                mod = self._build()
                self.controller.update_model(self._editing_name, mod)
                self._editing_name = mod.name
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Model", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            name = self.tree.selected_payload() or self._editing_name
            if name:
                self.controller.remove_model(name)
                self._clear_form()

    return ModelTab(parent)
