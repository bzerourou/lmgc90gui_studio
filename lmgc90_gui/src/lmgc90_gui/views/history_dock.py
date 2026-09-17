"""HistoryDock — chronological command stack (undo journal) with Undo/Redo."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_history_dock(parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget,
    )

    class HistoryPanel(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.controller: Optional["ProjectController"] = None
            layout = QVBoxLayout(self)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.addWidget(QLabel("Command history (chronological)"))
            self.list = QListWidget()
            layout.addWidget(self.list)
            row = QHBoxLayout()
            self.btn_undo = QPushButton("Undo")
            self.btn_redo = QPushButton("Redo")
            self.btn_undo.clicked.connect(self._on_undo)
            self.btn_redo.clicked.connect(self._on_redo)
            row.addWidget(self.btn_undo)
            row.addWidget(self.btn_redo)
            layout.addLayout(row)
            self.count_label = QLabel("0 commands")
            layout.addWidget(self.count_label)

        def bind_controller(self, controller: "ProjectController") -> None:
            self.controller = controller
            controller.state_changed.connect(self.refresh)
            self.refresh()

        def refresh(self) -> None:
            if self.controller is None:
                return
            hist = self.controller.project.history
            self.list.clear()
            for i, line in enumerate(hist.describe_stack(), 1):
                self.list.addItem(f"{i:03d}  {line}")
            n = len(hist)
            self.count_label.setText(f"{n} command(s)  ·  undo stack")
            # scroll to end
            if n:
                self.list.scrollToBottom()

        def _on_undo(self) -> None:
            if self.controller is None:
                return
            try:
                self.controller.undo()
                self.controller.journal.info("Undo")
            except Exception as exc:
                self.controller.journal.warning(str(exc))

        def _on_redo(self) -> None:
            if self.controller is None:
                return
            try:
                self.controller.redo()
                self.controller.journal.info("Redo")
            except Exception as exc:
                self.controller.journal.warning(str(exc))

    return HistoryPanel(parent)
