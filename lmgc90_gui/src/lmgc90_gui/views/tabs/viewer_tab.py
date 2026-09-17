"""ViewerTab — Viewer3D legacy (pyvistaqt), refresh manuel.

Port fidèle de LMG90_GUI_MVC viewer_tab + viewer_3d.
"""
from __future__ import annotations

from .base_tab import BaseTab

VIEWER_PORT_TAG = "Viewer3D-port-v0.2"


def pyvista_available() -> bool:
    try:
        import pyvista  # noqa: F401
        import pyvistaqt  # noqa: F401
        return True
    except ImportError:
        return False


def create_viewer_tab(parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton,
        QVBoxLayout, QWidget,
    )

    class ViewerTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._dirty = False
            self.viewer = None

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            bar = QHBoxLayout()
            bar.setContentsMargins(4, 2, 4, 2)

            self._tag = QLabel(VIEWER_PORT_TAG)
            self._tag.setStyleSheet("color:#6af; font-size:8pt;")
            bar.addWidget(self._tag)

            self._pending_label = QLabel("")
            self._pending_label.setStyleSheet(
                "color: #e8a020; font-size: 9pt; font-style: italic;"
            )
            bar.addWidget(self._pending_label)
            bar.addStretch()

            self._visu_btn = QPushButton("👁 pre.visuAvatars")
            self._visu_btn.clicked.connect(self._on_visu_avatars)
            bar.addWidget(self._visu_btn)

            self._refresh_btn = QPushButton("🔄 Rafraîchir la scène")
            self._refresh_btn.setStyleSheet(
                "QPushButton { font-weight: bold; padding: 3px 10px; }"
                "QPushButton:hover { background: #2a5a9a; color: white; }"
            )
            self._refresh_btn.clicked.connect(self._do_refresh)
            bar.addWidget(self._refresh_btn)

            bar_w = QWidget()
            bar_w.setLayout(bar)
            bar_w.setStyleSheet(
                "background: #111122; border-bottom: 1px solid #333; color: #eee;"
            )
            root.addWidget(bar_w)

            self._holder_layout = QVBoxLayout()
            self._holder_layout.setContentsMargins(0, 0, 0, 0)
            holder = QWidget()
            holder.setLayout(self._holder_layout)
            root.addWidget(holder, stretch=1)

            if not pyvista_available():
                self._holder_layout.addWidget(QLabel(
                    "⚠️ pyvista + pyvistaqt absents.\n"
                    "  pip install pyvista pyvistaqt\n"
                    "Puis relancez lmgc90-gui."
                ))
            else:
                self._holder_layout.addWidget(QLabel(
                    "Viewer en attente du contrôleur…"
                ))

        def bind_controller(self, controller) -> None:
            super().bind_controller(controller)
            self._ensure_viewer()

        def _ensure_viewer(self) -> bool:
            if self.viewer is not None:
                return True
            if self.controller is None:
                return False
            if not pyvista_available():
                return False
            try:
                from .. import viewer_3d as v3mod
                from ..viewer_3d import Viewer3D
                # prove which file is loaded
                self._tag.setText(f"{VIEWER_PORT_TAG}  [{v3mod.__file__}]")
                while self._holder_layout.count():
                    item = self._holder_layout.takeAt(0)
                    w = item.widget()
                    if w is not None:
                        w.deleteLater()
                self.viewer = Viewer3D(self.controller, self)
                self._holder_layout.addWidget(self.viewer)
                if self.controller:
                    self.controller.journal.info(
                        f"Viewer3D ready from {v3mod.__file__}"
                    )
                return True
            except Exception as exc:
                self._pending_label.setText(f"❌ Viewer3D: {exc}")
                if self.controller:
                    self.controller.journal.exception("Viewer3D init", exc)
                return False

        def on_state_changed(self) -> None:
            self._dirty = True
            if self.controller is None:
                return
            p = self.controller.project
            n = len(p.avatars) + sum(len(pop) for pop in p.populations)
            self._pending_label.setText(
                f"⚠️ Scène non à jour — {n} objet(s)"
            )
            self._refresh_btn.setStyleSheet(
                "QPushButton { font-weight: bold; padding: 3px 10px; "
                "background: #3a6aaa; color: white; }"
            )

        def refresh(self) -> None:
            self.on_state_changed()
            self._do_refresh()

        def _do_refresh(self) -> None:
            if self.controller is None:
                return
            if not self._ensure_viewer():
                QMessageBox.warning(
                    self, "Visualisation 3D",
                    "Viewer3D indisponible.\n"
                    "pip install pyvista pyvistaqt\n"
                    "Puis: pip install -e .\\lmgc90_gui[qt,viz] --force-reinstall",
                )
                return
            p = self.controller.project
            renderables = list(p.avatars) + list(p.populations)
            n = len(p.avatars)
            try:
                self.viewer.update_avatars(renderables)
                self._pending_label.setText(f"✅ {n} avatar(s) envoyés au viewer")
                self.controller.journal.info(f"Viewer refresh: {n} avatars")
            except Exception as exc:
                QMessageBox.warning(self, "Visualisation 3D", str(exc))
                self.controller.journal.exception("Viewer3D update", exc)
                return
            self._dirty = False
            self._refresh_btn.setStyleSheet(
                "QPushButton { font-weight: bold; padding: 3px 10px; }"
            )

        def _on_visu_avatars(self) -> None:
            if self.controller is None:
                return
            if not self.controller.pylmgc_available():
                QMessageBox.warning(self, "visuAvatars", "pylmgc90 non disponible")
                return
            try:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                self.controller.visu_avatars(force=True)
            except Exception as e:
                QMessageBox.critical(self, "visuAvatars", str(e))
            finally:
                QApplication.restoreOverrideCursor()

    return ViewerTab(parent)
