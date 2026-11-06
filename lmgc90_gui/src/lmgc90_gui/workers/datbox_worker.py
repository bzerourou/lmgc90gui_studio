"""Background DATBOX generation: materialize + writeDatbox + emit scripts."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from lmgc90_engine import EngineSession

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_datbox_worker(
    controller: "ProjectController",
    output_dir: Path,
    *,
    try_live_datbox: bool = True,
    chipy_params: Optional[dict[str, Any]] = None,
    use_loop: bool = False,
):
    from PyQt6.QtCore import QObject, QThread, pyqtSignal

    project_snapshot = deepcopy(controller.project)
    session = EngineSession(project_snapshot)
    params = dict(controller.prefs.chipy_params())
    params["nb_steps"] = controller.prefs.nb_steps
    params.update(chipy_params or {})
    live_datbox_available = try_live_datbox and controller.pylmgc_available()

    class DatboxWorker(QObject):
        finished = pyqtSignal(dict)   # paths written
        failed = pyqtSignal(str)
        progress = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.session = session
            self.output_dir = Path(output_dir)
            self.try_live = live_datbox_available
            self.chipy_params = params

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
                self.session.emit_pre_script(pre_path, use_loop=use_loop)
                paths["pre"] = str(pre_path)

                self.progress.emit("Writing command.py…")
                cmd_path = out / "command.py"
                self.session.emit_chipy_script(cmd_path, **self.chipy_params)
                paths["command"] = str(cmd_path)

                if self.try_live:
                    self.progress.emit("Materializing pylmgc objects…")
                    self.session.materialize(force=True)
                    self.progress.emit("Writing DATBOX…")
                    db = self.session.write_datbox(out / "DATBOX")
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
