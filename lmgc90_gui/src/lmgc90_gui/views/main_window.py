"""MainWindow — menus, tree dock, tabs, status."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..controller.project_controller import ProjectController
from ..controller.signals import qt_available


def create_main_window(controller: Optional[ProjectController] = None):
    if not qt_available():
        raise ImportError("PyQt6 required (pip install lmgc90-gui[qt])")

    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QAction, QKeySequence
    from PyQt6.QtWidgets import (
        QDockWidget, QFileDialog, QMainWindow, QMessageBox, QStatusBar,
        QTabWidget, QToolBar, QWidget,
    )

    from .tabs.avatar_tab import create_avatar_tab
    from .tabs.contact_tab import create_contact_tab
    from .tabs.dof_tab import create_dof_tab
    from .tabs.granulo_tab import create_granulo_tab
    from .tabs.loop_tab import create_loop_tab
    from .tabs.for_loop_tab import create_for_loop_tab
    from .tabs.material_tab import create_material_tab
    from .tabs.model_tab import create_model_tab
    from .tabs.postpro_tab import create_postpro_tab
    from .tabs.visibility_tab import create_visibility_tab
    from .tabs.viewer_tab import create_viewer_tab
    from .tabs.groups_tab import create_groups_tab
    from .tabs.contactors_tab import create_contactors_tab
    from .tabs.deformable_tab import create_deformable_tab
    from .tabs.masonry_tab import create_masonry_tab
    from .tabs.compute_tab import create_compute_tab
    from .history_dock import create_history_dock
    from .tree_view import create_tree_view
    from .styles import apply_app_style, tab_title, MENU_ICONS, EXPR_HINT_HTML

    class MainWindow(QMainWindow):
        def __init__(self, controller: Optional[ProjectController] = None):
            super().__init__()
            self.controller = controller or ProjectController()
            self.setWindowTitle(f"LMGC90_GUI v0.6.1 — {self.controller.project.name}")
            self.resize(1280, 860)
            apply_app_style(self)
            self._build_ui()
            self._connect()
            self.controller.state_changed.emit()  # initial refresh

        def _build_ui(self) -> None:
            self.tabs = QTabWidget()
            self.tabs.setTabsClosable(True)
            self.tabs.tabCloseRequested.connect(self._on_tab_close_requested)
            self.setCentralWidget(self.tabs)

            self.material_tab = create_material_tab()
            self.model_tab = create_model_tab()
            self.avatar_tab = create_avatar_tab()
            self.loop_tab = create_loop_tab()
            self.for_loop_tab = create_for_loop_tab()
            self.granulo_tab = create_granulo_tab()
            self.contact_tab = create_contact_tab()
            self.visibility_tab = create_visibility_tab()
            self.dof_tab = create_dof_tab()
            self.postpro_tab = create_postpro_tab()
            self.viewer_tab = create_viewer_tab()
            self.groups_tab = create_groups_tab()
            self.contactors_tab = create_contactors_tab()
            self.deformable_tab = create_deformable_tab()
            self.masonry_tab = create_masonry_tab()
            self.compute_tab = create_compute_tab()

            # Registry of all available tabs (id → title, widget, icon)
            from .styles import TAB_ICONS
            self.all_tabs = {
                "material":   ("Materials", self.material_tab, TAB_ICONS.get("Materials", "🧪")),
                "model":      ("Models", self.model_tab, TAB_ICONS.get("Models", "📐")),
                "avatar":     ("Avatars", self.avatar_tab, TAB_ICONS.get("Avatars", "🔵")),
                "loop":       ("Loops", self.loop_tab, TAB_ICONS.get("Loops", "🔁")),
                "for_loop":   ("ForLoop", self.for_loop_tab, TAB_ICONS.get("ForLoop", "🔢")),
                "granulo":    ("Granulo", self.granulo_tab, TAB_ICONS.get("Granulo", "⚪")),
                "contact":    ("Contact", self.contact_tab, TAB_ICONS.get("Contact", "🤝")),
                "visibility": ("Visibility", self.visibility_tab, TAB_ICONS.get("Visibility", "👁️")),
                "dof":        ("DOF", self.dof_tab, TAB_ICONS.get("DOF", "📌")),
                "postpro":    ("Post-pro", self.postpro_tab, TAB_ICONS.get("Post-pro", "📊")),
                "viewer":     ("Visualisation 3D", self.viewer_tab, TAB_ICONS.get("Visualisation 3D", "🎨")),
                "groups":     ("Groups", self.groups_tab, TAB_ICONS.get("Groups", "📁")),
                "contactors": ("Contactors", self.contactors_tab, TAB_ICONS.get("Contactors", "🔗")),
                "deformable": ("Deformable", self.deformable_tab, TAB_ICONS.get("Deformable", "🧩")),
                "masonry":    ("Masonry", self.masonry_tab, TAB_ICONS.get("Masonry", "🧱")),
                "compute":    ("Compute", self.compute_tab, TAB_ICONS.get("Compute", "⚙️")),
            }
            self._default_tab_ids = [
                "material", "model", "avatar", "contact", "visibility", "dof", "viewer",
            ]
            for tid in self._default_tab_ids:
                self._add_tab(tid)

            self.tree = create_tree_view()
            dock = QDockWidget("🌳  Model tree", self)
            dock.setWidget(self.tree)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

            self.history_panel = create_history_dock()
            hist_dock = QDockWidget("🕒  History", self)
            hist_dock.setWidget(self.history_panel)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, hist_dock)

            self._build_menus()
            self.setStatusBar(QStatusBar())
            self._update_status()

            self._all_tabs = (
                self.material_tab, self.model_tab, self.avatar_tab,
                self.loop_tab, self.for_loop_tab, self.granulo_tab, self.contact_tab,
                self.visibility_tab, self.dof_tab, self.postpro_tab, self.viewer_tab,
                self.groups_tab, self.contactors_tab,
                self.deformable_tab, self.masonry_tab, self.compute_tab, self.tree,
            )
            for tab in self._all_tabs:
                tab.bind_controller(self.controller)
            self.history_panel.bind_controller(self.controller)

        def _build_menus(self) -> None:
            mb = self.menuBar()
            file_m = mb.addMenu(f"{MENU_ICONS['file']} &File")

            act_new = QAction(f"{MENU_ICONS['new']} &New", self)
            act_new.setShortcut(QKeySequence.StandardKey.New)
            act_new.triggered.connect(self._on_new)
            file_m.addAction(act_new)

            act_open = QAction(f"{MENU_ICONS['open']} &Open…", self)
            act_open.setShortcut(QKeySequence.StandardKey.Open)
            act_open.triggered.connect(self._on_open)
            file_m.addAction(act_open)

            act_save = QAction(f"{MENU_ICONS['save']} &Save", self)
            act_save.setShortcut(QKeySequence.StandardKey.Save)
            act_save.triggered.connect(self._on_save)
            file_m.addAction(act_save)

            act_save_as = QAction(f"{MENU_ICONS['save']} Save &As…", self)
            act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
            act_save_as.triggered.connect(self._on_save_as)
            file_m.addAction(act_save_as)

            file_m.addSeparator()
            act_quit = QAction("&Quit", self)
            act_quit.setShortcut(QKeySequence.StandardKey.Quit)
            act_quit.triggered.connect(self.close)
            file_m.addAction(act_quit)

            project_m = mb.addMenu("&Project")
            act_dim = QAction("Set &dimension…", self)
            act_dim.triggered.connect(self._on_set_dimension)
            project_m.addAction(act_dim)

            edit = mb.addMenu(f"{MENU_ICONS['edit']} &Edit")
            act_undo = QAction(f"{MENU_ICONS['undo']} Undo", self)
            act_undo.setShortcut(QKeySequence.StandardKey.Undo)
            act_undo.triggered.connect(self._on_undo)
            edit.addAction(act_undo)
            act_redo = QAction(f"{MENU_ICONS['redo']} Redo", self)
            act_redo.setShortcut(QKeySequence.StandardKey.Redo)
            act_redo.triggered.connect(self._on_redo)
            edit.addAction(act_redo)

            tools = mb.addMenu(f"{MENU_ICONS['tools']} &Tools")
            act_pre = QAction("Generate pre.py…", self)
            act_pre.triggered.connect(self._on_export_pre)
            tools.addAction(act_pre)
            act_chipy = QAction("Generate command.py…", self)
            act_chipy.triggered.connect(self._on_export_chipy)
            tools.addAction(act_chipy)
            act_export = QAction("Export all (pre + command [+ DATBOX])…", self)
            act_export.triggered.connect(self._on_export_all)
            tools.addAction(act_export)
            tools.addSeparator()
            act_pipe = QAction(f"{MENU_ICONS['pipeline']} Pipeline / &SLURM…", self)
            act_pipe.triggered.connect(self._on_pipeline)
            tools.addAction(act_pipe)
            act_mesh = QAction(f"{MENU_ICONS['mesh']} Assistant &Mesh déformable…", self)
            act_mesh.triggered.connect(self._on_mesh_wizard)
            tools.addAction(act_mesh)
            act_mas = QAction(f"{MENU_ICONS['masonry']} Assistant M&açonnerie…", self)
            act_mas.triggered.connect(self._on_masonry_wizard)
            tools.addAction(act_mas)
            tools.addSeparator()
            act_dyn = QAction(f"{MENU_ICONS['dynvars']} &Variables dynamiques…", self)
            act_dyn.setShortcut(QKeySequence("Ctrl+V"))
            act_dyn.triggered.connect(self._on_dynamic_vars)
            tools.addAction(act_dyn)
            act_visu = QAction("👁 visuAvatars (pylmgc90)…", self)
            act_visu.triggered.connect(self._on_visu_avatars)
            tools.addAction(act_visu)
            tools.addSeparator()
            act_prefs = QAction(f"{MENU_ICONS['prefs']} &Preferences…", self)
            act_prefs.setShortcut(QKeySequence("Ctrl+,"))
            act_prefs.triggered.connect(self._on_preferences)
            tools.addAction(act_prefs)

            comp = mb.addMenu(f"{MENU_ICONS['computation']} &Computation")
            act_datbox = QAction(f"{MENU_ICONS['datbox']} Generate DATBOX / scripts…", self)
            act_datbox.setShortcut(QKeySequence("Ctrl+F5"))
            act_datbox.triggered.connect(self._on_generate_datbox)
            comp.addAction(act_datbox)
            act_run = QAction(f"{MENU_ICONS['run']} &Run computation", self)
            act_run.setShortcut(QKeySequence("F5"))
            act_run.triggered.connect(self._on_run_computation)
            comp.addAction(act_run)
            act_journal = QAction(f"{MENU_ICONS['journal']} Application &journal", self)
            act_journal.setShortcut(QKeySequence("F7"))
            act_journal.triggered.connect(self._on_journal)
            comp.addAction(act_journal)

            view_m = mb.addMenu(f"{MENU_ICONS['view']} &View")
            act_refresh_view = QAction(f"{MENU_ICONS['refresh']} Refresh &viewer", self)
            act_refresh_view.setShortcut(QKeySequence("F6"))
            act_refresh_view.triggered.connect(self._on_refresh_viewer)
            view_m.addAction(act_refresh_view)

            # ── Menu Onglets (open / close) ─────────────────────────────────
            tabs_m = mb.addMenu("📑 &Onglets")
            open_sub = tabs_m.addMenu("➕ Ouvrir")
            tab_menu_items = [
                ("material", "🧪 Matériaux"),
                ("model", "📐 Modèles"),
                ("avatar", "🔵 Avatars"),
                ("loop", "🔁 Boucles"),
                ("for_loop", "🔢 ForLoop"),
                ("granulo", "⚪ Granulo"),
                ("contact", "🤝 Contact"),
                ("visibility", "👁️ Visibilité"),
                ("dof", "📌 DOF"),
                ("postpro", "📊 Post-pro"),
                ("viewer", "🎨 Visualisation 3D"),
                ("groups", "📁 Groups"),
                ("contactors", "🔗 Contactors"),
                ("deformable", "🧩 Déformable"),
                ("masonry", "🧱 Maçonnerie"),
            ]
            for n, (tid, label) in enumerate(tab_menu_items, 1):
                act = QAction(label, self)
                if n <= 9:
                    act.setShortcut(QKeySequence(f"Ctrl+{n}"))
                act.triggered.connect(lambda checked=False, t=tid: self._add_tab(t))
                open_sub.addAction(act)
            tabs_m.addSeparator()
            act_close_others = QAction("❌ Fermer les autres", self)
            act_close_others.triggered.connect(self._close_other_tabs)
            tabs_m.addAction(act_close_others)
            act_close_all = QAction("🗑️ Fermer tous (sauf essentiels)", self)
            act_close_all.triggered.connect(self._close_all_tabs)
            tabs_m.addAction(act_close_all)
            tabs_m.addSeparator()
            act_defaults = QAction("🔄 Onglets par défaut", self)
            act_defaults.setShortcut(QKeySequence("Ctrl+Alt+D"))
            act_defaults.triggered.connect(self._reopen_default_tabs)
            tabs_m.addAction(act_defaults)

            ex_m = mb.addMenu("📚 &Exemples")
            act_browse = QAction("Bibliothèque d'exemples…", self)
            act_browse.setShortcut(QKeySequence("Ctrl+Shift+E"))
            act_browse.triggered.connect(self._on_browse_examples)
            ex_m.addAction(act_browse)

            help_m = mb.addMenu(f"{MENU_ICONS['help']} &Help")
            act_about = QAction(f"{MENU_ICONS['about']} &About / shortcuts", self)
            act_about.triggered.connect(self._on_about)
            help_m.addAction(act_about)

            tb = QToolBar("Main")
            tb.setMovable(False)
            tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.addToolBar(tb)
            tb.addAction(act_new)
            tb.addAction(act_open)
            tb.addAction(act_save)
            tb.addSeparator()
            tb.addAction(act_run)
            tb.addAction(act_datbox)
            tb.addSeparator()
            tb.addAction(act_dyn)
            tb.addAction(act_refresh_view)

        def _connect(self) -> None:
            self.controller.state_changed.connect(self._update_status)
            self.controller.error_occurred.connect(self._on_error)
            self.controller.project_loaded.connect(self._on_loaded)

        def _update_status(self) -> None:
            p = self.controller.project
            n_vars = len(p.dynamic_vars)
            self.statusBar().showMessage(
                f"📁 {p.name}  ·  {p.dimension}D  ·  🔵 bodies={p.n_bodies}  ·  "
                f"𝑥 vars={n_vars}  ·  "
                f"pylmgc={'✅' if self.controller.pylmgc_available() else '—'}"
            )
            self.setWindowTitle(f"LMGC90_GUI v0.6.1 — {p.name}")

        def _on_error(self, msg: str) -> None:
            QMessageBox.warning(self, "LMGC90_GUI v0.6.1", msg)

        def _on_loaded(self) -> None:
            self._update_status()

        def _on_new(self) -> None:
            from PyQt6.QtWidgets import QInputDialog
            dim, ok = QInputDialog.getItem(
                self, "New project", "Dimension:",
                ["2", "3"], 0, False,
            )
            if not ok:
                return
            name, ok2 = QInputDialog.getText(self, "New project", "Name:", text="untitled")
            if not ok2:
                return
            self.controller.new_project((name or "untitled").strip(), dimension=int(dim))
            self.controller.journal.info(f"New project dimension={dim}")

        def _on_open(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Open project", "", "LMGC90 project (*.lmgc90);;All (*)"
            )
            if path:
                try:
                    self.controller.load_project(path)
                except Exception as exc:
                    QMessageBox.critical(self, "Open", str(exc))

        def _on_save(self) -> None:
            if self.controller.filepath is None:
                self._on_save_as()
                return
            try:
                self.controller.save_project()
                self.statusBar().showMessage(f"Saved {self.controller.filepath}", 3000)
            except Exception as exc:
                QMessageBox.critical(self, "Save", str(exc))

        def _on_save_as(self) -> None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save project", "", "LMGC90 project (*.lmgc90)"
            )
            if path:
                if not path.endswith(".lmgc90"):
                    path += ".lmgc90"
                try:
                    self.controller.save_project(path)
                    self.statusBar().showMessage(f"Saved {path}", 3000)
                except Exception as exc:
                    QMessageBox.critical(self, "Save", str(exc))

        def _on_export_pre(self) -> None:
            path, _ = QFileDialog.getSaveFileName(self, "pre.py", "pre.py", "Python (*.py)")
            if path:
                self.controller.emit_pre_script(path)
                self.statusBar().showMessage(f"Wrote {path}", 3000)

        def _on_export_chipy(self) -> None:
            path, _ = QFileDialog.getSaveFileName(self, "command.py", "command.py", "Python (*.py)")
            if path:
                self.controller.emit_chipy_script(path)
                self.statusBar().showMessage(f"Wrote {path}", 3000)

        def _on_export_all(self) -> None:
            path = QFileDialog.getExistingDirectory(self, "Export directory")
            if path:
                written = self.controller.export_all(path)
                keys = ", ".join(written.keys())
                self.statusBar().showMessage(f"Exported: {keys}", 4000)

        def _on_undo(self) -> None:
            try:
                self.controller.undo()
            except Exception as exc:
                self.statusBar().showMessage(str(exc), 3000)

        def _on_redo(self) -> None:
            try:
                self.controller.redo()
            except Exception as exc:
                self.statusBar().showMessage(str(exc), 3000)


        def _on_set_dimension(self) -> None:
            from PyQt6.QtWidgets import QInputDialog, QMessageBox
            p = self.controller.project
            current = 0 if p.dimension == 2 else 1
            dim, ok = QInputDialog.getItem(
                self, "Project dimension",
                "Change project dimension (models/avatars must stay consistent):",
                ["2", "3"], current, False,
            )
            if not ok:
                return
            new_dim = int(dim)
            if new_dim == p.dimension:
                return
            # Warn if models exist with other dim
            bad = [m.name for m in p.models if m.dimension != new_dim]
            if bad:
                r = QMessageBox.question(
                    self, "Dimension",
                    f"Models with different dimension will become invalid: {', '.join(bad)}.\n"
                    "Continue?",
                )
                if r != QMessageBox.StandardButton.Yes:
                    return
            p.dimension = new_dim
            self.controller.session.mark_dirty()
            self.controller.journal.info(f"Project dimension set to {new_dim}D")
            self.controller.state_changed.emit()
            self._update_status()

        def _on_mesh_wizard(self) -> None:
            from ..dialogs.mesh_wizard import create_mesh_wizard
            create_mesh_wizard(self.controller, self).exec()

        def _on_masonry_wizard(self) -> None:
            from ..dialogs.masonry_wizard import create_masonry_wizard
            create_masonry_wizard(self.controller, self).exec()

        def _on_visu_avatars(self) -> None:
            try:
                if not self.controller.pylmgc_available():
                    QMessageBox.warning(self, "visuAvatars", "pylmgc90 non disponible")
                    return
                self.controller.visu_avatars(force=True)
            except Exception as exc:
                QMessageBox.critical(self, "visuAvatars", str(exc))

        def _on_dynamic_vars(self) -> None:
            from ..dialogs.dynamic_vars_dialog import create_dynamic_vars_dialog
            create_dynamic_vars_dialog(self.controller, self).exec()


        # ── Tab lifecycle (like legacy MainWindowTabsMixin) ─────────────────
        def _add_tab(self, tab_id: str) -> None:
            """Open tab if not already open; otherwise focus it."""
            if tab_id not in self.all_tabs:
                return
            title, widget, icon = self.all_tabs[tab_id]
            for i in range(self.tabs.count()):
                if self.tabs.widget(i) is widget:
                    self.tabs.setCurrentIndex(i)
                    return
            idx = self.tabs.addTab(widget, f"{icon}  {title}")
            self.tabs.setCurrentIndex(idx)

        def _on_tab_close_requested(self, index: int) -> None:
            widget = self.tabs.widget(index)
            name = self.tabs.tabText(index)
            essential = {self.material_tab, self.model_tab}
            if widget in essential:
                QMessageBox.warning(
                    self, "Onglet essentiel",
                    f"L'onglet « {name} » est essentiel et ne peut pas être fermé.",
                )
                return
            self.tabs.removeTab(index)

        def _close_other_tabs(self) -> None:
            current = self.tabs.currentIndex()
            essential = {self.material_tab, self.model_tab}
            for i in range(self.tabs.count() - 1, -1, -1):
                w = self.tabs.widget(i)
                if i != current and w not in essential:
                    self.tabs.removeTab(i)

        def _close_all_tabs(self) -> None:
            essential = {self.material_tab, self.model_tab}
            for i in range(self.tabs.count() - 1, -1, -1):
                if self.tabs.widget(i) not in essential:
                    self.tabs.removeTab(i)

        def _reopen_default_tabs(self) -> None:
            for tid in getattr(self, "_default_tab_ids", ["material", "model", "avatar"]):
                self._add_tab(tid)


        def _on_pipeline(self) -> None:
            from ..dialogs.pipeline_dialog import create_pipeline_dialog
            dlg = create_pipeline_dialog(self.controller, self)
            dlg.exec()


        def _on_browse_examples(self) -> None:
            from ..dialogs.examples_dialog import create_examples_dialog
            dlg = create_examples_dialog(self)
            if dlg.exec():
                ex = dlg.selected_example()
                if ex is not None:
                    self._load_example(ex)

        def _load_example(self, example) -> None:
            from PyQt6.QtWidgets import QMessageBox
            r = QMessageBox.question(
                self,
                "Charger l'exemple",
                f"Remplacer le projet courant par\n« {example.title} » ?",
            )
            if r != QMessageBox.StandardButton.Yes:
                return
            try:
                self.controller.new_project(example.id, dimension=int(example.dimension))
                self.controller.apply_scene(example.scene)
                self.controller.journal.info(f"Example loaded: {example.id}")
                self.statusBar().showMessage(f"Exemple chargé : {example.title}", 5000)
                self._update_status()
            except Exception as exc:
                QMessageBox.critical(self, "Exemple", str(exc))
                try:
                    self.controller.journal.exception("example load failed", exc)
                except Exception:
                    pass

        def _on_about(self) -> None:
            from ..dialogs.about_dialog import create_about_dialog
            create_about_dialog(self).exec()

        def _on_refresh_viewer(self) -> None:
            try:
                self.tabs.setCurrentWidget(self.viewer_tab)
                self.viewer_tab.refresh()
            except Exception as exc:
                QMessageBox.warning(self, "Viewer", str(exc))

        def _on_preferences(self) -> None:
            from ..dialogs.preferences_dialog import create_preferences_dialog
            dlg = create_preferences_dialog(self.controller.prefs, self)
            if dlg.exec():
                dlg.apply_to(self.controller.prefs)
                self.controller.save_preferences()
                self.statusBar().showMessage("Preferences saved", 3000)

        def _on_journal(self) -> None:
            from ..dialogs.journal_dialog import create_journal_dialog
            dlg = create_journal_dialog(self)
            dlg.show()
            self._journal_dlg = dlg

        def _on_generate_datbox(self) -> None:
            from pathlib import Path as _P
            from ..workers.datbox_worker import create_datbox_worker
            start = str(self.controller.work_dir or _P.cwd())
            path = QFileDialog.getExistingDirectory(self, "Output directory for DATBOX / scripts", start)
            if not path:
                return
            self.controller.journal.info(f"DATBOX generation requested → {path}")
            self.statusBar().showMessage("Generating scripts / DATBOX…")
            runner = create_datbox_worker(
                self.controller,
                _P(path),
                try_live_datbox=self.controller.prefs.auto_write_datbox,
                chipy_params=self.controller.prefs.chipy_params(),
            )
            self._datbox_runner = runner

            def on_progress(msg: str):
                self.statusBar().showMessage(msg)
                self.controller.journal.info(msg)

            def on_finished(paths: dict):
                keys = ", ".join(paths.keys())
                self.statusBar().showMessage(f"Done: {keys}", 5000)
                self.controller.journal.info(f"Generation finished: {paths}")
                self.controller.set_work_dir(path)
                lines = "\n".join(f"{k}: {v}" for k, v in paths.items())
                QMessageBox.information(self, "DATBOX / scripts", f"Written:\n{lines}")

            def on_failed(msg: str):
                self.controller.journal.error(msg)
                QMessageBox.critical(self, "DATBOX", msg)
                self.statusBar().showMessage("DATBOX failed", 4000)

            runner.worker.progress.connect(on_progress)
            runner.worker.finished.connect(on_finished)
            runner.worker.failed.connect(on_failed)
            runner.start()

        def _show_tab(self, key: str) -> None:
            meta = self.all_tabs.get(key)
            if not meta:
                return
            title, widget, icon = meta
            for i in range(self.tabs.count()):
                if self.tabs.widget(i) is widget:
                    self.tabs.setCurrentIndex(i)
                    return
            # reopen closed tab
            idx = self.tabs.addTab(widget, f"{icon} {title}" if icon else title)
            self.tabs.setCurrentIndex(idx)

        def _on_run_computation(self) -> None:

            # Prefer dedicated Compute tab when available
            try:
                if hasattr(self, "compute_tab") and self.compute_tab is not None:
                    self._show_tab("compute")
                    self.compute_tab.run_computation()
                    return
            except Exception:
                pass
            from pathlib import Path as _P
            from ..dialogs.compute_log_dialog import create_compute_log_dialog
            from ..workers.compute_worker import create_compute_worker

            work = self.controller.work_dir
            if work is None or not (_P(work) / "command.py").is_file():
                path = QFileDialog.getExistingDirectory(
                    self,
                    "Select directory with command.py (or empty folder to prepare)",
                    str(work or _P.cwd()),
                )
                if not path:
                    return
                work = _P(path)
                if not (work / "command.py").is_file():
                    try:
                        self.controller.prepare_run_directory(work)
                    except Exception as exc:
                        QMessageBox.critical(self, "Prepare", str(exc))
                        return
            else:
                work = _P(work)

            if self.controller.prefs.confirm_run:
                r = QMessageBox.question(
                    self,
                    "Run computation",
                    f"Run chipy in:\n{work}\n\n{self.controller.prefs.python_executable} command.py",
                )
                if r != QMessageBox.StandardButton.Yes:
                    return

            log = create_compute_log_dialog(self)
            self._compute_log = log
            runner = create_compute_worker(
                work,
                python_executable=self.controller.prefs.python_executable,
            )
            self._compute_runner = runner
            log.set_stop_callback(runner.stop)

            def on_line(line: str):
                log.append_line(line)
                self.controller.journal.info(line)

            def on_finished(rc: int):
                log.mark_finished(rc)
                self.controller.journal.info(f"Computation finished rc={rc}")
                self.statusBar().showMessage(f"Computation finished (rc={rc})", 5000)

            def on_failed(msg: str):
                log.mark_failed(msg)
                self.controller.journal.error(msg)
                self.statusBar().showMessage("Computation failed", 4000)

            runner.worker.line_out.connect(on_line)
            runner.worker.finished.connect(on_finished)
            runner.worker.failed.connect(on_failed)
            log.show()
            self.controller.journal.info(f"Starting computation in {work}")
            runner.start()


    return MainWindow(controller)
