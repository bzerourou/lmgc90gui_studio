"""Application entry point."""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    try:
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

    controller = ProjectController()
    window = create_main_window(controller)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
