"""Application entry point."""
from __future__ import annotations

import sys
from pathlib import Path


def _app_icon_path() -> Path | None:
    """Locate packaged app.ico (editable install or frozen)."""
    candidates = [
        Path(__file__).resolve().parent / "resources" / "app.ico",
        Path(__file__).resolve().parent / "resources" / "app.png",
        Path(__file__).resolve().parents[2] / "app.ico",  # package root
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    try:
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print(
            "PyQt6 is required to run the GUI.\n"
            "  pip install 'lmgc90-gui[qt]'\n"
            "Or use the controller headless:\n"
            "  from lmgc90_gui import ProjectController",
            file=sys.stderr,
        )
        return 1

    from .controller.project_controller import ProjectController
    from .views.main_window import create_main_window

    app = QApplication(argv)
    app.setApplicationName("LMGC90_GUI")
    app.setOrganizationName("LMGC90")

    icon_path = _app_icon_path()
    if icon_path is not None:
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)

    controller = ProjectController()
    window = create_main_window(controller)
    if icon_path is not None:
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
