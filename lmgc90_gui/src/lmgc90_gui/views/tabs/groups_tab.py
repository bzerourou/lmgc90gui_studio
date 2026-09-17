"""GroupsTab — create / edit / delete avatar groups (by stable avatar_id)."""
from __future__ import annotations

from lmgc90_core import ValidationError

from .base_tab import BaseTab
from ...utils.naming import unique_name


def create_groups_tab(parent=None):
    from PyQt6.QtWidgets import (
        QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
        QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class GroupsTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)

            layout.addWidget(QLabel("Existing groups"))
            self.group_list = QListWidget()
            self.group_list.currentTextChanged.connect(self._on_group_selected)
            layout.addWidget(self.group_list)

            layout.addWidget(QLabel("Members (avatar_id) — multi-select from all avatars"))
            self.member_list = QListWidget()
            self.member_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            layout.addWidget(self.member_list)

            row = QHBoxLayout()
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText("group name")
            btn_new = QPushButton("New / Update")
            btn_rm = QPushButton("Delete group")
            btn_new.clicked.connect(self._on_save)
            btn_rm.clicked.connect(self._on_delete)
            row.addWidget(self.name_edit)
            row.addWidget(btn_new)
            row.addWidget(btn_rm)
            layout.addLayout(row)
            layout.addWidget(QLabel(
                "Groups are used by DOF targets and visibility workflows. "
                "Identity = avatar_id, never list index."
            ))

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            cur = self.group_list.currentItem().text() if self.group_list.currentItem() else ""
            self.group_list.clear()
            for name, ids in sorted(p.avatar_groups.items()):
                self.group_list.addItem(f"{name}  ({len(ids)})")
            if cur:
                for i in range(self.group_list.count()):
                    if self.group_list.item(i).text().startswith(cur.split()[0]):
                        self.group_list.setCurrentRow(i)
                        break
            # all avatars as candidates
            selected_ids = {
                self.member_list.item(i).data(256)
                for i in range(self.member_list.count())
                if self.member_list.item(i).isSelected()
            }
            self.member_list.clear()
            for av in p.avatars:
                label = f"{av.avatar_id[:10]}…  {av.avatar_type.value}  @ {av.center}"
                item = QListWidgetItem(label)
                item.setData(256, av.avatar_id)  # Qt.UserRole
                self.member_list.addItem(item)
                if av.avatar_id in selected_ids:
                    item.setSelected(True)
            if not self.name_edit.text().strip():
                existing = list(p.avatar_groups.keys())
                self.name_edit.setText(unique_name("GRP", existing, max_len=8))

        def _on_group_selected(self, text: str) -> None:
            if self.controller is None or not text:
                return
            name = text.split()[0]
            self.name_edit.setText(name)
            ids = set(self.controller.project.avatar_groups.get(name, []))
            for i in range(self.member_list.count()):
                item = self.member_list.item(i)
                item.setSelected(item.data(256) in ids)

        def _on_save(self) -> None:
            if self.controller is None:
                return
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Groups", "Group name required")
                return
            ids = [
                self.member_list.item(i).data(256)
                for i in range(self.member_list.count())
                if self.member_list.item(i).isSelected()
            ]
            if not ids:
                QMessageBox.warning(self, "Groups", "Select at least one avatar")
                return
            try:
                self.controller.group(name, ids)
                self.controller.journal.info(f"Group {name!r} = {len(ids)} avatars")
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Groups", str(exc))

        def _on_delete(self) -> None:
            if self.controller is None:
                return
            name = self.name_edit.text().strip()
            if not name or name not in self.controller.project.avatar_groups:
                return
            # empty group via group(name, [])
            try:
                self.controller.remove_group(name)
                self.controller.journal.info(f"Group {name!r} deleted")
            except Exception as exc:
                QMessageBox.warning(self, "Groups", str(exc))

    return GroupsTab(parent)
