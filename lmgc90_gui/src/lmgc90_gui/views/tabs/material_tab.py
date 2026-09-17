"""MaterialTab — QTreeWidget list + form CRUD (select → edit → Update)."""
from __future__ import annotations

from lmgc90_core import Material, MaterialType, ValidationError
from lmgc90_core.types import MATERIAL_PROPERTY_SCHEMA

from .base_tab import BaseTab
from ...utils.field_forms import clear_layout
from ...utils.naming import suggest_material_name
from ..widgets.entity_tree import create_entity_tree


def create_material_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
        QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class MaterialTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._prop_widgets: dict = {}
            self._editing_name: str | None = None
            layout = QVBoxLayout(self)

            layout.addWidget(QLabel("Liste des matériaux — sélectionnez pour modifier"))
            self.tree = create_entity_tree(
                ["Name", "Type", "Density", "Properties"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)

            form = QFormLayout()
            self.name_edit = QLineEdit()
            self.name_edit.setMaxLength(5)
            self.name_edit.setPlaceholderText("≤ 5 chars (LMGC90)")
            self.type_combo = QComboBox()
            for t in MaterialType:
                self.type_combo.addItem(t.value, t)
            self.density_edit = QLineEdit("7800")
            self.density_edit.setPlaceholderText("7800 or expression")
            self.mark_expr_field(self.density_edit)
            form.addRow("Name", self.name_edit)
            form.addRow("Type", self.type_combo)
            form.addRow("Density", self.density_edit)
            layout.addLayout(form)
            self.add_expression_help_label(layout)

            self.props_box = QGroupBox("Type-specific properties")
            self.props_form = QFormLayout(self.props_box)
            layout.addWidget(self.props_box)
            self.type_combo.currentIndexChanged.connect(self._rebuild_props)
            self.type_combo.currentIndexChanged.connect(self._suggest_name)
            self._rebuild_props()

            row = QHBoxLayout()
            btn_add = QPushButton("➕ Add")
            btn_upd = QPushButton("💾 Update")
            btn_rm = QPushButton("🗑️ Delete")
            btn_clr = QPushButton("Clear form")
            btn_add.clicked.connect(self._on_add)
            btn_upd.clicked.connect(self._on_update)
            btn_rm.clicked.connect(self._on_remove)
            btn_clr.clicked.connect(self._clear_form)
            row.addWidget(btn_add)
            row.addWidget(btn_upd)
            row.addWidget(btn_rm)
            row.addWidget(btn_clr)
            layout.addLayout(row)

        def _rebuild_props(self, *_a) -> None:
            clear_layout(self.props_form)
            self._prop_widgets.clear()
            mtype = self.type_combo.currentData()
            key = mtype.value if mtype else "RIGID"
            for name, default, kind in MATERIAL_PROPERTY_SCHEMA.get(key, ()):
                if kind == "float":
                    w = QDoubleSpinBox()
                    w.setRange(-1e30, 1e30)
                    w.setDecimals(6)
                    w.setValue(float(default) if default not in (None, "") else 0.0)
                else:
                    w = QLineEdit(str(default) if default is not None else "")
                self.props_form.addRow(name, w)
                self._prop_widgets[name] = (w, kind)

        def _suggest_name(self, *_a) -> None:
            if self.controller is None or self._editing_name:
                return
            mtype = self.type_combo.currentData()
            key = mtype.value if mtype else "RIGID"
            existing = [m.name for m in self.controller.project.materials]
            suggested = suggest_material_name(key, existing)
            cur = self.name_edit.text().strip()
            if not cur or getattr(self, "_last_auto_name", "") == cur:
                self.name_edit.setText(suggested)
                self._last_auto_name = suggested

        def _collect_props(self) -> dict:
            props = {}
            for key, (w, kind) in self._prop_widgets.items():
                if kind == "float":
                    props[key] = float(w.value())
                else:
                    props[key] = w.text().strip()
            return props

        def _build_material(self) -> Material:
            name = self.name_edit.text().strip()
            if not name:
                raise ValidationError("Name required")
            mtype = self.type_combo.currentData()
            return Material(
                name=name,
                material_type=mtype,
                density=self.eval_float(self.density_edit.text(), 7800.0, "density"),
                properties=self._collect_props(),
            )

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            sel = self.tree.selected_payload()
            self.tree.clear_rows()
            for m in self.controller.project.materials:
                extra = ", ".join(f"{k}={v}" for k, v in (m.properties or {}).items())
                self.tree.add_row(
                    [m.name, m.material_type.value, f"{m.density:g}", extra[:60]],
                    m.name,
                )
            self.tree.resize_columns()
            if sel:
                self.tree.select_payload(sel)
            if not self._editing_name:
                self._suggest_name()

        def _load_selected(self, name: str) -> None:
            if self.controller is None or not name:
                return
            mat = next((m for m in self.controller.project.materials if m.name == name), None)
            if mat is None:
                return
            self._editing_name = mat.name
            self.name_edit.setText(mat.name)
            idx = self.type_combo.findData(mat.material_type)
            if idx < 0:
                idx = self.type_combo.findText(mat.material_type.value)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.density_edit.setText(str(mat.density))
            self._rebuild_props()
            for key, (w, kind) in self._prop_widgets.items():
                val = (mat.properties or {}).get(key)
                if val is None:
                    continue
                if kind == "float":
                    try:
                        w.setValue(float(val))
                    except Exception:
                        pass
                else:
                    w.setText(str(val))

        def _clear_form(self) -> None:
            self._editing_name = None
            self.name_edit.clear()
            self.density_edit.setText("7800")
            self._last_auto_name = ""
            self._rebuild_props()
            self._suggest_name()
            self.tree.clearSelection()

        def _on_add(self) -> None:
            if self.controller is None:
                return
            try:
                mat = self._build_material()
                if any(m.name == mat.name for m in self.controller.project.materials):
                    raise ValidationError(f"Material {mat.name!r} already exists — use Update")
                self.controller.add_material(mat)
                self._clear_form()
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Material", str(exc))

        def _on_update(self) -> None:
            if self.controller is None:
                return
            if not self._editing_name:
                QMessageBox.information(self, "Material", "Sélectionnez un matériau dans la liste")
                return
            try:
                mat = self._build_material()
                self.controller.update_material(self._editing_name, mat)
                self._editing_name = mat.name
                self.controller.journal.info(f"Material updated: {mat.name}")
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Material", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            name = self.tree.selected_payload() or self._editing_name
            if not name:
                return
            self.controller.remove_material(name)
            self._clear_form()

    return MaterialTab(parent)
