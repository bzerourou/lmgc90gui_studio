"""MaterialTab — full ELAS family + orthotropic G (pylmgc90-compatible)."""
from __future__ import annotations

from lmgc90_core import Material, MaterialType, ValidationError
from lmgc90_core.types import (
    ISOTROPIC_FIELDS,
    MATERIAL_PROPERTY_CHOICES,
    MATERIAL_PROPERTY_SCHEMA,
    ORTHOTROPIC_FIELDS_2D,
    ORTHOTROPIC_FIELDS_3D,
)

from .base_tab import BaseTab
from ...utils.field_forms import clear_layout
from ...utils.naming import suggest_material_name
from ..widgets.entity_tree import create_entity_tree

_ELAS_TYPES = {
    MaterialType.ELAS,
    MaterialType.ELAS_DILA,
    MaterialType.VISCO_ELAS,
    MaterialType.ELAS_PLAS,
    MaterialType.THERMO_ELAS,
    MaterialType.PORO_ELAS,
}

_LABELS = {
    "elas": "elas (loi)",
    "anisotropy": "anisotropy",
    "young": "E — Young (Pa)",
    "nu": "ν — Poisson",
    "young1": "E1 — Young dir. 1 (Pa)",
    "young2": "E2 — Young dir. 2 (Pa)",
    "young3": "E3 — Young dir. 3 (Pa)",
    "nu12": "ν12 — Poisson",
    "nu13": "ν13 — Poisson",
    "nu23": "ν23 — Poisson",
    "G": "G — cisaillement (Pa)",
    "G12": "G12 — cisaillement (Pa)",
    "G13": "G13 — cisaillement (Pa)",
    "G23": "G23 — cisaillement (Pa)",
    "dilatation": "dilatation (α thermique / dilatation)",
    "T_ref_meca": "température mécanique de référence",
    "viscous_model": "modèle visqueux",
    "viscous_young": "Young visqueux (Pa)",
    "viscous_nu": "Poisson visqueux",
    "critere": "critère plastique",
    "isoh": "écrouissage isotrope",
    "iso_hard": "limite élastique initiale (Pa)",
    "isoh_coeff": "module d’écrouissage isotrope (Pa)",
    "cinh": "écrouissage cinématique",
    "visc": "viscoplasticité",
    "conductivity": "conductivité",
    "specific_capacity": "capacité spécifique / stockage",
    "hydro_cpl": "couplage hydraulique (Biot)",
    "masses": "masses (vecteur 2D/3D)",
    "stiffnesses": "raideurs (vecteur 2D/3D)",
    "viscosities": "viscosités (vecteur 2D/3D)",
    "file_mat": "fichier de loi matériau",
}


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
            for mt in MaterialType:
                self.type_combo.addItem(mt.value, mt)
            self.density_edit = QLineEdit("7800")
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
            key = mtype.value if mtype else "RIGID"
            self.density_edit.setEnabled(
                mtype not in (MaterialType.DISCRETE, MaterialType.EXTERNAL)
            )
            schema = MATERIAL_PROPERTY_SCHEMA.get(key, ())
            if not schema:
                self.props_form.addRow(QLabel("(aucune propriété spécifique)"))
                return

            # Always build all schema widgets; visibility toggled by anisotropy
            for name, default, kind in schema:
                choices = MATERIAL_PROPERTY_CHOICES.get(name)
                if name == "anisotropy" and mtype != MaterialType.ELAS:
                    choices = ("isotropic",)
                if choices:
                    w = QComboBox()
                    w.addItems(list(choices))
                    i = w.findText(str(default))
                    if i >= 0:
                        w.setCurrentIndex(i)
                    w.currentTextChanged.connect(self._apply_anisotropy_visibility)
                    self.props_form.addRow(_LABELS.get(name, name), w)
                    self._prop_widgets[name] = (w, "combo")
                    continue
                if name == "elas":
                    w = QComboBox()
                    w.addItems(list(MATERIAL_PROPERTY_CHOICES[name]))
                    i = w.findText(str(default))
                    if i >= 0:
                        w.setCurrentIndex(i)
                    else:
                        w.setCurrentIndex(0)
                    self.props_form.addRow(_LABELS.get(name, name), w)
                    self._prop_widgets[name] = (w, "combo")
                    continue
                if kind == "float":
                    w = QDoubleSpinBox()
                    w.setRange(0.0, 1e30)
                    w.setDecimals(6)
                    if name.startswith(("young", "G", "sigc")):
                        w.setDecimals(4)
                    w.setValue(float(default) if default not in (None, "") else 0.0)
                elif kind == "float_or_field":
                    w = QLineEdit(str(default))
                    w.setPlaceholderText("valeur numérique ou field")
                elif kind == "vector":
                    dim = self._project_dim()
                    values = tuple(default)
                    w = QLineEdit(", ".join(str(v) for v in values[:dim]))
                    w.setPlaceholderText("valeurs séparées par des virgules")
                else:
                    w = QLineEdit(str(default) if default is not None else "")
                self.props_form.addRow(_LABELS.get(name, name), w)
                self._prop_widgets[name] = (w, kind)

            self._apply_anisotropy_visibility()

        def _apply_anisotropy_visibility(self, *_a) -> None:
            mtype = self.type_combo.currentData()
            if mtype not in _ELAS_TYPES and mtype not in (
                MaterialType.ELAS, MaterialType.ELAS_DILA, MaterialType.VISCO_ELAS,
            ):
                # only types with orthotropic extras
                pass
            aniso = "isotropic"
            if "anisotropy" in self._prop_widgets:
                aniso = self._prop_widgets["anisotropy"][0].currentText().strip().lower()
            ortho = aniso in ("orthotropic", "ortho")
            dim = self._project_dim()
            ortho_keys = set(ORTHOTROPIC_FIELDS_3D if dim == 3 else ORTHOTROPIC_FIELDS_2D)
            # hide 3D-only when 2D
            all_ortho = set(ORTHOTROPIC_FIELDS_3D)

            for name, (w, _kind) in self._prop_widgets.items():
                if name in ("anisotropy", "elas"):
                    continue
                # non elastic extra fields always on (alpha, eta, ...)
                if name in ISOTROPIC_FIELDS:
                    show = not ortho
                elif name in all_ortho:
                    show = ortho and name in ortho_keys
                else:
                    show = True
                w.setVisible(show)
                w.setEnabled(show)
                # label visibility: walk form rows
            # update form labels visibility by matching widgets
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
            key = mtype.value if mtype else "RIGID"
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
            ortho_keys = set(ORTHOTROPIC_FIELDS_3D if dim == 3 else ORTHOTROPIC_FIELDS_2D)

            for key, (w, kind) in self._prop_widgets.items():
                if key in ISOTROPIC_FIELDS and ortho:
                    continue
                if key in set(ORTHOTROPIC_FIELDS_3D):
                    if not ortho or key not in ortho_keys:
                        continue
                if kind == "float":
                    if not w.isEnabled():
                        continue
                    props[key] = float(w.value())
                elif kind == "float_or_field":
                    text = w.text().strip()
                    props[key] = "field" if text.lower() == "field" else self.eval_float(text, 0.0, key)
                elif kind == "vector":
                    parts = [part.strip() for part in w.text().replace(";", ",").split(",") if part.strip()]
                    dim = self._project_dim()
                    if len(parts) != dim:
                        raise ValidationError(f"{key} doit contenir {dim} valeurs pour un projet {dim}D")
                    props[key] = [self.eval_float(part, 0.0, key) for part in parts]
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
                    [m.name, m.material_type.value, f"{m.density:g}", extra[:80]],
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
                idx = self.type_combo.findText(mat.material_type.value)
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
                        w.setValue(float(val))
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
                # remove old if renamed
                if mat.name != self._editing_name:
                    self.controller.remove_material(self._editing_name)
                    self.controller.add_material(mat)
                else:
                    # replace in place via remove+add to keep simple API
                    self.controller.remove_material(self._editing_name)
                    self.controller.add_material(mat)
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
