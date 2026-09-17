"""ContactorsTab — manage contactors on a selected avatar (esp. emptyAvatar / mesh)."""
from __future__ import annotations

from lmgc90_core import ValidationError
from lmgc90_core.types import AvatarType
from lmgc90_core.validate import compatible_contactors

from .base_tab import BaseTab


def create_contactors_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
        QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

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
            self.color_edit = QLineEdit("BLUEx")
            self.bygroup_edit = QLineEdit()
            self.bygroup_edit.setPlaceholderText("optional group (mesh)")
            form.addRow("Shape", self.shape_combo)
            form.addRow("Color", self.color_edit)
            form.addRow("by group", self.bygroup_edit)
            layout.addLayout(form)

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

        def _on_avatar_changed(self, *_a) -> None:
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
            byg = self.bygroup_edit.text().strip()
            if byg:
                entry["by"] = byg
            try:
                # validate compatibility
                dim = self.controller.project.dimension
                if shape not in compatible_contactors(av.avatar_type, dim):
                    raise ValidationError(
                        f"shape {shape!r} incompatible with {av.avatar_type.value} in {dim}D"
                    )
                av.contactors.append(entry)
                self.controller.session.mark_dirty()
                self.controller.state_changed.emit()
                self.controller.journal.info(
                    f"Contactor {shape} added on {av.avatar_id[:8]}…"
                )
            except (ValidationError, ValueError) as exc:
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
