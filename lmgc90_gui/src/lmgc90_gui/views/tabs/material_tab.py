"""MaterialTab — full ELAS family + orthotropic G (pylmgc90-compatible)."""
from __future__ import annotations

import ast

from lmgc90_core import Material, MaterialType, ValidationError
from lmgc90_core.types import coerce_material_type, material_type_name
from lmgc90_engine.schema import material_schema_catalog

from .base_tab import BaseTab
from ...utils.field_forms import clear_layout
from ...utils.naming import suggest_material_name
from ..widgets.entity_tree import create_entity_tree


def create_material_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
        QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class MaterialTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.material_schema = material_schema_catalog()
            self._prop_widgets: dict = {}
            self._editing_name: str | None = None
            layout = QVBoxLayout(self)

            layout.addWidget(QLabel(
                "Liste des matériaux — sélectionnez pour modifier. "
                "Orthotrope : E1/E2/(E3), νij, <b>Gij</b>."
            ))
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
            for material_type in self.material_schema["types"]:
                value = coerce_material_type(str(material_type))
                self.type_combo.addItem(material_type_name(value), value)
            self.density_edit = QLineEdit("7800")
            self.density_edit.setPlaceholderText("nombre ou expression")
            self.mark_expr_field(self.density_edit)
            form.addRow("Name", self.name_edit)
            form.addRow("Type", self.type_combo)
            form.addRow("Density", self.density_edit)
            layout.addLayout(form)

            self.props_box = QGroupBox("Propriétés (selon type / anisotropie)")
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

        def _project_dim(self) -> int:
            if self.controller is None:
                return 2
            return int(getattr(self.controller.project, "dimension", 2) or 2)

        def _rebuild_props(self, *_a) -> None:
            clear_layout(self.props_form)
            self._prop_widgets.clear()
            mtype = self.type_combo.currentData()
            key = material_type_name(mtype) if mtype else "RIGID"
            options = self.material_schema.get("options", {})
            if key in options:
                self.density_edit.setEnabled("density" in options[key])
            else:
                self.density_edit.setEnabled(
                    key not in (
                        MaterialType.DISCRETE.value,
                        MaterialType.EXTERNAL.value,
                    )
                )
            schema = self.material_schema["properties"].get(key, ())
            if not schema:
                self.props_form.addRow(QLabel("(aucune propriété spécifique)"))
                return

            # Always build all schema widgets; visibility toggled by anisotropy
            for name, default, kind in schema:
                type_choices = self.material_schema.get(
                    "choices_by_type", {},
                ).get(key, {})
                choices = type_choices.get(
                    name, self.material_schema["choices"].get(name),
                )
                if (
                    name == "anisotropy"
                    and key != MaterialType.ELAS.value
                    and name not in type_choices
                ):
                    choices = ("isotropic",)
                if choices:
                    w = QComboBox()
                    w.addItems(list(choices))
                    i = w.findText(str(default))
                    if i >= 0:
                        w.setCurrentIndex(i)
                    w.currentTextChanged.connect(self._apply_anisotropy_visibility)
                    self.props_form.addRow(self.material_schema["labels"].get(name, name), w)
                    self._prop_widgets[name] = (w, "combo")
                    continue
                if name == "elas":
                    w = QComboBox()
                    w.addItems(list(self.material_schema["choices"][name]))
                    i = w.findText(str(default))
                    if i >= 0:
                        w.setCurrentIndex(i)
                    else:
                        w.setCurrentIndex(0)
                    self.props_form.addRow(self.material_schema["labels"].get(name, name), w)
                    self._prop_widgets[name] = (w, "combo")
                    continue
                if kind == "float":
                    w = QLineEdit(str(default) if default not in (None, "") else "0")
                    w.setPlaceholderText("nombre ou expression")
                    self.mark_expr_field(w)
                elif kind == "float_or_field":
                    w = QLineEdit(str(default))
                    w.setPlaceholderText("nombre, expression ou field")
                    self.mark_expr_field(w)
                elif kind == "vector":
                    dim = self._project_dim()
                    values = tuple(default)
                    w = QLineEdit(", ".join(str(v) for v in values[:dim]))
                    w.setPlaceholderText("valeurs / expressions séparées par des virgules")
                    self.mark_expr_field(w)
                elif kind == "auto":
                    w = QLineEdit(str(default) if default is not None else "")
                    w.setPlaceholderText("valeur ou expression")
                    self.mark_expr_field(w)
                else:
                    w = QLineEdit(str(default) if default is not None else "")
                self.props_form.addRow(self.material_schema["labels"].get(name, name), w)
                self._prop_widgets[name] = (w, kind)

            self._apply_anisotropy_visibility()

        def _apply_anisotropy_visibility(self, *_a) -> None:
            aniso = "isotropic"
            if "anisotropy" in self._prop_widgets:
                aniso = self._prop_widgets["anisotropy"][0].currentText().strip().lower()
            ortho = aniso in ("orthotropic", "ortho")
            dim = self._project_dim()
            ortho_keys = set(
                self.material_schema["orthotropic_fields"][3 if dim == 3 else 2]
            )
            all_ortho = set(self.material_schema["orthotropic_fields"][3])

            for name, (w, _kind) in self._prop_widgets.items():
                if name in ("anisotropy", "elas"):
                    continue
                if name in self.material_schema["isotropic_fields"]:
                    show = not ortho
                elif name in all_ortho:
                    show = ortho and name in ortho_keys
                else:
                    show = True
                w.setVisible(show)
                w.setEnabled(show)
            for i in range(self.props_form.rowCount()):
                lab_item = self.props_form.itemAt(i, QFormLayout.ItemRole.LabelRole)
                field_item = self.props_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if field_item is None:
                    continue
                fw = field_item.widget()
                if fw is None:
                    continue
                vis = fw.isVisible()
                if lab_item and lab_item.widget():
                    lab_item.widget().setVisible(vis)

        def _suggest_name(self, *_a) -> None:
            if self.controller is None or self._editing_name:
                return
            mtype = self.type_combo.currentData()
            key = material_type_name(mtype) if mtype else "RIGID"
            existing = [m.name for m in self.controller.project.materials]
            suggested = suggest_material_name(key, existing)
            cur = self.name_edit.text().strip()
            if not cur or getattr(self, "_last_auto_name", "") == cur:
                self.name_edit.setText(suggested)
                self._last_auto_name = suggested

        def _collect_props(self) -> dict:
            props = {}
            aniso = "isotropic"
            if "anisotropy" in self._prop_widgets:
                aniso = self._prop_widgets["anisotropy"][0].currentText().strip().lower()
            ortho = aniso in ("orthotropic", "ortho")
            dim = self._project_dim()
            ortho_keys = set(
                self.material_schema["orthotropic_fields"][3 if dim == 3 else 2]
            )

            for key, (w, kind) in self._prop_widgets.items():
                if key in self.material_schema["isotropic_fields"] and ortho:
                    continue
                if key in set(self.material_schema["orthotropic_fields"][3]):
                    if not ortho or key not in ortho_keys:
                        continue
                if kind == "float":
                    if not w.isEnabled():
                        continue
                    props[key] = self.eval_float(w.text(), 0.0, key)
                elif kind == "float_or_field":
                    text = w.text().strip()
                    props[key] = "field" if text.lower() == "field" else self.eval_float(text, 0.0, key)
                elif kind == "vector":
                    dim = self._project_dim()
                    props[key] = self.eval_list(
                        w.text().replace(";", ","), dim, field_name=key
                    )
                elif kind == "auto":
                    text = w.text().strip()
                    if not text:
                        continue
                    try:
                        props[key] = ast.literal_eval(text)
                    except (SyntaxError, ValueError):
                        props[key] = text
                elif kind == "combo":
                    props[key] = w.currentText().strip()
                else:
                    if not w.isEnabled():
                        continue
                    props[key] = w.text().strip()
            return props

        def _build_material(self) -> Material:
            name = self.name_edit.text().strip()
            if not name:
                raise ValidationError("Name required")
            if len(name) > 5:
                raise ValidationError("Name must be ≤ 5 characters (LMGC90)")
            mtype = self.type_combo.currentData()
            props = self._collect_props()
            if props.get("anisotropy", "").lower() in ("orthotropic", "ortho"):
                # require G12
                if "G12" not in props:
                    raise ValidationError(
                        "Orthotrope : G12 (module de cisaillement) est obligatoire"
                    )
            return Material(
                name=name,
                material_type=mtype,
                density=self.eval_float(self.density_edit.text(), 7800.0, "density"),
                properties=props,
            )

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            sel = self.tree.selected_payload()
            self.tree.clear_rows()
            for m in self.controller.project.materials:
                extra = ", ".join(f"{k}={v}" for k, v in (m.properties or {}).items())
                self.tree.add_row(
                    [
                        m.name, material_type_name(m.material_type),
                        f"{m.density:g}", extra[:80],
                    ],
                    m.name,
                )
            self.tree.resize_columns()
            if sel:
                self.tree.select_payload(sel)
            if not self._editing_name:
                self._suggest_name()
            # dimension may have changed → refresh ortho field set
            self._apply_anisotropy_visibility()

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
                idx = self.type_combo.findText(
                    material_type_name(mat.material_type),
                )
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.density_edit.setText(str(mat.density))
            self._rebuild_props()
            props = mat.properties or {}
            for key, (w, kind) in self._prop_widgets.items():
                val = props.get(key)
                if val is None:
                    continue
                if kind == "float":
                    try:
                        w.setText(str(val))
                    except Exception:
                        pass
                elif kind == "combo":
                    i = w.findText(str(val))
                    if i >= 0:
                        w.setCurrentIndex(i)
                else:
                    w.setText(str(val))
            self._apply_anisotropy_visibility()

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
                    QMessageBox.warning(self, "Material", f"{mat.name!r} existe déjà")
                    return
                self.controller.add_material(mat)
                self._clear_form()
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Material", str(exc))

        def _on_update(self) -> None:
            if self.controller is None or not self._editing_name:
                QMessageBox.information(self, "Material", "Sélectionnez un matériau")
                return
            try:
                mat = self._build_material()
                self.controller.update_material(self._editing_name, mat)
                self._editing_name = mat.name
                QMessageBox.information(self, "Material", f"{mat.name} mis à jour")
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Material", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            name = self._editing_name or self.tree.selected_payload()
            if not name:
                return
            self.controller.remove_material(name)
            self._clear_form()

    return MaterialTab(parent)
