"""Run command.py (chipy) in a subprocess so the UI stays responsive."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def create_compute_worker(
    work_dir: Path,
    *,
    command_script: str = "command.py",
    python_executable: str = "python",
    env: Optional[dict] = None,
):
    from PyQt6.QtCore import QObject, QThread, pyqtSignal

    class ComputeWorker(QObject):
        line_out = pyqtSignal(str)
        finished = pyqtSignal(int)   # return code
        failed = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.work_dir = Path(work_dir)
            self.command_script = command_script
            self.python = python_executable
            self.env = env
            self._proc: Optional[subprocess.Popen] = None
            self._stop = False

        def stop(self) -> None:
            self._stop = True
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass

        def run(self) -> None:
            script = self.work_dir / self.command_script
            if not script.is_file():
                self.failed.emit(f"Script not found: {script}")
                return
            try:
                env = os.environ.copy()
                if self.env:
                    env.update(self.env)
                self._proc = subprocess.Popen(
                    [self.python, str(script)],
                    cwd=str(self.work_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                )
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    if self._stop:
                        break
                    self.line_out.emit(line.rstrip("\n"))
                rc = self._proc.wait()
                self.finished.emit(rc)
            except Exception as exc:
                self.failed.emit(str(exc))

    class Runner:
        def __init__(self):
            self.thread = QThread()
            self.worker = ComputeWorker()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.failed.connect(self.thread.quit)

        def start(self) -> None:
            self.thread.start()

        def stop(self) -> None:
            self.worker.stop()

    return Runner()
