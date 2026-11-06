import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QMessageBox

from lmgc90_gui import ProjectController
from lmgc90_gui.views.main_window import create_main_window


def test_close_event_respects_unsaved_changes_confirmation(monkeypatch):
    app = QApplication.instance() or QApplication([])
    controller = ProjectController()
    window = create_main_window(controller)
    window._confirm_unsaved_changes = lambda: False

    cancelled = QCloseEvent()
    window.closeEvent(cancelled)
    assert cancelled.isAccepted() is False

    window._confirm_unsaved_changes = lambda: True
    accepted = QCloseEvent()
    window.closeEvent(accepted)
    assert accepted.isAccepted() is True
    window.deleteLater()
    app.processEvents()


def test_window_initializes_recent_menu_and_autosave_timer(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    controller = ProjectController()
    existing = tmp_path / "recent.lmgc90"
    existing.touch()
    controller.prefs.recent_projects = [str(existing)]
    controller.prefs.auto_save = True
    controller.prefs.auto_save_interval_min = 2
    window = create_main_window(controller)

    assert [action.text() for action in window.recent_menu.actions()] == [
        str(existing), "", "Vider la liste",
    ]
    assert window._autosave_timer.isActive()
    assert window._autosave_timer.interval() == 120_000

    controller.save_preferences = lambda: Path(tmp_path / "prefs.json")
    window._remember_recent(existing)
    assert controller.prefs.recent_projects[0] == str(existing.resolve())
    assert window.recent_menu.actions()[0].text() == str(existing.resolve())
    window.close()
    window.deleteLater()
    app.processEvents()


def test_autosave_saves_modified_named_project(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    controller = ProjectController()
    controller.prefs.auto_save = False
    controller.new_project("autosave", dimension=2)
    path = tmp_path / "autosave.lmgc90"
    controller.save_project(path)
    controller.add(
        controller.pre().material(name="STEEL", materialType="RIGID", density=7800)
    )
    controller.save_preferences = lambda: Path(tmp_path / "prefs.json")
    window = create_main_window(controller)

    window._on_autosave_tick()

    assert not controller.modified
    assert path.is_file()
    window.close()
    window.deleteLater()
    app.processEvents()


def test_loaded_project_warnings_are_shown_and_logged(monkeypatch):
    app = QApplication.instance() or QApplication([])
    controller = ProjectController()
    window = create_main_window(controller)
    controller.project.load_warnings = [
        "population sidecar 'demo.populations.npz' not found",
        "population abc: sidecar integrity check failed, population skipped",
    ]
    shown = []
    logged = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: shown.append(args),
    )
    monkeypatch.setattr(
        controller.journal,
        "warning",
        lambda message: logged.append(message),
    )

    window._on_loaded()

    assert len(shown) == 1
    assert "not found" in shown[0][2]
    assert "population skipped" in shown[0][2]
    assert len(logged) == 1
    assert "2 warning(s)" in logged[0]
    window.close()
    window.deleteLater()
    app.processEvents()
