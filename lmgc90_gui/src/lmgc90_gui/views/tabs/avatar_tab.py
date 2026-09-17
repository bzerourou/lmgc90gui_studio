"""AvatarTab — all avatar types for project dimension, with type-specific params."""
from __future__ import annotations

from lmgc90_core import ValidationError
from lmgc90_core.types import RIGID_AVATARS_2D, RIGID_AVATARS_3D, AvatarType

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree
from ...utils.field_forms import AVATAR_PARAM_SCHEMA, clear_layout, parse_vertices


def create_avatar_tab(parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
        QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
        QSpinBox, QVBoxLayout, QWidget,
    )

    class AvatarTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._param_widgets: dict = {}
            layout = QVBoxLayout(self)
            layout.addWidget(__import__("PyQt6.QtWidgets", fromlist=["QLabel"]).QLabel("Avatars — sélectionnez pour modifier"))
            self.tree = create_entity_tree(
                ["ID", "Type", "Center", "Material", "Model", "Color"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)
            self._editing_id = None

            form = QFormLayout()
            self.type_combo = QComboBox()
            self.cx = QDoubleSpinBox(); self.cy = QDoubleSpinBox(); self.cz = QDoubleSpinBox()
            for s in (self.cx, self.cy, self.cz):
                s.setRange(-1e9, 1e9)
                s.setDecimals(8)
            self.mat_combo = QComboBox()
            self.mod_combo = QComboBox()
            self.color_edit = QLineEdit("BLUEx")
            form.addRow("Type", self.type_combo)
            form.addRow("Center X", self.cx)
            form.addRow("Center Y", self.cy)
            form.addRow("Center Z", self.cz)
            form.addRow("Material", self.mat_combo)
            form.addRow("Model", self.mod_combo)
            form.addRow("Color", self.color_edit)
            layout.addLayout(form)
            self.add_expression_help_label(layout)

            self.params_box = QGroupBox("Type parameters")
            self.params_form = QFormLayout(self.params_box)
            layout.addWidget(self.params_box)
            self.type_combo.currentIndexChanged.connect(self._rebuild_params)

            row = QHBoxLayout()
            btn_add = QPushButton("➕ Add")
            btn_upd = QPushButton("💾 Update")
            btn_rm = QPushButton("🗑️ Delete")
            btn_add.clicked.connect(self._on_add)
            btn_upd.clicked.connect(self._on_update)
            btn_rm.clicked.connect(self._on_remove)
            row.addWidget(btn_add)
            row.addWidget(btn_upd)
            row.addWidget(btn_rm)
            layout.addLayout(row)
            layout.addWidget(QLabel("Identity = avatar_id (stable, never list index)"))

        def _types_for_dim(self, dim: int):
            if dim == 3:
                types = list(RIGID_AVATARS_3D) + [AvatarType.EMPTY_AVATAR, AvatarType.MESH_DEFORMABLE]
            else:
                types = list(RIGID_AVATARS_2D) + [AvatarType.EMPTY_AVATAR, AvatarType.MESH_DEFORMABLE]
            return sorted(set(types), key=lambda t: t.value)

        def _rebuild_type_list(self) -> None:
            dim = self.controller.project.dimension if self.controller else 2
            cur = self.type_combo.currentData()
            self.type_combo.blockSignals(True)
            self.type_combo.clear()
            for t in self._types_for_dim(dim):
                self.type_combo.addItem(t.value, t)
            self.type_combo.blockSignals(False)
            if cur is not None:
                idx = self.type_combo.findData(cur)
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)
            self.cz.setEnabled(dim == 3)
            self._rebuild_params()

        def _rebuild_params(self, *_a) -> None:
            clear_layout(self.params_form)
            self._param_widgets.clear()
            atype = self.type_combo.currentData()
            key = atype.value if atype else "rigidDisk"
            schema = AVATAR_PARAM_SCHEMA.get(key, ())
            for name, default, kind in schema:
                if kind == "float":
                    w = QLineEdit(str(default))
                    w.setPlaceholderText("number or expression")
                elif kind == "int":
                    w = QSpinBox(); w.setRange(0, 1_000_000); w.setValue(int(default))
                elif kind == "bool":
                    w = QCheckBox(); w.setChecked(bool(default))
                else:
                    w = QLineEdit(str(default))
                    if name == "vertices":
                        w.setPlaceholderText("x1,y1; x2,y2; …")
                self.params_form.addRow(name, w)
                self._param_widgets[name] = (w, kind)
            self.params_box.setVisible(bool(schema))

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.tree.clear_rows()
            sel = self.tree.selected_payload()
            for av in p.avatars:
                self.tree.add_row(
                    [
                        av.avatar_id[:10] + "…",
                        av.avatar_type.value,
                        str(av.center),
                        av.material_name,
                        av.model_name,
                        av.color,
                    ],
                    av.avatar_id,
                )
            self.tree.resize_columns()
            if sel:
                self.tree.select_payload(sel)
            cur_m, cur_o = self.mat_combo.currentText(), self.mod_combo.currentText()
            self.mat_combo.clear(); self.mat_combo.addItems([m.name for m in p.materials])
            self.mod_combo.clear(); self.mod_combo.addItems([m.name for m in p.models])
            if cur_m:
                i = self.mat_combo.findText(cur_m)
                if i >= 0: self.mat_combo.setCurrentIndex(i)
            if cur_o:
                i = self.mod_combo.findText(cur_o)
                if i >= 0: self.mod_combo.setCurrentIndex(i)
            self._rebuild_type_list()

        def _read_params(self) -> dict:
            out = {}
            for name, (w, kind) in self._param_widgets.items():
                if kind == "float":
                    # allow expression if the widget is a line edit
                    if hasattr(w, "text") and not hasattr(w, "value"):
                        out[name] = self.eval_float(w.text(), 0.0, name)
                    else:
                        out[name] = float(w.value())
                elif kind == "int":
                    if hasattr(w, "text") and not hasattr(w, "value"):
                        out[name] = self.eval_int(w.text(), 0, name)
                    else:
                        out[name] = int(w.value())
                elif kind == "bool":
                    out[name] = bool(w.isChecked())
                else:
                    out[name] = w.text().strip()
            return out

        def _read_num(self, w):
            from PyQt6.QtWidgets import QLineEdit, QDoubleSpinBox, QSpinBox
            if isinstance(w, QLineEdit):
                return self.eval_float(w.text(), 0.0)
            if isinstance(w, (QDoubleSpinBox, QSpinBox)):
                return w.value()
            return w

        def _on_add(self) -> None:
            if self.controller is None:
                return
            pre = self.controller.pre()
            atype = self.type_combo.currentData()
            mat = self.mat_combo.currentText()
            mod = self.mod_combo.currentText()
            if not mat or not mod:
                QMessageBox.warning(self, "Avatar", "Material and model required")
                return
            dim = self.controller.project.dimension
            center = [
                self.eval_float(self.cx.text(), 0.0, "center X"),
                self.eval_float(self.cy.text(), 0.0, "center Y"),
            ]
            if dim == 3:
                center.append(self.eval_float(self.cz.text(), 0.0, "center Z"))
            color = self.color_edit.text().strip() or "BLUEx"
            p = self._read_params()
            try:
                av = self._build(pre, atype, center, mat, mod, color, p)
                self.controller.add_avatar(av)
            except (ValidationError, ValueError, TypeError, KeyError) as exc:
                QMessageBox.warning(self, "Avatar", str(exc))

        def _build(self, pre, atype, center, mat, mod, color, p):
            t = atype
            if t == AvatarType.RIGID_DISK:
                return pre.rigidDisk(r=p.get("r", 0.1), center=center, model=mod, material=mat, color=color, is_Hollow=p.get("is_Hollow", False))
            if t == AvatarType.RIGID_SPHERE:
                return pre.rigidSphere(r=p.get("r", 0.1), center=center, model=mod, material=mat, color=color, is_Hollow=p.get("is_Hollow", False))
            if t == AvatarType.RIGID_DISCRETE:
                return pre.rigidDiscreteDisk(r=p.get("r", 0.1), center=center, model=mod, material=mat, color=color)
            if t == AvatarType.RIGID_JONC:
                return pre.rigidJonc(axe1=p["axe1"], axe2=p["axe2"], center=center, model=mod, material=mat, color=color)
            if t == AvatarType.RIGID_POLYGON:
                return pre.rigidPolygon(center=center, model=mod, material=mat, color=color, generation_type=p.get("generation_type") or "regular", nb_vertices=int(p.get("nb_vertices") or 6), radius=float(p["radius"]) if p.get("radius") not in (None, "") else None, vertices=parse_vertices(p.get("vertices") or ""))
            if t == AvatarType.RIGID_OVOID:
                return pre.rigidOvoidPolygon(center=center, model=mod, material=mat, color=color, radius=p.get("radius"), vertices=parse_vertices(p.get("vertices") or ""))
            if t == AvatarType.RIGID_CLUSTER:
                return pre.rigidCluster(r=p.get("r", 0.05), center=center, model=mod, material=mat, color=color, nb_disk=int(p.get("nb_disk", 3)))
            if t == AvatarType.RIGID_CYLINDER:
                return pre.rigidCylinder(r=p.get("r", 0.1), h=p.get("h", 0.3), center=center, model=mod, material=mat, color=color, is_Hollow=p.get("is_Hollow", False))
            if t == AvatarType.RIGID_PLAN:
                return pre.rigidPlan(center=center, model=mod, material=mat, color=color, axe1=p["axe1"], axe2=p["axe2"], axe3=p["axe3"])
            if t == AvatarType.RIGID_POLYHEDRON:
                return pre.rigidPolyhedron(center=center, model=mod, material=mat, color=color, generation_type=p.get("generation_type") or "regular", nb_vertices=int(p.get("nb_vertices") or 8), radius=float(p["radius"]) if p.get("radius") not in (None, "") else None, vertices=parse_vertices(p.get("vertices") or ""))
            if t == AvatarType.SMOOTH_WALL:
                return pre.smoothWall(l=p["l"], h=p["h"], center=center, model=mod, material=mat, color=color, nb_polyg=int(p.get("nb_polyg", 16)))
            if t == AvatarType.ROUGH_WALL:
                return pre.roughWall(l=p["l"], r=p["r"], center=center, model=mod, material=mat, color=color, nb_vertex=int(p.get("nb_vertex", 10)))
            if t == AvatarType.FINE_WALL:
                return pre.fineWall(l=p["l"], r=p["r"], center=center, model=mod, material=mat, color=color, nb_vertex=int(p.get("nb_vertex", 10)))
            if t == AvatarType.GRANULO_WALL:
                return pre.granuloRoughWall(l=p["l"], rmin=p["rmin"], rmax=p["rmax"], center=center, model=mod, material=mat, color=color, nb_vertex=int(p.get("nb_vertex", 10)))
            if t == AvatarType.ROUGH_WALL_3D:
                return pre.roughWall3D(lx=p["lx"], ly=p["ly"], lz=p["lz"], center=center, model=mod, material=mat, color=color)
            if t == AvatarType.GRANULO_ROUGH_WALL_3D:
                return pre.granuloRoughWall3D(lx=p["lx"], ly=p["ly"], lz=p["lz"], rmin=p["rmin"], rmax=p["rmax"], center=center, model=mod, material=mat, color=color)
            if t == AvatarType.EMPTY_AVATAR:
                return pre.emptyAvatar(center=center, model=mod, material=mat, color=color)
            if t == AvatarType.MESH_DEFORMABLE:
                return pre.meshed_rectangle(lx=p.get("lx", 0.15), ly=p.get("ly", 0.3), nx=int(p.get("nx", 4)), ny=int(p.get("ny", 8)), center=center, model=mod, material=mat, color=color, mesh_type=p.get("mesh_type") or "2T3")
            raise ValueError(f"unsupported avatar type {t}")

        def _load_selected(self, avatar_id: str) -> None:
            if self.controller is None or not avatar_id:
                return
            av = next((a for a in self.controller.project.avatars if a.avatar_id == avatar_id), None)
            if av is None:
                return
            self._editing_id = av.avatar_id
            # type
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == av.avatar_type:
                    self.type_combo.setCurrentIndex(i)
                    break
            # center
            c = list(av.center)
            self.cx.setText(f"{float(c[0] if c else 0):.8g}")
            self.cy.setText(f"{float(c[1] if len(c) > 1 else 0):.8g}")
            if len(c) > 2:
                self.cz.setText(f"{float(c[2]):.8g}")
            i = self.mat_combo.findText(av.material_name)
            if i >= 0:
                self.mat_combo.setCurrentIndex(i)
            i = self.mod_combo.findText(av.model_name)
            if i >= 0:
                self.mod_combo.setCurrentIndex(i)
            self.color_edit.setText(av.color or "BLUEx")
            self._rebuild_params()
            # fill known params from avatar attributes
            mapping = {
                "r": av.radius, "radius": av.radius,
                "h": (av.wall_params or {}).get("h"),
                "l": (av.wall_params or {}).get("l"),
            }
            if av.axis:
                mapping.update(av.axis)
            if av.mesh_params:
                mapping.update(av.mesh_params)
            for name, (w, kind) in self._param_widgets.items():
                val = mapping.get(name)
                if val is None:
                    continue
                if kind == "float":
                    if hasattr(w, "setValue"):
                        w.setValue(float(val))
                    else:
                        w.setText(str(val))
                elif kind == "int":
                    if hasattr(w, "setValue"):
                        w.setValue(int(val))
                    else:
                        w.setText(str(val))
                elif kind == "bool":
                    w.setChecked(bool(val))
                else:
                    w.setText(str(val))

        def _on_update(self) -> None:
            if self.controller is None or not getattr(self, "_editing_id", None):
                QMessageBox.information(self, "Avatar", "Sélectionnez un avatar dans la liste")
                return
            try:
                pre = self.controller.pre()
                atype = self.type_combo.currentData()
                mat = self.mat_combo.currentText()
                mod = self.mod_combo.currentText()
                dim = self.controller.project.dimension
                center = [
                    self.eval_float(self.cx.text(), 0.0, "center X"),
                    self.eval_float(self.cy.text(), 0.0, "center Y"),
                ]
                if dim == 3:
                    center.append(self.eval_float(self.cz.text(), 0.0, "center Z"))
                color = self.color_edit.text().strip() or "BLUEx"
                p = self._read_params()
                av = self._build(pre, atype, center, mat, mod, color, p)
                self.controller.update_avatar(self._editing_id, av)
                self.controller.journal.info(f"Avatar updated {self._editing_id[:8]}…")
            except Exception as exc:
                QMessageBox.warning(self, "Avatar", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            aid = self.tree.selected_payload() or getattr(self, "_editing_id", None)
            if not aid:
                return
            try:
                self.controller.remove_avatar(aid)
                self._editing_id = None
            except Exception as exc:
                QMessageBox.warning(self, "Avatar", str(exc))

    return AvatarTab(parent)
