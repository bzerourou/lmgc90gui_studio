"""ContactorsTab — manage contactors on a selected avatar (esp. emptyAvatar / mesh)."""
from __future__ import annotations

import ast

from lmgc90_core import ValidationError
from lmgc90_core.types import AvatarType
from lmgc90_core.validate import compatible_contactors

from .base_tab import BaseTab


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


def _contactor_param_schema(shape: str, generation_type: str = "regular"):
    schema = _CONTACTOR_PARAMS.get(shape, ())
    if shape in _MESH_CONTACTORS:
        return schema
    if shape not in ("POLYG", "POLYR"):
        return (*schema, ("shift", "shift", "", "Coordinates relative to the avatar center"))
    selector = schema[0]
    return (
        selector,
        *_POLYGON_PARAMS[(shape, generation_type)],
        ("shift", "shift", "", "Coordinates relative to the avatar center"),
    )


def _read_contactor_params(
    shape: str,
    fields: dict[str, object],
    *,
    dimension: int = 2,
) -> dict[str, object]:
    """Convert the visible shape-specific form fields to pylmgc90 option values."""
    parsed: dict[str, object] = {}
    generation_type = str(fields.get("generation_type", "regular"))
    if shape in ("POLYG", "POLYR") and generation_type not in ("regular", "full"):
        raise ValueError("generation_type must be 'regular' or 'full'")
    schemas = {
        name: kind
        for name, kind, _, _ in _contactor_param_schema(shape, generation_type)
    }
    for name, raw_value in fields.items():
        if name not in schemas:
            continue
        kind = schemas[name]
        value = str(raw_value).strip()
        if kind in ("shift", "choice"):
            continue
        if kind == "float":
            number = float(value)
            if number <= 0:
                raise ValueError(f"{name} must be greater than zero")
            parsed[name] = number
        elif kind == "int":
            number = int(value)
            minimum = 3 if shape == "POLYG" else 4 if shape == "POLYR" else 1
            if number < minimum:
                raise ValueError(f"{name} must be at least {minimum}")
            parsed[name] = number
        elif kind in ("vertices2d", "vertices3d"):
            dimension = 2 if kind == "vertices2d" else 3
            rows = []
            for row in value.replace("\n", ";").split(";"):
                if row.strip():
                    coordinates = [float(part) for part in row.replace(",", " ").split()]
                    if len(coordinates) != dimension:
                        raise ValueError(
                            f"{name} needs {dimension} coordinates per vertex"
                        )
                    rows.append(coordinates)
            if len(rows) < dimension + 1:
                raise ValueError(f"{name} needs at least {dimension + 1} vertices")
            parsed[name] = rows
        elif kind == "triangles":
            faces = ast.literal_eval(value)
            if not isinstance(faces, list) or not faces:
                raise ValueError("connectivity must be a non-empty list of triangular faces")
            if any(not isinstance(face, (list, tuple)) or len(face) != 3 for face in faces):
                raise ValueError("each connectivity row must contain 3 vertex indices")
            parsed[name] = [[int(index) for index in face] for face in faces]
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
        coordinates = [float(part) for part in str(shift).replace(",", " ").split()]
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
            shapes = compatible_contactors(av.avatar_type, dim)
            self.shape_combo.addItems(list(shapes))
            # sensible default for emptyAvatar
            if av.avatar_type == AvatarType.EMPTY_AVATAR and "DISKx" in shapes:
                self.shape_combo.setCurrentText("DISKx")
            self._on_shape_changed(self.shape_combo.currentText())

        def _on_shape_changed(self, shape: str) -> None:
            if shape in ("POLYG", "POLYR"):
                self._build_polygon_fields(shape, "regular")
            else:
                clear_layout(self._param_layout)
                self._param_fields = {}
                for name, kind, default, placeholder in _contactor_param_schema(shape):
                    if kind == "shift" and self.controller is not None:
                        dimension = self.controller.project.dimension
                        placeholder = (
                            f"{dimension}D offset, e.g. "
                            + ", ".join(["0.0"] * dimension)
                        )
                    field = QLineEdit(str(default))
                    field.setPlaceholderText(placeholder)
                    self._param_layout.addRow(name, field)
                    self._param_fields[name] = field
            is_mesh = shape in _MESH_CONTACTORS
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
            for name, _kind, default, placeholder in _POLYGON_PARAMS[
                (shape, generation_type)
            ]:
                field = QLineEdit(str(default))
                field.setPlaceholderText(placeholder)
                self._param_layout.addRow(name, field)
                self._param_fields[name] = field
            dimension = self.controller.project.dimension if self.controller else (
                2 if shape == "POLYG" else 3
            )
            shift = QLineEdit(shift_text)
            shift.setPlaceholderText(
                f"{dimension}D offset, e.g. " + ", ".join(["0.0"] * dimension)
            )
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
                if shape not in compatible_contactors(av.avatar_type, dim):
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
                )
                if params:
                    entry["params"] = params
                group = self.bygroup_edit.text().strip()
                if shape in _MESH_CONTACTORS and group:
                    entry["group"] = group
                av.contactors.append(entry)
                self.controller.session.mark_dirty()
                self.controller.state_changed.emit()
                self.controller.journal.info(
                    f"Contactor {shape} added on {av.avatar_id[:8]}…"
                )
            except (ValidationError, ValueError, SyntaxError, TypeError, KeyError) as exc:
                QMessageBox.warning(self, "Contactors", str(exc))

        def _on_remove(self) -> None:
            av = self._current_avatar()
            if av is None or self.controller is None:
                return
            row = self.list.currentRow()
            if row < 0 or row >= len(av.contactors):
                return
            removed = av.contactors.pop(row)
            self.controller.session.mark_dirty()
            self.controller.state_changed.emit()
            self.controller.journal.info(f"Removed contactor {removed.get('shape')}")

    return ContactorsTab(parent)
