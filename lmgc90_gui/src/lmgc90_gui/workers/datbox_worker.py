"""Background DATBOX generation: materialize + writeDatbox + emit scripts."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_datbox_worker(
    controller: "ProjectController",
    output_dir: Path,
    *,
    try_live_datbox: bool = True,
    chipy_params: Optional[dict[str, Any]] = None,
):
    from PyQt6.QtCore import QObject, QThread, pyqtSignal

    class DatboxWorker(QObject):
        finished = pyqtSignal(dict)   # paths written
        failed = pyqtSignal(str)
        progress = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.controller = controller
            self.output_dir = Path(output_dir)
            self.try_live = try_live_datbox
            self.chipy_params = chipy_params or {}

        def run(self) -> None:
            try:
                try:
                    from lmgc90_core.numpy_compat import patch_numpy_cross
                    patch_numpy_cross()
                except Exception:
                    pass
                out = self.output_dir
                out.mkdir(parents=True, exist_ok=True)
                paths: dict[str, str] = {}

                self.progress.emit("Writing pre.py…")
                pre_path = out / "pre.py"
                self.controller.emit_pre_script(pre_path)
                paths["pre"] = str(pre_path)

                self.progress.emit("Writing command.py…")
                cmd_path = out / "command.py"
                self.controller.emit_chipy_script(cmd_path, **self.chipy_params)
                paths["command"] = str(cmd_path)

                if self.try_live and self.controller.pylmgc_available():
                    self.progress.emit("Materializing pylmgc objects…")
                    self.controller.materialize(force=True)
                    self.progress.emit("Writing DATBOX…")
                    db = self.controller.write_datbox(out / "DATBOX")
                    paths["datbox"] = str(db)
                else:
                    self.progress.emit(
                        "pylmgc90 not available — scripts only "
                        "(run pre.py on a node with pylmgc90 to build DATBOX)"
                    )

                self.finished.emit(paths)
            except Exception as exc:
                self.failed.emit(str(exc))

    class Runner:
        def __init__(self):
            self.thread = QThread()
            self.worker = DatboxWorker()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.failed.connect(self.thread.quit)

        def start(self) -> None:
            self.thread.start()

    return Runner()
