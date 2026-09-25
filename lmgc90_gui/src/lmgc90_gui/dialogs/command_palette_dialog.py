"""Command palette (Ctrl+K) — fuzzy filter over app actions.

Inspired by the legacy LMGC90_GUI command palette: quick access to menus,
tabs, export, compute, examples without navigating the menu bar.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


def create_command_palette(parent, commands: list[dict[str, Any]]):
    """Show a modal filterable command list.

    Each command dict::

        {"id": str, "label": str, "category": str, "shortcut": str, "callback": callable}
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtWidgets import (
        QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
        QVBoxLayout,
    )

    class CommandPalette(QDialog):
        def __init__(self, parent, commands: list[dict[str, Any]]):
            super().__init__(parent)
            self.setWindowTitle("Palette de commandes")
            self.setModal(True)
            self.setMinimumSize(520, 380)
            self._commands = list(commands)
            self._filtered: list[dict[str, Any]] = list(commands)
            self._chosen: Optional[dict[str, Any]] = None

            lay = QVBoxLayout(self)
            lay.setContentsMargins(10, 10, 10, 10)
            hint = QLabel(
                "Tapez pour filtrer · ↑↓ pour naviguer · Entrée pour exécuter · Échap pour fermer"
            )
            hint.setStyleSheet("color:#888; font-size:11px;")
            lay.addWidget(hint)

            self.search = QLineEdit()
            self.search.setPlaceholderText("Commande, onglet, export, exemple…")
            self.search.setClearButtonEnabled(True)
            self.search.textChanged.connect(self._on_filter)
            lay.addWidget(self.search)

            self.list = QListWidget()
            self.list.itemActivated.connect(self._on_activate)
            self.list.itemDoubleClicked.connect(self._on_activate)
            lay.addWidget(self.list, stretch=1)

            foot = QLabel(f"{len(self._commands)} commandes")
            foot.setObjectName("palette_foot")
            foot.setStyleSheet("color:#666; font-size:10px;")
            self._foot = foot
            lay.addWidget(foot)

            self._refill("")
            self.search.setFocus()

        def _score(self, query: str, cmd: dict) -> int:
            q = query.strip().lower()
            if not q:
                return 1
            label = (cmd.get("label") or "").lower()
            cat = (cmd.get("category") or "").lower()
            cid = (cmd.get("id") or "").lower()
            blob = f"{label} {cat} {cid}"
            if q == label:
                return 100
            if label.startswith(q):
                return 80
            if q in label:
                return 60
            if q in cat or q in cid:
                return 40
            # token AND
            parts = q.split()
            if parts and all(p in blob for p in parts):
                return 30
            return 0

        def _refill(self, query: str) -> None:
            scored = []
            for cmd in self._commands:
                s = self._score(query, cmd)
                if s > 0:
                    scored.append((s, cmd))
            scored.sort(key=lambda x: (-x[0], x[1].get("category", ""), x[1].get("label", "")))
            self._filtered = [c for _, c in scored]
            self.list.clear()
            for cmd in self._filtered:
                cat = cmd.get("category") or ""
                sc = cmd.get("shortcut") or ""
                text = f"{cmd.get('label', '')}"
                if cat:
                    text = f"[{cat}]  {text}"
                if sc:
                    text = f"{text}    ({sc})"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, cmd)
                self.list.addItem(item)
            if self.list.count():
                self.list.setCurrentRow(0)
            self._foot.setText(f"{len(self._filtered)} / {len(self._commands)} commandes")

        def _on_filter(self, text: str) -> None:
            self._refill(text)

        def _on_activate(self, item=None) -> None:
            it = item or self.list.currentItem()
            if it is None:
                return
            cmd = it.data(Qt.ItemDataRole.UserRole)
            self._chosen = cmd
            self.accept()

        def keyPressEvent(self, event) -> None:
            key = event.key()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._on_activate()
                return
            if key == Qt.Key.Key_Down:
                row = min(self.list.currentRow() + 1, self.list.count() - 1)
                self.list.setCurrentRow(max(0, row))
                return
            if key == Qt.Key.Key_Up:
                row = max(self.list.currentRow() - 1, 0)
                self.list.setCurrentRow(row)
                return
            if key == Qt.Key.Key_Escape:
                self.reject()
                return
            super().keyPressEvent(event)

        def chosen(self) -> Optional[dict[str, Any]]:
            return self._chosen

    dlg = CommandPalette(parent, commands)
    if dlg.exec():
        cmd = dlg.chosen()
        if cmd and callable(cmd.get("callback")):
            try:
                cmd["callback"]()
            except Exception as exc:
                try:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(parent, "Commande", str(exc))
                except Exception:
                    pass
                raise
    return dlg


def collect_window_commands(window) -> list[dict[str, Any]]:
    """Harvest QActions from the menu bar + synthetic tab / utility commands."""
    from PyQt6.QtWidgets import QMenu

    commands: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(cid: str, label: str, category: str, callback: Callable, shortcut: str = "") -> None:
        key = f"{category}:{label}"
        if key in seen:
            return
        seen.add(key)
        commands.append({
            "id": cid,
            "label": label,
            "category": category,
            "shortcut": shortcut,
            "callback": callback,
        })

    # Menu bar actions
    try:
        mb = window.menuBar()
        for action in mb.actions():
            menu = action.menu()
            if menu is None:
                continue
            cat = (action.text() or "Menu").replace("&", "").strip()
            for act in menu.actions():
                if act.isSeparator():
                    continue
                sub = act.menu()
                if sub is not None:
                    for subact in sub.actions():
                        if subact.isSeparator() or not subact.isEnabled():
                            continue
                        label = (subact.text() or "").replace("&", "").strip()
                        if not label:
                            continue
                        sc = subact.shortcut().toString() if subact.shortcut() else ""
                        add(
                            f"menu.{cat}.{label}",
                            label,
                            cat,
                            (lambda a=subact: a.trigger()),
                            sc,
                        )
                    continue
                if not act.isEnabled():
                    continue
                label = (act.text() or "").replace("&", "").strip()
                if not label:
                    continue
                sc = act.shortcut().toString() if act.shortcut() else ""
                add(
                    f"menu.{cat}.{label}",
                    label,
                    cat,
                    (lambda a=act: a.trigger()),
                    sc,
                )
    except Exception:
        pass

    # Open any registered tab
    all_tabs = getattr(window, "all_tabs", None) or {}
    for tid, meta in all_tabs.items():
        try:
            title, _w, icon = meta
        except Exception:
            title, icon = tid, ""
        label = f"{icon} Ouvrir onglet « {title} »" if icon else f"Ouvrir onglet « {title} »"
        add(
            f"tab.open.{tid}",
            label,
            "Onglets",
            (lambda t=tid: window._ensure_tab(t) if hasattr(window, "_ensure_tab")
             else window._add_tab(t) if hasattr(window, "_add_tab") else None),
            "",
        )

    # Palette itself (no-op if already open)
    add("palette", "Palette de commandes", "Navigation", lambda: None, "Ctrl+K")

    return commands
