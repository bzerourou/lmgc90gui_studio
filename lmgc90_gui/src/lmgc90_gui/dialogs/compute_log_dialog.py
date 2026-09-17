"""Live log window while chipy computation runs."""
from __future__ import annotations


def create_compute_log_dialog(parent=None):
    from PyQt6.QtGui import QFont, QTextCursor
    from PyQt6.QtWidgets import (
        QDialog, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    )

    class ComputeLogDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Computation log")
            self.resize(700, 400)
            self._stop_cb = None
            layout = QVBoxLayout(self)
            self.status = QLabel("Running…")
            layout.addWidget(self.status)
            self.text = QTextEdit()
            self.text.setReadOnly(True)
            self.text.setFont(QFont("Consolas", 10))
            layout.addWidget(self.text)
            row = QHBoxLayout()
            self.btn_stop = QPushButton("Stop")
            self.btn_close = QPushButton("Close")
            self.btn_close.setEnabled(False)
            self.btn_stop.clicked.connect(self._on_stop)
            self.btn_close.clicked.connect(self.accept)
            row.addWidget(self.btn_stop)
            row.addStretch()
            row.addWidget(self.btn_close)
            layout.addLayout(row)

        def set_stop_callback(self, cb) -> None:
            self._stop_cb = cb

        def append_line(self, line: str) -> None:
            self.text.append(line)
            self.text.moveCursor(QTextCursor.MoveOperation.End)

        def mark_finished(self, rc: int) -> None:
            self.status.setText(f"Finished (exit code {rc})")
            self.btn_stop.setEnabled(False)
            self.btn_close.setEnabled(True)

        def mark_failed(self, msg: str) -> None:
            self.status.setText("Failed")
            self.append_line(msg)
            self.btn_stop.setEnabled(False)
            self.btn_close.setEnabled(True)

        def _on_stop(self) -> None:
            if self._stop_cb:
                self._stop_cb()
            self.status.setText("Stopping…")

    return ComputeLogDialog(parent)
