"""Logging and GUI reporting for otherwise-unhandled Python exceptions."""
from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType

from PyQt6.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMessageBox


_LOGGER = logging.getLogger("lmgc90_gui")
_reporter: _ExceptionReporter | None = None


class _ExceptionReporter(QObject):
    report_exception = pyqtSignal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.report_exception.connect(
            self._show_exception,
            Qt.ConnectionType.QueuedConnection,
        )

    @pyqtSlot(str, str)
    def _show_exception(self, message: str, details: str) -> None:
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("Unexpected error")
        dialog.setText(message)
        dialog.setInformativeText(
            "The error was logged. The application will continue if it is safe."
        )
        dialog.setDetailedText(details)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()


def _write_stderr(text: str) -> None:
    stderr = sys.__stderr__
    if stderr is not None:
        try:
            stderr.write(text)
            stderr.flush()
        except OSError:
            return


def _handle_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    try:
        details = "".join(traceback.format_exception(
            exc_type, exc_value, exc_traceback,
        ))
        message = f"{exc_type.__name__}: {exc_value}"
    except Exception as formatting_error:
        details = f"{exc_type.__name__} (exception details could not be formatted)"
        message = details
        _LOGGER.error(
            "Failed to format an unhandled exception: %s",
            type(formatting_error).__name__,
        )

    try:
        _LOGGER.critical("Unhandled exception in the GUI:\n%s", details)
    except Exception as logging_error:
        _write_stderr(
            f"Failed to log an unhandled GUI exception: "
            f"{type(logging_error).__name__}\n{details}"
        )

    reporter = _reporter
    if reporter is not None and QApplication.instance() is not None:
        try:
            reporter.report_exception.emit(message, details)
            return
        except RuntimeError as report_error:
            _write_stderr(
                f"Failed to queue the GUI exception dialog: "
                f"{type(report_error).__name__}\n{details}"
            )
            return

    _write_stderr(details)


def install_exception_hook() -> None:
    """Install a non-fatal handler for unhandled Python/Qt slot exceptions."""
    global _reporter
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("create QApplication before installing the exception hook")
    if _reporter is None:
        _reporter = _ExceptionReporter()
        _reporter.setParent(app)
    sys.excepthook = _handle_exception
