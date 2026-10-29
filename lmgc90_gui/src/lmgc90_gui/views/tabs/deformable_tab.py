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
                "<b>Deformable Bodies (EF)</b><br/><br/>"
                "The multi-page wizard reproduces the flow of "
                "<code>mesh_wiz_def.MeshWizard</code> :<br/>"
                "Dimension → Material ELAS → FE Model → Geometry → "
                "Refinement → Contactors → Generation.<br/><br/>"
                "The data goes into <code>Project</code> (not into the "

                " direct pylmgc docker) ; the materialization is done by the"
                "lmgc90_engine at export / DATBOX."
            ))
            btn = QPushButton("Open Mesh Wizard…")
            btn.setMinimumHeight(40)
            btn.clicked.connect(self._open_wizard)
            layout.addWidget(btn)
            layout.addWidget(QLabel(
                "<i>Pages : Intro, Dimension, Material, FE Model, Geometry "
                "(Rectangle / Disk / Box / Sphere / Cylinder / File), "
                "Refinement, Contactors CLxxx/CSpxx, Summary.</i>"
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
