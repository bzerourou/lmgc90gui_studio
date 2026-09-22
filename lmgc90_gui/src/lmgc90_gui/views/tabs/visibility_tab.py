"""VisibilityTab — see tables as QTreeWidget CRUD.

P1 facilitation:
  • Corps candidat / antagoniste : combobox selon dimension (2D/3D)
  • Shape / Color : combobox **éditables** remplies depuis les avatars du projet
  • Law : combobox des lois Contact déjà définies
"""
from __future__ import annotations

from lmgc90_core import ValidationError, VisibilityRule, pre
from lmgc90_core.types import AvatarType

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree

_BODY_2D = ("RBDY2", "MAILx", "MBS2D")
_BODY_3D = ("RBDY3", "MAILx", "MBS3D")
_BODY_ALL = ("RBDY2", "RBDY3", "MAILx", "MBS2D", "MBS3D")

# Fallback shapes if project is empty
_SHAPES_2D = ("DISKx", "JONCx", "POLYG", "CLxxx", "ALpxx", "PT2Dx")
_SHAPES_3D = ("SPHER", "CYLND", "POLYR", "PT3Dx", "CSpxx", "ASpxx")
_SHAPES_ALL = tuple(dict.fromkeys(_SHAPES_2D + _SHAPES_3D))

# AvatarType → contactor shape hint
_TYPE_SHAPE = {
    AvatarType.RIGID_DISK: "DISKx",
    AvatarType.RIGID_SPHERE: "SPHER",
    AvatarType.RIGID_JONC: "JONCx",
    AvatarType.RIGID_PLAN: "PLANx",
    AvatarType.RIGID_CYLINDER: "CYLND",
    AvatarType.RIGID_POLYGON: "POLYG",
    AvatarType.RIGID_POLYHEDRON: "POLYR",
    AvatarType.RIGID_CLUSTER: "DISKx",
    AvatarType.EMPTY_AVATAR: "POLYG",
    AvatarType.MESH_DEFORMABLE: "CLxxx",
    AvatarType.ROUGH_WALL: "JONCx",
    AvatarType.SMOOTH_WALL: "JONCx",
}


def _project_colors(project) -> list[str]:
    colors: list[str] = []
    seen: set[str] = set()

    def add(c: str) -> None:
        c = (c or "").strip()
        if c and c not in seen:
            seen.add(c)
            colors.append(c)

    for av in getattr(project, "avatars", []) or []:
        add(getattr(av, "color", None) or "")
        for cont in getattr(av, "contactors", None) or []:
            if isinstance(cont, dict):
                add(cont.get("color") or "")
    for pop in getattr(project, "populations", []) or []:
        add(getattr(pop, "color", None) or "")
    # common LMGC defaults last
    for c in ("BLUEx", "REDxx", "GREEx", "GRAYx", "ORANx", "YELLO", "VERTx", "NOEUx"):
        add(c)
    return colors


def _project_shapes(project) -> list[str]:
    shapes: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = (s or "").strip()
        if s and s not in seen:
            seen.add(s)
            shapes.append(s)

    for av in getattr(project, "avatars", []) or []:
        for cont in getattr(av, "contactors", None) or []:
            if isinstance(cont, dict):
                add(cont.get("shape") or "")
        t = getattr(av, "avatar_type", None)
        if t in _TYPE_SHAPE:
            add(_TYPE_SHAPE[t])
        # rough / smooth wall often JONCx even without explicit contactor
        name = getattr(t, "value", str(t) if t else "")
        if "wall" in name.lower() or "jonc" in name.lower():
            add("JONCx")
        if "disk" in name.lower():
            add("DISKx")
        if "sphere" in name.lower():
            add("SPHER")
    dim = int(getattr(project, "dimension", 2) or 2)
    for s in (_SHAPES_2D if dim == 2 else _SHAPES_3D):
        add(s)
    return shapes


def _project_laws(project) -> list[str]:
    names = [law.name for law in (getattr(project, "laws", None) or []) if law.name]
    if not names:
        names = ["IQS", "IQS_CLB", "iqsc0"]
    return names


def create_visibility_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
        QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class VisibilityTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_index: int | None = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "See tables — shapes / couleurs / lois proposés depuis le projet "
                "(listes éditables : vous pouvez encore saisir une valeur libre)"
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

            self.c_shape = QComboBox()
            self.c_shape.setEditable(True)
            self.a_shape = QComboBox()
            self.a_shape.setEditable(True)
            self.c_color = QComboBox()
            self.c_color.setEditable(True)
            self.a_color = QComboBox()
            self.a_color.setEditable(True)
            self.behav = QComboBox()
            self.behav.setEditable(True)

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
                ("↻ Listes", self._refill_from_project),
                ("🔗 Lier A ↔ B", self._on_link_ab),
            ):
                b = QPushButton(text)
                b.clicked.connect(slot)
                row.addWidget(b)
            layout.addLayout(row)

            # initial fallbacks
            self._fill_combo(self.c_shape, list(_SHAPES_2D), "DISKx")
            self._fill_combo(self.a_shape, list(_SHAPES_2D), "DISKx")
            self._fill_combo(self.c_color, ["BLUEx", "REDxx", "GRAYx"], "BLUEx")
            self._fill_combo(self.a_color, ["BLUEx", "REDxx", "GRAYx"], "BLUEx")
            self._fill_combo(self.behav, ["IQS", "IQS_CLB"], "IQS")

        # ----- combo helpers -----
        @staticmethod
        def _fill_combo(box, items: list[str], current: str | None = None) -> None:
            cur = (current if current is not None else box.currentText()).strip()
            box.blockSignals(True)
            box.clear()
            for it in items:
                box.addItem(it)
            if cur:
                idx = box.findText(cur)
                if idx >= 0:
                    box.setCurrentIndex(idx)
                else:
                    box.setEditText(cur)
            box.blockSignals(False)

        def _combo_text(self, box: QComboBox) -> str:
            return box.currentText().strip()

        def _refill_from_project(self) -> None:
            if self.controller is None:
                return
            pr = self.controller.project
            shapes = _project_shapes(pr)
            colors = _project_colors(pr)
            laws = _project_laws(pr)
            self._fill_combo(self.c_shape, shapes, self._combo_text(self.c_shape) or "DISKx")
            self._fill_combo(self.a_shape, shapes, self._combo_text(self.a_shape) or "DISKx")
            self._fill_combo(self.c_color, colors, self._combo_text(self.c_color) or (colors[0] if colors else "BLUEx"))
            self._fill_combo(self.a_color, colors, self._combo_text(self.a_color) or (colors[0] if colors else "BLUEx"))
            self._fill_combo(self.behav, laws, self._combo_text(self.behav) or (laws[0] if laws else "IQS"))

        def _refill_body_combos(self, default_dim: int = 2) -> None:
            dim = default_dim
            if self.controller is not None:
                dim = int(getattr(self.controller.project, "dimension", default_dim) or default_dim)
            items = list(_BODY_2D if dim == 2 else _BODY_3D)
            # keep exotic values available at end
            for extra in _BODY_ALL:
                if extra not in items:
                    items.append(extra)
            for box in (self.c_body, self.a_body):
                cur = box.currentText() if box.count() else ""
                box.blockSignals(True)
                box.clear()
                box.addItems(items)
                if cur and box.findText(cur) >= 0:
                    box.setCurrentText(cur)
                else:
                    box.setCurrentIndex(0)
                box.blockSignals(False)

        def _default_body(self) -> str:
            if self.controller is not None and int(self.controller.project.dimension) == 3:
                return "RBDY3"
            return "RBDY2"

        def _set_combo(self, box: QComboBox, value: str) -> None:
            value = (value or "").strip()
            if not value:
                return
            idx = box.findText(value)
            if idx >= 0:
                box.setCurrentIndex(idx)
            elif box.isEditable():
                box.setEditText(value)
            else:
                box.addItem(value)
                box.setCurrentText(value)

        def _body_text(self, box: QComboBox) -> str:
            return box.currentText().strip() or self._default_body()

        # ----- BaseTab -----
        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            self._refill_body_combos()
            self._refill_from_project()
            rows = []
            for i, r in enumerate(self.controller.project.visibility):
                rows.append((
                    [str(i), r.candidate_body, r.candidate_contactor, r.candidate_color,
                     r.antagonist_body, r.antagonist_contactor, r.antagonist_color,
                     r.behavior_name, f"{r.alert:g}"],
                    i,
                ))
            self.tree.set_rows(rows)

        def _load_selected(self, index: int) -> None:
            if self.controller is None:
                return
            if not (0 <= index < len(self.controller.project.visibility)):
                return
            r = self.controller.project.visibility[index]
            self._editing_index = index
            self._refill_from_project()
            self._set_combo(self.c_body, r.candidate_body)
            self._set_combo(self.c_shape, r.candidate_contactor)
            self._set_combo(self.c_color, r.candidate_color)
            self._set_combo(self.a_body, r.antagonist_body)
            self._set_combo(self.a_shape, r.antagonist_contactor)
            self._set_combo(self.a_color, r.antagonist_color)
            self._set_combo(self.behav, r.behavior_name)
            self.alert.setValue(float(r.alert))

        def _clear_form(self) -> None:
            self._editing_index = None
            self.tree.clearSelection()
            d = self._default_body()
            self._set_combo(self.c_body, d)
            self._set_combo(self.a_body, d)
            self._refill_from_project()

        def _build(self) -> VisibilityRule:
            return pre.see_table(
                CorpsCandidat=self._body_text(self.c_body),
                candidat=self._combo_text(self.c_shape),
                colorCandidat=self._combo_text(self.c_color),
                CorpsAntagoniste=self._body_text(self.a_body),
                antagoniste=self._combo_text(self.a_shape),
                colorAntagoniste=self._combo_text(self.a_color),
                behav=self._combo_text(self.behav),
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

        def _on_link_ab(self) -> None:
            if self.controller is None:
                return
            from ...dialogs.link_visibility_dialog import create_link_visibility_dialog
            dlg = create_link_visibility_dialog(self.controller, self)
            if dlg.exec():
                # tree refresh via state_changed
                pass

    return VisibilityTab(parent)
