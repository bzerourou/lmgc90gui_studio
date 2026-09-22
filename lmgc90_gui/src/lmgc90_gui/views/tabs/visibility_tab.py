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
# AvatarType → contactor(s) LMGC90 (aligné avatar_tab / pre)
# Candidat = corps « mobile » qui peut s'approcher
# Antagoniste = corps non pénétrable (mur JONCx, plan, sol, …)
_AVATAR_CONTACTORS: dict[AvatarType, tuple[str, ...]] = {
    AvatarType.RIGID_DISK: ("DISKx",),
    AvatarType.RIGID_SPHERE: ("SPHER",),
    AvatarType.RIGID_DISCRETE: ("DISKx",),
    AvatarType.RIGID_JONC: ("JONCx",),
    AvatarType.RIGID_POLYGON: ("POLYG",),
    AvatarType.RIGID_OVOID: ("DISKx",),
    AvatarType.RIGID_CLUSTER: ("DISKx",),
    AvatarType.RIGID_CYLINDER: ("CYLND",),
    AvatarType.RIGID_PLAN: ("PLANx",),
    AvatarType.RIGID_POLYHEDRON: ("POLYR",),
    AvatarType.SMOOTH_WALL: ("JONCx",),
    AvatarType.ROUGH_WALL: ("JONCx",),
    AvatarType.FINE_WALL: ("JONCx",),
    AvatarType.GRANULO_WALL: ("JONCx",),
    AvatarType.ROUGH_WALL_3D: ("PLANx",),
    AvatarType.GRANULO_ROUGH_WALL_3D: ("PLANx",),
    AvatarType.EMPTY_AVATAR: ("POLYG", "PT3Dx", "PT2Dx"),
    AvatarType.MESH_DEFORMABLE: ("CLxxx", "ALpxx", "CSpxx", "ASpxx", "PT2Dx", "PT3Dx"),
}

# Contacteurs typiquement *antagonistes* (obstacles non pénétrables)
_ANTAGONIST_SHAPES = frozenset({
    "JONCx", "PLANx", "POLYG", "POLYR", "CLxxx", "ALpxx", "CSpxx", "ASpxx",
})
# Contacteurs typiquement *candidats* (grains / mobiles)
_CANDIDATE_SHAPES = frozenset({
    "DISKx", "xKSID", "SPHER", "CYLND", "PT2Dx", "PT3Dx",
})


def _contactors_for_avatar(av) -> list[str]:
    """Contacteurs réels sur l'avatar, sinon défauts selon AvatarType."""
    out: list[str] = []
    for cont in getattr(av, "contactors", None) or []:
        if isinstance(cont, dict):
            sh = (cont.get("shape") or "").strip()
            if sh:
                out.append(sh)
    if out:
        return out
    t = getattr(av, "avatar_type", None)
    if t in _AVATAR_CONTACTORS:
        return list(_AVATAR_CONTACTORS[t])
    return []


def _project_avatar_pairs(project) -> list[tuple[str, str, str]]:
    """Liste (color, shape, role) role in candidate|antagonist|both."""
    rows: list[tuple[str, str, str]] = []
    for av in getattr(project, "avatars", []) or []:
        color = (getattr(av, "color", None) or "").strip() or "BLUEx"
        shapes = _contactors_for_avatar(av)
        t = getattr(av, "avatar_type", None)
        name = getattr(t, "value", str(t) if t else "")
        is_wall = any(k in name.lower() for k in ("wall", "jonc", "plan"))
        for sh in shapes or ["DISKx"]:
            if is_wall or sh in _ANTAGONIST_SHAPES and sh not in _CANDIDATE_SHAPES:
                role = "antagonist"
            elif sh in _CANDIDATE_SHAPES:
                role = "candidate"
            else:
                role = "both"
            rows.append((color, sh, role))
    for pop in getattr(project, "populations", []) or []:
        color = (getattr(pop, "color", None) or "").strip() or "BLUEx"
        at = getattr(pop, "avatar_type", None)
        if hasattr(at, "value"):
            key = at
        else:
            try:
                key = AvatarType(str(at))
            except Exception:
                key = None
        shapes = list(_AVATAR_CONTACTORS.get(key, ("DISKx", "SPHER")))
        for sh in shapes:
            rows.append((color, sh, "candidate"))
    return rows


def _project_colors(project) -> list[str]:
    colors: list[str] = []
    seen: set[str] = set()

    def add(c: str) -> None:
        c = (c or "").strip()
        if c and c not in seen:
            seen.add(c)
            colors.append(c)

    for color, _sh, _role in _project_avatar_pairs(project):
        add(color)
    for c in ("BLUEx", "REDxx", "GREEx", "GRAYx", "ORANx", "YELLO", "VERTx"):
        add(c)
    return colors


def _project_shapes(project, *, role: str = "both") -> list[str]:
    """Shapes proposées ; role=candidate|antagonist|both (ordre métier)."""
    shapes: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = (s or "").strip()
        if s and s not in seen:
            seen.add(s)
            shapes.append(s)

    pairs = _project_avatar_pairs(project)
    # first: shapes matching requested role from real avatars
    for _color, sh, r in pairs:
        if role == "both" or r == role or r == "both":
            add(sh)
    # preferred order boost for antagonist
    if role == "antagonist":
        for pref in ("JONCx", "PLANx", "POLYG", "POLYR"):
            if pref in seen:
                # move to front
                if pref in shapes:
                    shapes.remove(pref)
                    shapes.insert(0, pref)
            else:
                add(pref)
    if role == "candidate":
        for pref in ("DISKx", "SPHER", "CYLND", "PT2Dx", "PT3Dx"):
            if pref not in seen:
                add(pref)
            elif pref in shapes:
                shapes.remove(pref)
                shapes.insert(0, pref)

    dim = int(getattr(project, "dimension", 2) or 2)
    for s in (_SHAPES_2D if dim == 2 else _SHAPES_3D):
        add(s)
    return shapes


def _project_laws(project) -> list[str]:
    names = [law.name for law in (getattr(project, "laws", None) or []) if law.name]
    if not names:
        names = ["IQS", "IQS_CLB", "iqsc0"]
    return names


def validate_visibility_project(project) -> list[str]:
    """Soft checks: orphan colors, unused laws, unknown law refs. Returns messages."""
    msgs: list[str] = []
    colors_used = set(_project_colors(project))
    # strip fallback palette noise for orphan check — only colors on real entities
    real_colors: set[str] = set()
    for av in getattr(project, "avatars", []) or []:
        c = (getattr(av, "color", None) or "").strip()
        if c:
            real_colors.add(c)
        for cont in getattr(av, "contactors", None) or []:
            if isinstance(cont, dict):
                cc = (cont.get("color") or "").strip()
                if cc:
                    real_colors.add(cc)
    for pop in getattr(project, "populations", []) or []:
        c = (getattr(pop, "color", None) or "").strip()
        if c:
            real_colors.add(c)

    see_colors: set[str] = set()
    see_laws: set[str] = set()
    for r in getattr(project, "visibility", []) or []:
        see_colors.add((r.candidate_color or "").strip())
        see_colors.add((r.antagonist_color or "").strip())
        see_laws.add((r.behavior_name or "").strip())

    law_names = {law.name for law in (getattr(project, "laws", None) or [])}

    for c in sorted(real_colors):
        if c and c not in see_colors:
            msgs.append(f"Couleur « {c} » sur un avatar/population sans see-table")

    for law in sorted(law_names):
        if law and law not in see_laws:
            msgs.append(f"Loi « {law} » jamais référencée dans une see-table")

    for name in sorted(see_laws):
        if name and name not in law_names:
            msgs.append(f"See-table référence la loi inconnue « {name} »")

    if not getattr(project, "visibility", None):
        if real_colors:
            msgs.append("Aucune see-table définie alors que le projet a des avatars")

    return msgs




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
                ("Shape candidat (mobile)", self.c_shape),
                ("Color candidat", self.c_color),
                ("Corps antagoniste", self.a_body),
                ("Shape antagoniste (obstacle)", self.a_shape),
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
                ("⚡ Grains↔grains", self._preset_grain_grain),
                ("⚡ Grains↔sol", self._preset_grain_wall),
                ("⚠ Vérifier", self._on_validate),
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
            shapes_c = _project_shapes(pr, role="candidate")
            shapes_a = _project_shapes(pr, role="antagonist")
            colors = _project_colors(pr)
            laws = _project_laws(pr)
            dim = int(getattr(pr, "dimension", 2) or 2)
            default_c = "SPHER" if dim == 3 else "DISKx"
            default_a = "PLANx" if dim == 3 else "JONCx"
            self._fill_combo(
                self.c_shape, shapes_c,
                self._combo_text(self.c_shape) or (shapes_c[0] if shapes_c else default_c),
            )
            self._fill_combo(
                self.a_shape, shapes_a,
                self._combo_text(self.a_shape) or (shapes_a[0] if shapes_a else default_a),
            )
            # colors: candidate prefers grain-like, antagonist wall-like if possible
            cand_colors = [c for c, sh, r in _project_avatar_pairs(pr) if r in ("candidate", "both")]
            ant_colors = [c for c, sh, r in _project_avatar_pairs(pr) if r in ("antagonist", "both")]
            if not cand_colors:
                cand_colors = colors
            if not ant_colors:
                ant_colors = colors
            # unique preserve order
            def uniq(seq):
                out, seen = [], set()
                for x in seq:
                    if x not in seen:
                        seen.add(x)
                        out.append(x)
                return out
            cand_colors = uniq(cand_colors + colors)
            ant_colors = uniq(ant_colors + colors)
            self._fill_combo(
                self.c_color, cand_colors,
                self._combo_text(self.c_color) or (cand_colors[0] if cand_colors else "BLUEx"),
            )
            self._fill_combo(
                self.a_color, ant_colors,
                self._combo_text(self.a_color) or (ant_colors[0] if ant_colors else "GRAYx"),
            )
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


        def _apply_quick_see(self, shape_c: str, color_c: str, shape_a: str, color_a: str,
                             law: str | None = None, alert: float = 0.05) -> None:
            if self.controller is None:
                return
            pr = self.controller.project
            laws = _project_laws(pr)
            behav = law or (laws[0] if laws else "IQS")
            body = self._default_body()
            try:
                rule = pre.see_table(
                    CorpsCandidat=body,
                    candidat=shape_c,
                    colorCandidat=color_c,
                    CorpsAntagoniste=body,
                    antagoniste=shape_a,
                    colorAntagoniste=color_a,
                    behav=behav,
                    alert=alert,
                )
                self.controller.add_visibility(rule)
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "Preset", str(e))

        def _preset_grain_grain(self) -> None:
            if self.controller is None:
                return
            dim = int(self.controller.project.dimension)
            shape = "SPHER" if dim == 3 else "DISKx"
            colors = _project_colors(self.controller.project)
            # prefer non-gray particle-like colors
            col = "BLUEx"
            for c in colors:
                if c not in ("GRAYx", "SUBST", "NOEUx") and not c.startswith("I0"):
                    col = c
                    break
            self._apply_quick_see(shape, col, shape, col, alert=0.05)

        def _preset_grain_wall(self) -> None:
            if self.controller is None:
                return
            dim = int(self.controller.project.dimension)
            grain = "SPHER" if dim == 3 else "DISKx"
            colors = _project_colors(self.controller.project)
            gcol = "BLUEx"
            for c in colors:
                if c not in ("GRAYx", "SUBST") and not c.startswith("I0"):
                    gcol = c
                    break
            wcol = "GRAYx" if "GRAYx" in colors else (colors[-1] if colors else "GRAYx")
            for c in colors:
                if c in ("GRAYx", "SUBST", "ORANx", "REDxx"):
                    wcol = c
                    break
            self._apply_quick_see(grain, gcol, "JONCx", wcol, alert=0.05)

        def _on_validate(self) -> None:
            if self.controller is None:
                return
            msgs = validate_visibility_project(self.controller.project)
            if not msgs:
                QMessageBox.information(
                    self, "Visibility",
                    "Aucune anomalie détectée.\n"
                    "Couleurs couvertes et lois référencées coherentement.",
                )
                return
            text = "\n".join(f"• {m}" for m in msgs[:30])
            if len(msgs) > 30:
                text += f"\n… (+{len(msgs) - 30} autres)"
            QMessageBox.warning(self, "Vérification see-tables", text)

        def _on_link_ab(self) -> None:
            if self.controller is None:
                return
            from ...dialogs.link_visibility_dialog import create_link_visibility_dialog
            dlg = create_link_visibility_dialog(self.controller, self)
            if dlg.exec():
                # tree refresh via state_changed
                pass

    return VisibilityTab(parent)
