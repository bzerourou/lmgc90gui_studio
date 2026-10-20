"""DOFTab — configure LMGC90 kinematic and boundary-condition operations."""
from __future__ import annotations

import ast
from typing import Any

from lmgc90_core import DOFOperation, ValidationError

from .base_tab import BaseTab
from ..widgets.entity_tree import create_entity_tree

_LAWS = (
    "imposeDrivenDof",
    "imposeInitValue",
    "relaxDrivenDof",
    "translate",
    "rotate",
    "scale",
)

_LAW_HELP = {
    "imposeDrivenDof": (
        "predefined : (ct + amp·cos(omega·t + phi))·min(1, rampi + ramp·t). "
        "evolution : evolutionFile contient deux colonnes (temps, valeur). "
        "dofty dépend du modèle; plot_time_range est facultatif."
    ),
    "imposeInitValue": (
        "Initialise les ddl indiqués avec value (scalaire ou liste). "
        "group désigne le groupe de nœuds LMGC90, pas le groupe d’avatars."
    ),
    "relaxDrivenDof": "Libère les ddl précédemment imposés.",
    "translate": "Déplace les nœuds de l’avatar selon dx, dy, dz.",
    "rotate": (
        "Rotation en radians : angles d’Euler (phi, theta, psi) ou axe/angle. "
        "En 2D, seule psi peut être non nulle; center vide signifie l’origine."
    ),
    "scale": "Met à l’échelle l’avatar autour de son origine.",
}

_PARAM_FIELDS = {
    "imposeDrivenDof": (
        ("group", "Groupe de nœuds LMGC90", "text", "all"),
        ("component", "Composantes", "components", "1"),
        ("description", "Description", "choice", ("predefined", "evolution")),
        ("dofty", "Type de ddl", "text", "vlocy"),
        ("ct", "Valeur constante (ct)", "number", "0"),
        ("amp", "Amplitude", "number", "0"),
        ("omega", "Pulsation (omega)", "number", "0"),
        ("phi", "Phase (phi, rad)", "number", "0"),
        ("rampi", "Rampe initiale (rampi)", "number", "1"),
        ("ramp", "Pente de rampe (ramp)", "number", "0"),
        ("evolutionFile", "Fichier d’évolution", "text", ""),
        ("plot_time_range", "Plage de tracé [début, fin]", "value", ""),
    ),
    "imposeInitValue": (
        ("group", "Groupe de nœuds LMGC90", "text", "all"),
        ("component", "Composantes", "components", "1"),
        ("value", "Valeur(s)", "value", "0"),
    ),
    "relaxDrivenDof": (
        ("group", "Groupe de nœuds LMGC90", "text", "all"),
        ("component", "Composantes", "components", "1"),
    ),
    "translate": (
        ("dx", "Déplacement X", "number", "0"),
        ("dy", "Déplacement Y", "number", "0"),
        ("dz", "Déplacement Z", "number", "0"),
    ),
    "rotate": (
        ("description", "Paramétrisation", "choice", ("Euler", "axis")),
        ("phi", "Angle phi (rad)", "number", "0"),
        ("theta", "Angle theta (rad)", "number", "0"),
        ("psi", "Angle psi (rad)", "number", "0"),
        ("axis", "Axe [x, y, z]", "value", "[0, 0, 1]"),
        ("alpha", "Angle alpha (rad)", "number", "0"),
        ("center", "Centre (optionnel)", "value", ""),
    ),
    "scale": (("scale", "Facteur d’échelle", "number", "1"),),
}


def _parse_params(text: str) -> dict[str, Any]:
    """Parse legacy/custom ``key=value`` parameter strings."""
    text = (text or "").strip()
    if not text:
        return {}
    try:
        tree = ast.parse(f"f({text})", mode="eval")
        if not isinstance(tree.body, ast.Call):
            raise ValueError("paramètres attendus sous la forme clé=valeur")
        if any(keyword.arg is None for keyword in tree.body.keywords):
            raise ValueError("les paramètres **kwargs ne sont pas pris en charge")
        return {
            keyword.arg: ast.literal_eval(keyword.value)
            for keyword in tree.body.keywords
        }
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"Paramètres invalides : {exc}") from exc


def _parse_value(text: str) -> Any:
    value = text.strip()
    if not value:
        return ""
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        if "," in value:
            try:
                return [ast.literal_eval(part.strip()) for part in value.split(",")]
            except (SyntaxError, ValueError):
                pass
        return value


def _format_params(params: dict[str, Any] | None) -> str:
    if not params:
        return ""
    return ", ".join(f"{key}={value!r}" for key, value in params.items())


def create_dof_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
        QPushButton, QVBoxLayout, QWidget,
    )

    class DOFTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._editing_index: int | None = None
            self._suppress_law_default = False
            self._param_widgets: dict[str, Any] = {}
            self._advanced_params: QLineEdit | None = None
            self._hidden_params: set[str] = set()

            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "Conditions aux limites et opérations cinématiques. "
                "Une cible couleur sélectionne l’avatar entier si l’un de ses contacteurs "
                "porte cette couleur; le paramètre group peut limiter les nœuds."
            ))
            self.tree = create_entity_tree(
                ["#", "Fonction", "Cible", "Valeur cible", "Paramètres"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)

            form = QFormLayout()
            self.law_combo = QComboBox()
            self.law_combo.addItems(_LAWS)
            self.law_combo.currentTextChanged.connect(self._on_law_changed)

            self.target_type = QComboBox()
            self.target_type.addItems(["avatar", "group", "color"])
            self.target_type.currentTextChanged.connect(self._refill_target_values)

            self.target_value = QComboBox()
            self.target_value.setEditable(True)
            self.target_value.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            self.help_label = QLabel()
            self.help_label.setWordWrap(True)
            self.params_form = QFormLayout()

            form.addRow("Fonction LMGC90", self.law_combo)
            form.addRow("Cible", self.target_type)
            form.addRow("Valeur cible", self.target_value)
            form.addRow(self.help_label)
            form.addRow(self.params_form)
            layout.addLayout(form)

            row = QHBoxLayout()
            for text, slot in (
                ("➕ Add", self._on_add),
                ("💾 Update", self._on_update),
                ("🗑️ Delete", self._on_remove),
                ("Clear form", self._clear_form),
            ):
                button = QPushButton(text)
                button.clicked.connect(slot)
                row.addWidget(button)
            layout.addLayout(row)
            self._rebuild_params()

        def _avatar_choices(self) -> list[tuple[str, str]]:
            if self.controller is None:
                return []
            return [
                (avatar.avatar_id, f"{avatar.avatar_id[:12]}… | {avatar.avatar_type.value}")
                for avatar in self.controller.project.avatars
            ]

        def _group_choices(self) -> list[str]:
            if self.controller is None:
                return []
            return sorted(self.controller.project.avatar_groups)

        def _color_choices(self) -> list[str]:
            if self.controller is None:
                return []
            colors = set()
            for avatar in self.controller.project.avatars:
                if avatar.color:
                    colors.add(avatar.color)
                colors.update(
                    contactor["color"]
                    for contactor in avatar.contactors
                    if contactor.get("color")
                )
            return sorted(colors)

        def _refill_target_values(self, *_args) -> None:
            previous = self.target_value.currentData() or self.target_value.currentText().strip()
            self.target_value.blockSignals(True)
            self.target_value.clear()
            target_type = self.target_type.currentText()
            if target_type == "avatar":
                choices = self._avatar_choices()
            elif target_type == "group":
                choices = [(name, name) for name in self._group_choices()]
            else:
                choices = [(color, color) for color in self._color_choices()]

            if not choices:
                self.target_value.addItem("(aucune cible disponible)", "")
            else:
                for value, label in choices:
                    self.target_value.addItem(label, value)

            index = self.target_value.findData(previous)
            if index >= 0:
                self.target_value.setCurrentIndex(index)
            elif previous:
                self.target_value.setEditText(str(previous))
            self.target_value.blockSignals(False)

        @staticmethod
        def _line_edit(value: Any) -> QLineEdit:
            widget = QLineEdit(str(value))
            return widget

        def _clear_param_fields(self) -> None:
            while self.params_form.count():
                item = self.params_form.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            self._param_widgets.clear()
            self._advanced_params = None

        def _rebuild_params(self, values: dict[str, Any] | None = None) -> None:
            values = values or {}
            self._clear_param_fields()
            law = self.law_combo.currentText()
            self.help_label.setText(_LAW_HELP.get(
                law, "Arguments LMGC90 au format clé=valeur."
            ))
            fields = _PARAM_FIELDS.get(law)
            if fields is None:
                self._advanced_params = self._line_edit(
                    _format_params(values)
                )
                self.params_form.addRow("Arguments avancés", self._advanced_params)
                return

            for key, label, kind, default in fields:
                value = values.get(key, default)
                if kind == "choice":
                    widget = QComboBox()
                    widget.addItems(default)
                    current = widget.findText(str(value))
                    if current >= 0:
                        widget.setCurrentIndex(current)
                else:
                    widget = self._line_edit(value)
                self._param_widgets[key] = widget
                self.params_form.addRow(label, widget)

            description = self._param_widgets.get("description")
            if isinstance(description, QComboBox):
                description.currentTextChanged.connect(self._update_param_visibility)
            self._update_param_visibility()

        def _update_param_visibility(self, *_args) -> None:
            law = self.law_combo.currentText()
            description = self._param_widgets.get("description")
            mode = description.currentText() if isinstance(description, QComboBox) else ""
            visibility = {
                "imposeDrivenDof": {
                    "predefined": {"ct", "amp", "omega", "phi", "rampi", "ramp"},
                    "evolution": {"evolutionFile"},
                },
                "rotate": {
                    "Euler": {"phi", "theta", "psi"},
                    "axis": {"axis", "alpha"},
                },
            }
            groups = visibility.get(law, {})
            active = groups.get(mode)
            conditional = {
                name for names in groups.values() for name in names
            }
            self._hidden_params = conditional - (active or set())
            for key, widget in self._param_widgets.items():
                if key in conditional:
                    row = self.params_form.labelForField(widget)
                    visible = key in active
                    if (
                        law == "rotate" and key in {"phi", "theta"}
                        and self.controller is not None
                        and self.controller.project.dimension == 2
                    ):
                        visible = False
                    widget.setVisible(visible)
                    if row is not None:
                        row.setVisible(visible)

        def _on_law_changed(self, _law: str) -> None:
            if not self._suppress_law_default:
                self._rebuild_params()

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            self._refill_target_values()
            selected = self.tree.selected_payload()
            self.tree.clear_rows()
            for index, operation in enumerate(self.controller.project.operations):
                self.tree.add_row(
                    [
                        str(index), operation.operation_type, operation.target_type,
                        str(operation.target_value), _format_params(operation.parameters)[:48],
                    ],
                    payload=index,
                )
            self.tree.resize_columns()
            if selected is not None:
                self.tree.select_payload(selected)

        def _load_selected(self, index: int) -> None:
            if self.controller is None:
                return
            operations = self.controller.project.operations
            if not 0 <= index < len(operations):
                return
            operation = operations[index]
            self._editing_index = index
            self._suppress_law_default = True
            law_index = self.law_combo.findText(operation.operation_type)
            if law_index < 0:
                self.law_combo.addItem(operation.operation_type)
                law_index = self.law_combo.findText(operation.operation_type)
            self.law_combo.setCurrentIndex(law_index)
            self._suppress_law_default = False
            target_index = self.target_type.findText(operation.target_type)
            self.target_type.setCurrentIndex(target_index if target_index >= 0 else 0)
            self._refill_target_values()
            target_index = self.target_value.findData(str(operation.target_value))
            if target_index >= 0:
                self.target_value.setCurrentIndex(target_index)
            else:
                self.target_value.setEditText(str(operation.target_value))
            self._rebuild_params(operation.parameters)

        def _collect_params(self) -> dict[str, Any]:
            if self._advanced_params is not None:
                return _parse_params(self._advanced_params.text())
            params = {}
            for key, widget in self._param_widgets.items():
                if key in self._hidden_params:
                    continue
                if isinstance(widget, QComboBox):
                    params[key] = widget.currentText()
                    continue
                text = widget.text().strip()
                kind = next(
                    field[2] for field in _PARAM_FIELDS[self.law_combo.currentText()]
                    if field[0] == key
                )
                if not text and key in {"center", "evolutionFile", "plot_time_range"}:
                    continue
                if kind == "number":
                    try:
                        params[key] = float(text)
                    except ValueError as exc:
                        raise ValueError(f"{key} doit être un nombre.") from exc
                elif kind in ("value", "components"):
                    parsed = _parse_value(text)
                    if kind == "components":
                        if isinstance(parsed, str):
                            parsed = [
                                int(part.strip()) for part in text.split(",") if part.strip()
                            ]
                        components = parsed if isinstance(parsed, (list, tuple)) else [parsed]
                        if not all(
                            isinstance(component, int) and not isinstance(component, bool)
                            for component in components
                        ):
                            raise ValueError("Les composantes doivent être un entier ou une liste.")
                    elif key in {"axis", "center", "plot_time_range"}:
                        values = parsed if isinstance(parsed, (list, tuple)) else [parsed]
                        if not all(isinstance(value, (int, float)) for value in values):
                            raise ValueError(f"{key} doit contenir des valeurs numériques.")
                        if key == "axis" and len(values) != 3:
                            raise ValueError("L’axe doit comporter trois composantes.")
                        if key == "plot_time_range" and len(values) != 2:
                            raise ValueError("La plage de tracé doit être [début, fin].")
                    elif isinstance(parsed, str):
                        raise ValueError(f"{key} doit être un nombre ou une liste de nombres.")
                    params[key] = parsed
                else:
                    params[key] = text
            if params.get("description") != "evolution":
                params.pop("evolutionFile", None)
            elif not params.get("evolutionFile"):
                raise ValueError("Le mode evolution exige un fichier d’évolution.")
            return params

        def _clear_form(self) -> None:
            self._editing_index = None
            self.tree.clearSelection()
            self.law_combo.setCurrentIndex(0)
            self.target_type.setCurrentIndex(0)
            self._refill_target_values()
            self._rebuild_params()

        def _build(self) -> DOFOperation:
            law = self.law_combo.currentText().strip()
            target_type = self.target_type.currentText().strip()
            target_value = self.target_value.currentData()
            if target_value in (None, ""):
                target_value = self.target_value.currentText().strip()
            if not target_value or str(target_value).startswith("("):
                raise ValueError(f"Choisissez une cible valide pour {target_type!r}.")
            return DOFOperation(
                operation_type=law,
                target_type=target_type,
                target_value=str(target_value),
                parameters=self._collect_params(),
            )

        def _on_add(self) -> None:
            if self.controller is None:
                return
            try:
                self.controller.add_dof(self._build())
                self._clear_form()
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "DOF", str(exc))

        def _on_update(self) -> None:
            if self.controller is None:
                return
            if self._editing_index is None:
                QMessageBox.information(self, "DOF", "Sélectionnez une ligne")
                return
            try:
                self.controller.update_dof(self._editing_index, self._build())
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "DOF", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            index = self.tree.selected_payload()
            if index is None:
                index = self._editing_index
            if index is not None:
                self.controller.remove_dof(int(index))
                self._clear_form()

    return DOFTab(parent)
