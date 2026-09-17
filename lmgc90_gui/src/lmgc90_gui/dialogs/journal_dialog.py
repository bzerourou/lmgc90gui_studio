"""Journal dialog — live view of AppJournal."""
from __future__ import annotations


def create_journal_dialog(parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QTextCursor
    from PyQt6.QtWidgets import (
        QDialog, QDialogButtonBox, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout,
    )

    from ..utils.app_journal import get_journal

    class JournalDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Application journal")
            self.resize(720, 420)
            self._journal = get_journal()
            layout = QVBoxLayout(self)
            self.text = QTextEdit()
            self.text.setReadOnly(True)
            self.text.setFont(QFont("Consolas", 10))
            layout.addWidget(self.text)

            row = QHBoxLayout()
            btn_clear = QPushButton("Clear")
            btn_clear.clicked.connect(self._on_clear)
            btn_refresh = QPushButton("Refresh")
            btn_refresh.clicked.connect(self._reload)
            row.addWidget(btn_clear)
            row.addWidget(btn_refresh)
            row.addStretch()
            layout.addLayout(row)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(self.reject)
            buttons.accepted.connect(self.accept)
            buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
            layout.addWidget(buttons)

            self._reload()
            self._journal.subscribe(self._on_entry)

        def closeEvent(self, event):
            self._journal.unsubscribe(self._on_entry)
            super().closeEvent(event)

        def _reload(self) -> None:
            self.text.setPlainText(self._journal.text())
            self.text.moveCursor(QTextCursor.MoveOperation.End)

        def _on_entry(self, entry) -> None:
            self.text.append(entry.format())

        def _on_clear(self) -> None:
            self._journal.clear()
            self.text.clear()

    return JournalDialog(parent)
