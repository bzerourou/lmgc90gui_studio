"""MasonryTab — lance MasonryWizard (flux masonery_wizard.py)."""
from __future__ import annotations

from .base_tab import BaseTab


def create_masonry_tab(parent=None):
    from PyQt6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

    class MasonryTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "<b>Maçonnerie</b><br/><br/>"
                "Assistant multi-pages aligné sur "
                "<code>masonery_wizard.MasonryWizard</code> :<br/>"
                "Dimension → Matériau → Modèle → Brique → Appareil → "
                "Transform → Génération.<br/><br/>"
                "Appareils : <b>Standard</b>, <b>Running Bond</b>, "
                "<b>Stack Bond</b>, <b>Flemish Bond</b>.<br/>"
                "Briques = <code>rigidPolygon</code> dans le Project "
                "(pas d'injection pylmgc directe)."
            ))
            btn = QPushButton("Ouvrir l'assistant MasonryWizard…")
            btn.setMinimumHeight(40)
            btn.clicked.connect(self._open_wizard)
            layout.addWidget(btn)
            layout.addStretch()

        def on_state_changed(self) -> None:
            pass

        def _open_wizard(self) -> None:
            if self.controller is None:
                return
            try:
                from ...dialogs.masonry_wizard import create_masonry_wizard
                create_masonry_wizard(self.controller, self).exec()
            except Exception as exc:
                QMessageBox.critical(self, "MasonryWizard", str(exc))
                if self.controller:
                    self.controller.journal.exception("open MasonryWizard", exc)

    return MasonryTab(parent)
