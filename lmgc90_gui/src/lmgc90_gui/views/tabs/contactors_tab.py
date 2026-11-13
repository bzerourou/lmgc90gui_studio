"""ContactorsTab — manage contactors on a selected avatar (esp. emptyAvatar / mesh)."""
from __future__ import annotations

import ast

from lmgc90_core import LMGC90Error, ValidationError
from lmgc90_core.types import (
    AvatarType, CONTACTORS_MESH_2D, CONTACTORS_MESH_3D,
)
from lmgc90_core.validate import compatible_contactors
from lmgc90_engine.schema import (
    contactor_schema_catalog, contactors_for_body_type,
)

from .base_tab import BaseTab
from ...utils.safe_eval import safe_eval


_CONTACTOR_PARAMS: dict[str, tuple[tuple[str, str, object, str], ...]] = {
    "DISKx": (("byrd", "float", 0.1, "Contact radius"),),
    "xKSID": (("byrd", "float", 0.1, "Contact radius"),),
    "JONCx": (
        ("axe1", "float", 0.2, "Half-length along axis 1"),
        ("axe2", "float", 0.05, "Half-width along axis 2"),
    ),
    "POLYG": (
        ("generation_type", "choice", ("regular", "full"), "Generation method"),
    ),
    "PT2Dx": (),
    "SPHER": (("byrd", "float", 0.1, "Contact radius"),),
    "PLANx": (
        ("axe1", "float", 0.5, "Half-length along axis 1"),
        ("axe2", "float", 0.5, "Half-length along axis 2"),
        ("axe3", "float", 0.05, "Half-thickness"),
    ),
    "CYLND": (
        ("High", "float", 0.1, "Half-height"),
        ("byrd", "float", 0.1, "Contact radius"),
    ),
    "DNLYC": (
        ("High", "float", 0.1, "Half-height"),
        ("byrd", "float", 0.1, "Contact radius"),
    ),
    "POLYR": (
        ("generation_type", "choice", ("regular", "full"), "Generation method"),
    ),
    "PT3Dx": (),
}

_MESH_CONTACTORS = {"CLxxx", "ALpxx", "CSpxx", "ASpxx"}

_POLYGON_PARAMS = {
    ("POLYG", "regular"): (
        ("nb_vertices", "int", 6, "Number of vertices (minimum 3)"),
        ("radius", "float", 0.1, "Circumradius"),
    ),
    ("POLYG", "full"): (
        ("vertices", "vertices2d", "0.1,0.1; -0.1,0.1; -0.1,-0.1; 0.1,-0.1",
         "x,y rows separated by semicolons"),
    ),
    ("POLYR", "regular"): (
        ("nb_vertices", "int", 8, "Number of vertices (minimum 4)"),
        ("radius", "float", 0.1, "Circumsphere radius"),
    ),
    ("POLYR", "full"): (
        ("vertices", "vertices3d",
         "0.1,0.1,0.1; -0.1,-0.1,0.1; -0.1,0.1,-0.1; 0.1,-0.1,-0.1",
         "x,y,z rows separated by semicolons"),
        ("connectivity", "triangles",
         "[[1,2,3],[1,4,2],[2,4,3],[3,4,1]]",
         "Triangular face indices, numbered from 1"),
    ),
}


_POLYGON_OPTION_NAMES = {
    "POLYG": {"nb_vertices", "vertices"},
    "POLYR": {"nb_vertices", "vertices", "nb_faces", "connectivity"},
}


def _contactor_param_schema(
    shape: str,
    generation_type: str = "regular",
    *,
    options=(),
    optional_options=(),
    mesh_contactors=None,
):
    mesh_shapes = set(
        _MESH_CONTACTORS if mesh_contactors is None else mesh_contactors
    )
    schema = _CONTACTOR_PARAMS.get(shape, ())
    if shape in ("POLYG", "POLYR"):
        fields = (
            schema[0],
            *_POLYGON_PARAMS[(shape, generation_type)],
            ("shift", "shift", "", "Coordinates relative to the avatar center"),
        )
    elif shape in mesh_shapes:
        fields = schema
    else:
        fields = (
            *schema,
            ("shift", "shift", "", "Coordinates relative to the avatar center"),
        )

    field_names = {field[0] for field in fields}
    for name in (*options, *optional_options):
        if name in field_names or name in _POLYGON_OPTION_NAMES.get(shape, ()):
            continue
        fields = (*fields, (
            name, "auto", "", "Runtime option; leave blank to omit",
        ))
        field_names.add(name)
    return fields


def _read_contactor_params(
    shape: str,
    fields: dict[str, object],
    *,
    dimension: int = 2,
    evaluate_float=None,
    evaluate_expression=None,
    options=(),
    optional_options=(),
    mesh_contactors=None,
) -> dict[str, object]:
    """Convert the visible shape-specific form fields to pylmgc90 option values."""
    parsed: dict[str, object] = {}
    number = evaluate_float or (lambda expression, _name: float(expression))
    expression = evaluate_expression or ast.literal_eval
    generation_type = str(fields.get("generation_type", "regular"))
    if shape in ("POLYG", "POLYR") and generation_type not in ("regular", "full"):
        raise ValueError("generation_type must be 'regular' or 'full'")
    schemas = {
        name: kind
        for name, kind, _, _ in _contactor_param_schema(
            shape,
            generation_type,
            options=options,
            optional_options=optional_options,
            mesh_contactors=mesh_contactors,
        )
    }
    for name, raw_value in fields.items():
        if name not in schemas:
            continue
        kind = schemas[name]
        value = str(raw_value).strip()
        if kind in ("shift", "choice"):
            continue
        if kind == "float":
            evaluated = number(value, name)
            if evaluated <= 0:
                raise ValueError(f"{name} must be greater than zero")
            parsed[name] = evaluated
        elif kind == "int":
            evaluated = number(value, name)
            if not evaluated.is_integer():
                raise ValueError(f"{name} must be an integer")
            evaluated = int(evaluated)
            minimum = 3 if shape == "POLYG" else 4 if shape == "POLYR" else 1
            if evaluated < minimum:
                raise ValueError(f"{name} must be at least {minimum}")
            parsed[name] = evaluated
        elif kind in ("vertices2d", "vertices3d"):
            dimension = 2 if kind == "vertices2d" else 3
            rows = []
            for row in value.replace("\n", ";").split(";"):
                if row.strip():
                    coordinates = [
                        number(part, name)
                        for part in row.replace(",", " ").split()
                    ]
                    if len(coordinates) != dimension:
                        raise ValueError(
                            f"{name} needs {dimension} coordinates per vertex"
                        )
                    rows.append(coordinates)
            if len(rows) < dimension + 1:
                raise ValueError(f"{name} needs at least {dimension + 1} vertices")
            parsed[name] = rows
        elif kind == "auto":
            if not value:
                continue
            try:
                parsed[name] = expression(value)
            except (NameError, SyntaxError, TypeError, ValueError):
                parsed[name] = value
        elif kind == "triangles":
            faces = expression(value)
            if not isinstance(faces, list) or not faces:
                raise ValueError("connectivity must be a non-empty list of triangular faces")
            if any(not isinstance(face, (list, tuple)) or len(face) != 3 for face in faces):
                raise ValueError("each connectivity row must contain 3 vertex indices")
            parsed[name] = [
                [int(number(str(index), name)) for index in face] for face in faces
            ]
        else:
            parsed[name] = value

    if shape in ("POLYG", "POLYR"):
        parsed["generation_type"] = generation_type
    if shape == "POLYG" and generation_type == "full":
        parsed["nb_vertices"] = len(parsed["vertices"])
        vertices = parsed["vertices"]
        signed_area = sum(
            vertices[index - 1][0] * vertices[index][1]
            - vertices[index][0] * vertices[index - 1][1]
            for index in range(len(vertices))
        )
        if signed_area <= 0:
            raise ValueError("POLYG vertices must be listed counter-clockwise")
    if shape == "POLYR" and generation_type == "full":
        parsed["nb_vertices"] = len(parsed["vertices"])
        parsed["nb_faces"] = len(parsed["connectivity"])
        if any(
            index < 1 or index > parsed["nb_vertices"]
            for face in parsed["connectivity"] for index in face
        ):
            raise ValueError("connectivity indices must refer to the listed vertices")
    shift = fields.get("shift")
    if shift:
        coordinates = [
            number(part, "shift")
            for part in str(shift).replace(",", " ").split()
        ]
        if len(coordinates) != dimension:
            raise ValueError(f"shift must contain exactly {dimension} coordinates")
        parsed["shift"] = coordinates
    return parsed


def create_contactors_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
        QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )
    from ...utils.field_forms import clear_layout

    class ContactorsTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.contactor_catalog = contactor_schema_catalog()
            body_types = self.contactor_catalog["body_type_contactors"]
            if "MAILx" in body_types:
                self._mesh_contactors = set(body_types["MAILx"]) - set(
                    body_types.get("RBDY2", ()) + body_types.get("RBDY3", ())
                )
            else:
                rigid_shapes = set(
                    compatible_contactors(AvatarType.EMPTY_AVATAR, 2)
                    + compatible_contactors(AvatarType.EMPTY_AVATAR, 3)
                )
                self._mesh_contactors = set((
                    *CONTACTORS_MESH_2D, *CONTACTORS_MESH_3D,
                    *_MESH_CONTACTORS,
                )) - rigid_shapes
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Select avatar"))
            self.avatar_combo = QComboBox()
            self.avatar_combo.currentIndexChanged.connect(self._on_avatar_changed)
            layout.addWidget(self.avatar_combo)

            layout.addWidget(QLabel("Contactors on avatar"))
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.shape_combo = QComboBox()
            self.shape_combo.currentTextChanged.connect(self._on_shape_changed)
            self.color_edit = QLineEdit("BLUEx")
            self.bygroup_edit = QLineEdit()
            self.bygroup_edit.setPlaceholderText("mesh element group (e.g. down)")
            self.group_label = QLabel("Group")
            form.addRow("Shape", self.shape_combo)
            form.addRow("Color", self.color_edit)
            form.addRow(self.group_label, self.bygroup_edit)
            layout.addLayout(form)
            self._param_layout = QFormLayout()
            layout.addLayout(self._param_layout)
            self._param_fields: dict[str, object] = {}
            self._param_widgets: dict[str, object] = {}

            row = QHBoxLayout()
            btn_add = QPushButton("Add contactor")
            btn_rm = QPushButton("Remove selected")
            btn_add.clicked.connect(self._on_add)
            btn_rm.clicked.connect(self._on_remove)
            row.addWidget(btn_add)
            row.addWidget(btn_rm)
            layout.addLayout(row)
            layout.addWidget(QLabel(
                "Compatible shapes depend on avatar type and project dimension "
                "(validate.compatible_contactors)."
            ))

        def bind_controller(self, controller) -> None:
            super().bind_controller(controller)
            self.on_state_changed()

        def _compatible_shapes(self, avatar, dimension: int) -> tuple[str, ...]:
            body_type = (
                "MAILx"
                if avatar.avatar_type == AvatarType.MESH_DEFORMABLE
                else "RBDY2" if dimension == 2 else "RBDY3"
            )
            return contactors_for_body_type(
                self.contactor_catalog,
                body_type,
                dimension,
                compatible_contactors(avatar.avatar_type, dimension),
            )

        def _shape_options(self, shape: str) -> tuple[str, ...]:
            return tuple(self.contactor_catalog["options"].get(shape, ()))

        def _shape_optional_options(self, shape: str) -> tuple[str, ...]:
            return tuple(self.contactor_catalog["optional_options"].get(shape, ()))

        def _current_avatar(self):
            if self.controller is None:
                return None
            aid = self.avatar_combo.currentData()
            if not aid:
                return None
            for av in self.controller.project.avatars:
                if av.avatar_id == aid:
                    return av
            return None

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            cur = self.avatar_combo.currentData()
            self.avatar_combo.blockSignals(True)
            self.avatar_combo.clear()
            for av in p.avatars:
                self.avatar_combo.addItem(
                    f"{av.avatar_id[:8]}… {av.avatar_type.value}", av.avatar_id,
                )
            if cur is not None:
                idx = self.avatar_combo.findData(cur)
                if idx >= 0:
                    self.avatar_combo.setCurrentIndex(idx)
            self.avatar_combo.blockSignals(False)
            self._on_avatar_changed()

        def _on_avatar_changed(self) -> None:
            av = self._current_avatar()
            self.list.clear()
            self.shape_combo.clear()
            if av is None or self.controller is None:
                return
            for i, c in enumerate(av.contactors):
                shape = c.get("shape", "?")
                color = c.get("color", "")
                extra = " ".join(f"{k}={v}" for k, v in c.items() if k not in ("shape", "color"))
                self.list.addItem(f"[{i}] {shape}  {color}  {extra}".strip())
            dim = self.controller.project.dimension
            shapes = self._compatible_shapes(av, dim)
            self.shape_combo.addItems(list(shapes))
            # sensible default for emptyAvatar
            if av.avatar_type == AvatarType.EMPTY_AVATAR and "DISKx" in shapes:
                self.shape_combo.setCurrentText("DISKx")
            self._on_shape_changed(self.shape_combo.currentText())

        def _on_shape_changed(self, shape: str) -> None:
            if not shape:
                clear_layout(self._param_layout)
                self._param_fields = {}
                self.group_label.setVisible(False)
                self.bygroup_edit.setVisible(False)
                return
            if shape in ("POLYG", "POLYR"):
                self._build_polygon_fields(shape, "regular")
            else:
                clear_layout(self._param_layout)
                self._param_fields = {}
                schema = _contactor_param_schema(
                    shape,
                    options=self._shape_options(shape),
                    optional_options=self._shape_optional_options(shape),
                    mesh_contactors=self._mesh_contactors,
                )
                for name, kind, default, placeholder in schema:
                    if kind == "shift" and self.controller is not None:
                        dimension = self.controller.project.dimension
                        placeholder = (
                            f"{dimension}D offset, e.g. "
                            + ", ".join(["0.0"] * dimension)
                        )
                    if kind == "choice":
                        field = QComboBox()
                        field.addItems(list(default))
                        field.setCurrentIndex(0)
                    else:
                        field = QLineEdit(str(default))
                        field.setPlaceholderText(placeholder)
                        if kind in ("float", "int", "shift", "auto"):
                            self.mark_expr_field(field)
                    self._param_layout.addRow(name, field)
                    self._param_fields[name] = field
            is_mesh = shape in self._mesh_contactors
            self.group_label.setVisible(is_mesh)
            self.bygroup_edit.setVisible(is_mesh)

        def _on_generation_changed(self, shape: str, generation_type: str) -> None:
            self._build_polygon_fields(shape, generation_type)

        def _build_polygon_fields(self, shape: str, generation_type: str) -> None:
            previous_shift = self._param_fields.get("shift")
            shift_text = previous_shift.text() if previous_shift is not None else ""
            clear_layout(self._param_layout)
            self._param_fields = {}
            selector = QComboBox()
            selector.addItems(["regular", "full"])
            selector.setCurrentText(generation_type)
            selector.currentTextChanged.connect(
                lambda value, selected_shape=shape:
                self._on_generation_changed(selected_shape, value)
            )
            self._param_layout.addRow("generation_type", selector)
            self._param_fields["generation_type"] = selector
            schema = _contactor_param_schema(
                shape,
                generation_type,
                options=self._shape_options(shape),
                optional_options=self._shape_optional_options(shape),
                mesh_contactors=self._mesh_contactors,
            )
            for name, kind, default, placeholder in schema:
                if name == "generation_type":
                    continue
                if name == "shift":
                    default = shift_text
                field = QLineEdit(str(default))
                field.setPlaceholderText(placeholder)
                if kind in (
                    "float", "int", "shift", "auto", "vertices2d",
                    "vertices3d", "triangles",
                ):
                    self.mark_expr_field(field)
                self._param_layout.addRow(name, field)
                self._param_fields[name] = field
            dimension = self.controller.project.dimension if self.controller else (
                2 if shape == "POLYG" else 3
            )
            shift = QLineEdit(shift_text)
            shift.setPlaceholderText(
                f"{dimension}D offset, e.g. " + ", ".join(["0.0"] * dimension)
            )
            self.mark_expr_field(shift)
            self._param_layout.addRow("shift", shift)
            self._param_fields["shift"] = shift

        def _on_add(self) -> None:
            if self.controller is None:
                return
            av = self._current_avatar()
            if av is None:
                QMessageBox.warning(self, "Contactors", "Select an avatar")
                return
            shape = self.shape_combo.currentText()
            if not shape:
                return
            color = self.color_edit.text().strip() or "BLUEx"
            entry = {"shape": shape, "color": color}
            try:
                # validate compatibility
                dim = self.controller.project.dimension
                if shape not in self._compatible_shapes(av, dim):
                    raise ValidationError(
                        f"shape {shape!r} incompatible with {av.avatar_type.value} in {dim}D"
                    )
                params = _read_contactor_params(
                    shape,
                    {
                        name: field.currentText() if isinstance(field, QComboBox) else field.text()
                        for name, field in self._param_fields.items()
                    },
                    dimension=dim,
                    evaluate_float=lambda text, name: self.eval_float(text, 0.0, name),
                    evaluate_expression=lambda text: safe_eval(text, self._get_context()),
                    options=self._shape_options(shape),
                    optional_options=self._shape_optional_options(shape),
                    mesh_contactors=self._mesh_contactors,
                )
                if params:
                    entry["params"] = params
                group = self.bygroup_edit.text().strip()
                if shape in self._mesh_contactors and group:
                    entry["group"] = group
                updated = av.copy()
                updated.contactors.append(entry)
                self.controller.update_avatar(av.avatar_id, updated)
                self.controller.journal.info(
                    f"Contactor {shape} added on {av.avatar_id[:8]}…"
                )
            except (
                LMGC90Error, ValueError, SyntaxError, TypeError, KeyError,
            ) as exc:
                QMessageBox.warning(self, "Contactors", str(exc))

        def _on_remove(self) -> None:
            av = self._current_avatar()
            if av is None or self.controller is None:
                return
            row = self.list.currentRow()
            if row < 0 or row >= len(av.contactors):
                return
            updated = av.copy()
            removed = updated.contactors.pop(row)
            try:
                self.controller.update_avatar(av.avatar_id, updated)
                self.controller.journal.info(
                    f"Removed contactor {removed.get('shape')}"
                )
            except (LMGC90Error, ValueError, TypeError) as exc:
                QMessageBox.warning(self, "Contactors", str(exc))

    return ContactorsTab(parent)
