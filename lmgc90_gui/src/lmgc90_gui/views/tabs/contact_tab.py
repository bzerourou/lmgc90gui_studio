"""ContactTab — laws list as QTreeWidget + form CRUD."""
from __future__ import annotations

from lmgc90_core import ContactLaw, ValidationError, pre
from lmgc90_core.types import (
    CONTACT_LAW_CATEGORIES, CONTACT_LAW_PROPERTY_SCHEMA, ContactLawType,
)

from .base_tab import BaseTab
from ...utils.field_forms import clear_layout
from ...utils.naming import suggest_law_name
from ..widgets.entity_tree import create_entity_tree


def create_contact_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
        QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class ContactTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._prop_widgets: dict = {}
            self._editing_name: str | None = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Lois de contact — sélectionnez pour modifier"))
            self.tree = create_entity_tree(
                ["Name", "Law", "Params"],
                on_select=self._load_selected,
            )
            layout.addWidget(self.tree, stretch=1)

            form = QFormLayout()
            self.name_edit = QLineEdit()
            self.name_edit.setMaxLength(5)
            self.category_combo = QComboBox()
            self.category_combo.addItems([
                "Toutes les familles", "rigid/rigid", "any/defo",
                "point/point", "any/any",
            ])
            self.law_combo = QComboBox()
            for law in ContactLawType:
                self.law_combo.addItem(law.value, law)
            self.category_combo.currentTextChanged.connect(self._filter_laws)
            form.addRow("Contact family", self.category_combo)
            form.addRow("Name", self.name_edit)
            form.addRow("Law type", self.law_combo)
            layout.addLayout(form)

            self.props_box = QGroupBox("Parameters")
            self.props_form = QFormLayout(self.props_box)
            layout.addWidget(self.props_box)
            self.law_combo.currentIndexChanged.connect(self._rebuild_props)
            self.law_combo.currentIndexChanged.connect(self._suggest_name)
            self._rebuild_props()

            row = QHBoxLayout()
            for text, slot in (
                ("➕ Add", self._on_add),
                ("💾 Update", self._on_update),
                ("🗑️ Delete", self._on_remove),
                ("Clear form", self._clear_form),
            ):
                b = QPushButton(text); b.clicked.connect(slot); row.addWidget(b)
            layout.addLayout(row)
            self._filter_laws(self.category_combo.currentText())

        def _filter_laws(self, category: str) -> None:
            selected = self.law_combo.currentData()
            if category == "Toutes les familles":
                law_values = [law.value for law in ContactLawType]
            else:
                law_values = list(CONTACT_LAW_CATEGORIES[category])
            self.law_combo.blockSignals(True)
            self.law_combo.clear()
            for value in law_values:
                law = ContactLawType(value)
                self.law_combo.addItem(value, law)
            index = self.law_combo.findData(selected)
            if index >= 0:
                self.law_combo.setCurrentIndex(index)
            self.law_combo.blockSignals(False)
            self._rebuild_props()
            self._suggest_name()

        def _rebuild_props(self, *_a) -> None:
            clear_layout(self.props_form)
            self._prop_widgets.clear()
            law = self.law_combo.currentData()
            key = law.value if law else "IQS_CLB"
            schema = CONTACT_LAW_PROPERTY_SCHEMA.get(key)
            if schema is None:
                schema = ()
            for name, default, kind in schema:
                if kind == "float":
                    w = QLineEdit(str(default) if default not in (None, "") else "0")
                    w.setPlaceholderText("nombre ou expression")
                    self.mark_expr_field(w)
                else:
                    w = QLineEdit(str(default or ""))
                self.props_form.addRow(name, w)
                self._prop_widgets[name] = (w, kind)

        def _suggest_name(self, *_a) -> None:
            if self.controller is None or self._editing_name:
                return
            law = self.law_combo.currentData()
            key = law.value if law else "IQS_CLB"
            existing = [x.name for x in self.controller.project.laws]
            suggested = suggest_law_name(key, existing)
            cur = self.name_edit.text().strip()
            if not cur or getattr(self, "_last_auto_name", "") == cur:
                self.name_edit.setText(suggested)
                self._last_auto_name = suggested

        def _collect(self) -> dict:
            props = {}
            for k, (w, kind) in self._prop_widgets.items():
                props[k] = (
                    self.eval_float(w.text(), 0.0, k)
                    if kind == "float" else w.text().strip()
                )
            return props

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            sel = self.tree.selected_payload()
            self.tree.clear_rows()
            for law in self.controller.project.laws:
                props = ", ".join(f"{k}={v}" for k, v in (law.properties or {}).items())
                self.tree.add_row([law.name, law.law_type.value, props[:50]], law.name)
            self.tree.resize_columns()
            if sel:
                self.tree.select_payload(sel)
            if not self._editing_name:
                self._suggest_name()

        def _load_selected(self, name: str) -> None:
            law = next((l for l in self.controller.project.laws if l.name == name), None)
            if not law:
                return
            self._editing_name = law.name
            self.name_edit.setText(law.name)
            idx = self.law_combo.findData(law.law_type)
            if idx < 0:
                self.category_combo.setCurrentText("Toutes les familles")
                idx = self.law_combo.findData(law.law_type)
            if idx >= 0:
                self.law_combo.setCurrentIndex(idx)
            self._rebuild_props()
            for k, (w, kind) in self._prop_widgets.items():
                val = (law.properties or {}).get(k)
                if val is None:
                    continue
                if kind == "float":
                    w.setText(str(val))
                else:
                    w.setText(str(val))

        def _clear_form(self) -> None:
            self._editing_name = None
            self.name_edit.clear()
            self._last_auto_name = ""
            self._rebuild_props()
            self._suggest_name()
            self.tree.clearSelection()

        def _build(self) -> ContactLaw:
            name = self.name_edit.text().strip()
            if not name:
                raise ValidationError("Name required")
            law_type = self.law_combo.currentData()
            return ContactLaw(name=name, law_type=law_type, properties=self._collect())

        def _on_add(self) -> None:
            try:
                law = self._build()
                if any(l.name == law.name for l in self.controller.project.laws):
                    raise ValidationError(f"{law.name!r} exists — use Update")
                self.controller.add_law(law)
                self._clear_form()
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Contact", str(exc))

        def _on_update(self) -> None:
            if not self._editing_name:
                QMessageBox.information(self, "Contact", "Sélectionnez une loi")
                return
            try:
                law = self._build()
                self.controller.update_law(self._editing_name, law)
                self._editing_name = law.name
            except (ValidationError, ValueError) as e:
                QMessageBox.warning(self, "Contact", str(e))

        def _on_remove(self) -> None:
            name = self.tree.selected_payload() or self._editing_name
            if name:
                self.controller.remove_law(name)
                self._clear_form()

    return ContactTab(parent)
