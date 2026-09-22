"""Assistant P2 — Lier deux couleurs / groupes avec une loi de contact.

Architecture: GUI only → builds VisibilityRule via core ``pre.see_table`` /
controller.add_visibility. No pylmgc import.
"""
from __future__ import annotations

from typing import Optional


def create_link_visibility_dialog(controller, parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
        QHBoxLayout, QLabel, QMessageBox, QVBoxLayout,
    )

    from lmgc90_core import ValidationError, pre
    from ..views.tabs.visibility_tab import (
        _project_colors, _project_laws, _project_shapes, _BODY_2D, _BODY_3D,
    )

    class LinkVisibilityDialog(QDialog):
        def __init__(self, controller, parent=None):
            super().__init__(parent)
            self.controller = controller
            self.setWindowTitle("Lier A ↔ B (see-table)")
            self.setMinimumWidth(420)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "Choisir deux couleurs (ou la même) présentes dans le projet,\n"
                "les shapes de contacteurs, et une loi déjà définie."
            ))

            form = QFormLayout()
            pr = controller.project
            dim = int(getattr(pr, "dimension", 2) or 2)
            bodies = list(_BODY_2D if dim == 2 else _BODY_3D)
            colors = _project_colors(pr)
            shapes_c = _project_shapes(pr, role="candidate")
            shapes_a = _project_shapes(pr, role="antagonist")
            laws = _project_laws(pr)

            def _cb(items, editable=False, default=None):
                box = QComboBox()
                box.setEditable(editable)
                for it in items:
                    box.addItem(it)
                if default and box.findText(default) >= 0:
                    box.setCurrentText(default)
                elif items:
                    box.setCurrentIndex(0)
                return box

            default_body = "RBDY3" if dim == 3 else "RBDY2"
            default_shape = "SPHER" if dim == 3 else "DISKx"
            c0 = colors[0] if colors else "BLUEx"
            c1 = colors[1] if len(colors) > 1 else c0

            self.c_body = _cb(bodies, default=default_body)
            self.a_body = _cb(bodies, default=default_body)
            self.c_shape = _cb(shapes_c, editable=True, default=default_shape)
            default_ant = "PLANx" if dim == 3 else "JONCx"
            self.a_shape = _cb(shapes_a, editable=True, default=default_ant)
            self.c_color = _cb(colors, editable=True, default=c0)
            self.a_color = _cb(colors, editable=True, default=c1)
            self.behav = _cb(laws, editable=True, default=laws[0] if laws else "IQS")
            self.alert = QDoubleSpinBox()
            self.alert.setRange(0, 1e3)
            self.alert.setDecimals(6)
            self.alert.setValue(0.05)

            # optional: group hints (informational)
            groups = sorted((pr.avatar_groups or {}).keys())
            self.group_a = _cb(["(aucun)"] + groups, editable=False)
            self.group_b = _cb(["(aucun)"] + groups, editable=False)

            form.addRow("Corps A", self.c_body)
            form.addRow("Shape A (candidat)", self.c_shape)
            form.addRow("Couleur A", self.c_color)
            form.addRow("Groupe A (info)", self.group_a)
            form.addRow("Corps B", self.a_body)
            form.addRow("Shape B (antagoniste)", self.a_shape)
            form.addRow("Couleur B", self.a_color)
            form.addRow("Groupe B (info)", self.group_b)
            form.addRow("Loi", self.behav)
            form.addRow("Alert", self.alert)
            layout.addLayout(form)

            # quick presets
            row = QHBoxLayout()
            layout.addWidget(QLabel("Presets rapides :"))
            from PyQt6.QtWidgets import QPushButton
            for label, slot in (
                ("Grains ↔ grains", self._preset_grain_grain),
                ("Grains ↔ sol", self._preset_grain_wall),
                ("Inverser A/B", self._swap_ab),
            ):
                b = QPushButton(label)
                b.clicked.connect(slot)
                row.addWidget(b)
            layout.addLayout(row)

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(self._accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def _text(self, box) -> str:
            return box.currentText().strip()

        def _swap_ab(self) -> None:
            pairs = (
                (self.c_body, self.a_body),
                (self.c_shape, self.a_shape),
                (self.c_color, self.a_color),
                (self.group_a, self.group_b),
            )
            for a, b in pairs:
                ta, tb = a.currentText(), b.currentText()
                a.setCurrentText(tb)
                b.setCurrentText(ta)

        def _preset_grain_grain(self) -> None:
            dim = int(self.controller.project.dimension)
            shape = "SPHER" if dim == 3 else "DISKx"
            for box in (self.c_shape, self.a_shape):
                if box.findText(shape) >= 0:
                    box.setCurrentText(shape)
                else:
                    box.setEditText(shape)
            # prefer BLUEx if present
            for box in (self.c_color, self.a_color):
                if box.findText("BLUEx") >= 0:
                    box.setCurrentText("BLUEx")
            self.alert.setValue(0.05)

        def _preset_grain_wall(self) -> None:
            dim = int(self.controller.project.dimension)
            grain = "SPHER" if dim == 3 else "DISKx"
            self.c_shape.setEditText(grain)
            self.a_shape.setEditText("JONCx")
            if self.a_color.findText("GRAYx") >= 0:
                self.a_color.setCurrentText("GRAYx")
            if self.c_color.findText("BLUEx") >= 0:
                self.c_color.setCurrentText("BLUEx")
            self.alert.setValue(0.05)

        def _accept(self) -> None:
            try:
                rule = pre.see_table(
                    CorpsCandidat=self._text(self.c_body),
                    candidat=self._text(self.c_shape),
                    colorCandidat=self._text(self.c_color),
                    CorpsAntagoniste=self._text(self.a_body),
                    antagoniste=self._text(self.a_shape),
                    colorAntagoniste=self._text(self.a_color),
                    behav=self._text(self.behav),
                    alert=self.alert.value(),
                )
                self.controller.add_visibility(rule)
                self.accept()
            except (ValidationError, ValueError, Exception) as e:
                QMessageBox.warning(self, "Lier A ↔ B", str(e))

    return LinkVisibilityDialog(controller, parent)
