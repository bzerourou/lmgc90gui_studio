"""Run EngineSession.materialize() off the UI thread."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_materialize_worker(controller: "ProjectController"):
    from PyQt6.QtCore import QObject, QThread, pyqtSignal

    class MaterializeWorker(QObject):
        finished = pyqtSignal(object)  # MaterializedScene or None
        failed = pyqtSignal(str)

        def __init__(self, controller: "ProjectController"):
            super().__init__()
            self.controller = controller

        def run(self) -> None:
            try:
                scene = self.controller.materialize(force=True)
                self.finished.emit(scene)
            except Exception as exc:
                self.failed.emit(str(exc))

    class Runner:
        def __init__(self, controller: "ProjectController"):
            self.thread = QThread()
            self.worker = MaterializeWorker(controller)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.failed.connect(self.thread.quit)

        def start(self) -> None:
            self.thread.start()

    return Runner(controller)
