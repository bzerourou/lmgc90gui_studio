"""Browse and load demo scenes (menu Exemples)."""
from __future__ import annotations

from typing import Optional

from ..examples import EXAMPLES, ExampleSpec, get_examples


def create_examples_dialog(parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget,
        QListWidgetItem, QSplitter, QTextBrowser, QVBoxLayout, QWidget,
    )

    class ExamplesDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("📚 Bibliothèque d'exemples")
            self.resize(720, 480)
            self._selected: Optional[ExampleSpec] = None

            root = QVBoxLayout(self)
            root.addWidget(QLabel(
                "Choisissez un exemple puis <b>Charger</b>. "
                "Le projet courant sera remplacé."
            ))

            split = QSplitter(Qt.Orientation.Horizontal)
            self.list = QListWidget()
            self.list.currentItemChanged.connect(self._on_sel)
            self.detail = QTextBrowser()
            split.addWidget(self.list)
            split.addWidget(self.detail)
            split.setStretchFactor(1, 2)
            root.addWidget(split, stretch=1)

            # group by category
            by_cat: dict[str, list[ExampleSpec]] = {}
            for ex in get_examples():
                by_cat.setdefault(ex.category, []).append(ex)
            for cat in sorted(by_cat.keys()):
                header = QListWidgetItem(f"— {cat} —")
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list.addItem(header)
                for ex in by_cat[cat]:
                    item = QListWidgetItem(ex.title)
                    item.setData(Qt.ItemDataRole.UserRole, ex.id)
                    self.list.addItem(item)

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Charger")
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            root.addWidget(buttons)

        def _on_sel(self, cur, _prev) -> None:
            if cur is None:
                return
            eid = cur.data(Qt.ItemDataRole.UserRole)
            if not eid:
                self._selected = None
                return
            from ..examples import get_example
            ex = get_example(str(eid))
            self._selected = ex
            if ex is None:
                return
            tags = ", ".join(ex.tags) if ex.tags else "—"
            self.detail.setHtml(
                f"<h2>{ex.title}</h2>"
                f"<p><b>Catégorie :</b> {ex.category} &nbsp; "
                f"<b>Dimension :</b> {ex.dimension}D &nbsp; "
                f"<b>Niveau :</b> {ex.difficulty}</p>"
                f"<p>{ex.description}</p>"
                f"<p><i>Tags : {tags}</i></p>"
                f"<p><code>id={ex.id}</code></p>"
            )

        def selected_example(self) -> Optional[ExampleSpec]:
            return self._selected

    return ExamplesDialog(parent)
