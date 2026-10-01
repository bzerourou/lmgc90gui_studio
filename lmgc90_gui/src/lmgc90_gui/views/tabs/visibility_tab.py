"""VisibilityTab — see tables as QTreeWidget CRUD.

P1 facilitation:
  • Corps candidat / antagoniste : combobox selon dimension (2D/3D)
  • Shape / Color : combobox **éditables** remplies depuis les avatars du projet
  • Law : combobox des lois Contact déjà définies
"""
from __future__ import annotations

from lmgc90_core import ValidationError, VisibilityRule, pre
from lmgc90_core.types import (
    CONTACTORS_MESH_2D,
    CONTACTORS_MESH_3D,
    CONTACTORS_RIGID_2D,
    CONTACTORS_RIGID_3D,
    AvatarType,
)
from lmgc90_core.validate import compatible_contactors

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree

_BODY_2D = ("RBDY2", "MAILx", "MBS2D")
_BODY_3D = ("RBDY3", "MAILx", "MBS3D")

_COMMON_COLORS = ("BLUEx", "REDxx", "GREEx", "GRAYx", "ORANx", "YELLO", "VERTx")

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
    """Contacteurs réels sur l'avatar, ou formes compatibles par défaut."""
    out: list[str] = []
    for cont in getattr(av, "contactors", None) or []:
        if isinstance(cont, dict):
            sh = (cont.get("shape") or "").strip()
            try:
                valid = compatible_contactors(av.avatar_type, len(av.center))
            except (AttributeError, TypeError, ValidationError):
                valid = ()
            if sh and sh in valid:
                out.append(sh)
    if out:
        return list(dict.fromkeys(out))
    atype = _as_avatar_type(getattr(av, "avatar_type", None))
    try:
        return _default_contactors_for_type(atype, len(av.center))
    except (AttributeError, TypeError):
        return []


def _as_avatar_type(value) -> AvatarType | None:
    if isinstance(value, AvatarType):
        return value
    try:
        return AvatarType(str(value))
    except (TypeError, ValueError):
        return None


def _default_contactors_for_type(atype: AvatarType | None, dimension: int) -> list[str]:
    try:
        if atype == AvatarType.MESH_DEFORMABLE:
            return list(compatible_contactors(atype, dimension))
        supported = set(compatible_contactors(atype, dimension)) if atype else set()
    except ValidationError:
        return []
    return [shape for shape in _AVATAR_CONTACTORS.get(atype, ()) if shape in supported]


def _body_for_avatar(avatar, project_dimension: int) -> str:
    atype = _as_avatar_type(getattr(avatar, "avatar_type", None))
    if atype == AvatarType.MESH_DEFORMABLE:
        return "MAILx"
    center = getattr(avatar, "center", None) or ()
    dimension = len(center) if len(center) in (2, 3) else project_dimension
    return "RBDY2" if dimension == 2 else "RBDY3"


def _role_for_contact(atype: AvatarType | None, shape: str) -> str:
    if atype in (
        AvatarType.SMOOTH_WALL, AvatarType.ROUGH_WALL, AvatarType.FINE_WALL,
        AvatarType.GRANULO_WALL, AvatarType.RIGID_PLAN, AvatarType.ROUGH_WALL_3D,
        AvatarType.GRANULO_ROUGH_WALL_3D,
    ):
        return "antagonist"
    if atype in (AvatarType.EMPTY_AVATAR, AvatarType.MESH_DEFORMABLE):
        return "both"
    if shape in _ANTAGONIST_SHAPES and shape not in _CANDIDATE_SHAPES:
        return "both"
    return "candidate"


def _project_contact_options(project) -> list[tuple[str, str, str, str]]:
    """Unique (body, shape, color, role) combinations actually present."""
    dimension = int(getattr(project, "dimension", 2) or 2)
    rows: list[tuple[str, str, str, str]] = []
    for avatar in getattr(project, "avatars", []) or []:
        atype = _as_avatar_type(getattr(avatar, "avatar_type", None))
        body = _body_for_avatar(avatar, dimension)
        base_color = (getattr(avatar, "color", None) or "").strip() or "BLUEx"
        contactors = [c for c in (getattr(avatar, "contactors", None) or []) if isinstance(c, dict)]
        if contactors:
            contacts = [
                (
                    (contact.get("shape") or "").strip(),
                    (contact.get("color") or base_color).strip() or base_color,
                )
                for contact in contactors
            ]
            contacts = [
                (shape, color) for shape, color in contacts
                if shape and shape in _contactors_for_avatar(avatar)
            ]
        else:
            contacts = [(shape, base_color) for shape in _contactors_for_avatar(avatar)]
        for shape, color in contacts:
            rows.append((body, shape, color, _role_for_contact(atype, shape)))

    for population in getattr(project, "populations", []) or []:
        atype = _as_avatar_type(getattr(population, "avatar_type", None))
        dimension = int(getattr(population, "dimension", dimension) or dimension)
        body = "RBDY2" if dimension == 2 else "RBDY3"
        color = (getattr(population, "color", None) or "").strip() or "BLUEx"
        shapes = _default_contactors_for_type(atype, dimension)
        for shape in shapes:
            rows.append((body, shape, color, _role_for_contact(atype, shape)))

    return list(dict.fromkeys(rows))


def _project_avatar_pairs(project) -> list[tuple[str, str, str]]:
    """Liste (color, shape, role) role in candidate|antagonist|both."""
    return [
        (color, shape, role)
        for _body, shape, color, role in _project_contact_options(project)
    ]


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
    for c in _COMMON_COLORS:
        add(c)
    return colors


def _project_shapes(project, *, role: str = "both") -> list[str]:
    """Formes présentes dans le projet et compatibles avec le rôle demandé."""
    shapes = list(dict.fromkeys(
        shape
        for _body, shape, _color, option_role in _project_contact_options(project)
        if role == "both" or option_role in (role, "both")
    ))
    if shapes:
        return shapes

    dimension = int(getattr(project, "dimension", 2) or 2)
    body = "RBDY2" if dimension == 2 else "RBDY3"
    return _fallback_shapes(body, dimension)


def _body_options(project) -> list[str]:
    dim = int(getattr(project, "dimension", 2) or 2)
    rigid_body = "RBDY2" if dim == 2 else "RBDY3"
    valid_for_dimension = set(_BODY_2D if dim == 2 else _BODY_3D)
    options = list(dict.fromkeys(body for body, _shape, _color, _role in _project_contact_options(project)))
    for rule in getattr(project, "visibility", []) or []:
        options.extend((rule.candidate_body, rule.antagonist_body))
    return [rigid_body] + [
        body for body in dict.fromkeys(options)
        if body in valid_for_dimension and body != rigid_body
    ]


def _fallback_shapes(body: str, dimension: int) -> list[str]:
    if body == "MAILx":
        return list(CONTACTORS_MESH_2D if dimension == 2 else CONTACTORS_MESH_3D)
    if body in ("MBS2D", "MBS3D"):
        return list(CONTACTORS_RIGID_2D if dimension == 2 else CONTACTORS_RIGID_3D)
    return list(CONTACTORS_RIGID_2D if dimension == 2 else CONTACTORS_RIGID_3D)


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
                "See tables — formes et couleurs proposées d’après les avatars/contacteurs "
                "du projet. Une combinaison personnalisée non reconnue demande confirmation."
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

            self.c_body.currentTextChanged.connect(
                lambda _text: self._refresh_side("candidate", reset_shape=True, reset_color=True)
            )
            self.a_body.currentTextChanged.connect(
                lambda _text: self._refresh_side("antagonist", reset_shape=True, reset_color=True)
            )
            self.c_shape.currentTextChanged.connect(
                lambda _text: self._refresh_side("candidate", reset_color=True)
            )
            self.a_shape.currentTextChanged.connect(
                lambda _text: self._refresh_side("antagonist", reset_color=True)
            )
            self.c_shape.setToolTip("Formes de contact compatibles présentes sur les corps candidats du projet")
            self.a_shape.setToolTip("Formes de contact compatibles présentes sur les corps antagonistes du projet")
            self.c_color.setToolTip("Couleurs réellement associées à la forme candidate sélectionnée")
            self.a_color.setToolTip("Couleurs réellement associées à la forme antagoniste sélectionnée")

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

            self._refill_body_combos()
            self._refill_from_project()
            self._fill_combo(self.behav, _project_laws(self.controller.project) if self.controller else ["IQS_CLB"], "")

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
            self._refill_body_combos()
            self._refresh_side("candidate")
            self._refresh_side("antagonist")
            laws = _project_laws(pr)
            self._fill_combo(self.behav, laws, self._combo_text(self.behav) or laws[0])

        def _refresh_side(
            self,
            side: str,
            *,
            reset_shape: bool = False,
            reset_color: bool = False,
        ) -> None:
            if self.controller is None:
                return
            candidate = side == "candidate"
            body_box = self.c_body if candidate else self.a_body
            shape_box = self.c_shape if candidate else self.a_shape
            color_box = self.c_color if candidate else self.a_color
            requested_role = "candidate" if candidate else "antagonist"
            body = body_box.currentText().strip()
            options = [
                option for option in _project_contact_options(self.controller.project)
                if option[0] == body and option[3] in (requested_role, "both")
            ]
            shape_items = list(dict.fromkeys(option[1] for option in options))
            if not shape_items:
                shape_items = _fallback_shapes(
                    body, int(self.controller.project.dimension)
                )
            old_shape = shape_box.currentText().strip()
            shape = shape_items[0] if reset_shape or old_shape not in shape_items else old_shape
            self._fill_combo(shape_box, shape_items, shape)

            matching_colors = list(dict.fromkeys(
                option[2] for option in options if option[1] == shape
            ))
            old_color = color_box.currentText().strip()
            if not matching_colors:
                matching_colors = list(_COMMON_COLORS)
            color = (
                matching_colors[0]
                if reset_color or (old_color and old_color not in matching_colors)
                else old_color or matching_colors[0]
            )
            self._fill_combo(color_box, matching_colors, color)

        def _refill_body_combos(self, default_dim: int = 2) -> None:
            dim = default_dim
            if self.controller is not None:
                dim = int(getattr(self.controller.project, "dimension", default_dim) or default_dim)
            items = _body_options(self.controller.project) if self.controller is not None else list(
                _BODY_2D if dim == 2 else _BODY_3D
            )
            for box in (self.c_body, self.a_body):
                cur = box.currentText() if box.count() else ""
                box.blockSignals(True)
                box.clear()
                box.addItems(items)
                if cur and box.findText(cur) >= 0:
                    box.setCurrentText(cur)
                else:
                    box.setCurrentText("RBDY2" if dim == 2 else "RBDY3")
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
            self._validate_color(self._combo_text(self.c_color), "candidate")
            self._validate_color(self._combo_text(self.a_color), "antagonist")
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

        @staticmethod
        def _validate_color(color: str, role: str) -> None:
            if len(color) != 5:
                raise ValidationError(
                    f"La couleur {role} doit contenir exactement 5 caractères (code LMGC90)."
                )

        def _confirm_unmatched_options(self) -> bool:
            if self.controller is None:
                return True
            project = self.controller.project
            if not (project.avatars or project.populations):
                return True
            options = _project_contact_options(project)
            pairs = (
                ("candidat", self._body_text(self.c_body), self._combo_text(self.c_shape), self._combo_text(self.c_color), "candidate"),
                ("antagoniste", self._body_text(self.a_body), self._combo_text(self.a_shape), self._combo_text(self.a_color), "antagonist"),
            )
            missing = []
            for label, body, shape, color, role in pairs:
                if not any(
                    item_body == body
                    and item_shape == shape
                    and item_color == color
                    and item_role in (role, "both")
                    for item_body, item_shape, item_color, item_role in options
                ):
                    missing.append(f"{label} : {body} / {shape} / {color}")
            if not missing:
                return True
            answer = QMessageBox.question(
                self,
                "Combinaison non proposée par le projet",
                "Au moins une combinaison ne correspond à aucun avatar/contacteur "
                "actuellement présent :\n\n"
                + "\n".join(missing)
                + "\n\nVoulez-vous tout de même ajouter cette règle ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            return answer == QMessageBox.StandardButton.Yes

        def _on_add(self) -> None:
            try:
                rule = self._build()
                if not self._confirm_unmatched_options():
                    return
                self.controller.add_visibility(rule)
                self._clear_form()
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "Visibility", str(e))

        def _on_update(self) -> None:
            if self._editing_index is None:
                QMessageBox.information(self, "Visibility", "Sélectionnez une ligne")
                return
            try:
                rule = self._build()
                if not self._confirm_unmatched_options():
                    return
                self.controller.update_visibility(self._editing_index, rule)
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
