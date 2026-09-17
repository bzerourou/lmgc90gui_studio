"""DeformableTab — lance le MeshWizard (même flux que mesh_wiz_def) + raccourci rapide."""
from __future__ import annotations

from .base_tab import BaseTab


def create_deformable_tab(parent=None):
    from PyQt6.QtWidgets import (
        QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox,
    )

    class DeformableTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "<b>Corps déformables (EF)</b><br/><br/>"
                "L'assistant multi-pages reprend le flux de "
                "<code>mesh_wiz_def.MeshWizard</code> :<br/>"
                "Dimension → Matériau ELAS → Modèle FE → Géométrie → "
                "Raffinement → Contacteurs → Génération.<br/><br/>"
                "Les données vont dans <code>Project</code> (pas dans les "
                "conteneurs pylmgc directs) ; la matérialisation se fait via "
                "lmgc90_engine au moment de l'export / DATBOX."
            ))
            btn = QPushButton("Ouvrir l'assistant MeshWizard…")
            btn.setMinimumHeight(40)
            btn.clicked.connect(self._open_wizard)
            layout.addWidget(btn)
            layout.addWidget(QLabel(
                "<i>Pages : Intro, Dimension, Matériau, Modèle, Géométrie "
                "(Rectangle / Disque / Boîte / Sphère / Cylindre / fichier), "
                "Raffinement, Contacteurs CLxxx/CSpxx, Résumé.</i>"
            ))
            layout.addStretch()

        def on_state_changed(self) -> None:
            pass

        def _open_wizard(self) -> None:
            if self.controller is None:
                return
            try:
                from ...dialogs.mesh_wizard import create_mesh_wizard
                wiz = create_mesh_wizard(self.controller, self)
                wiz.exec()
            except Exception as exc:
                QMessageBox.critical(self, "MeshWizard", str(exc))
                if self.controller:
                    self.controller.journal.exception("open MeshWizard", exc)

    return DeformableTab(parent)
