"""Reusable QTreeWidget for entity lists (CRUD selection)."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional, Sequence


def create_entity_tree(
    headers: Sequence[str],
    *,
    parent=None,
    on_select: Optional[Callable[[Any], None]] = None,
):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QAbstractItemView, QTreeWidget, QTreeWidgetItem

    class EntityTree(QTreeWidget):
        def __init__(self):
            super().__init__(parent)
            self.setColumnCount(len(headers))
            self.setHeaderLabels(list(headers))
            self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.setAlternatingRowColors(True)
            self.setUniformRowHeights(True)
            self.setRootIsDecorated(False)
            self.setSortingEnabled(True)
            self.itemSelectionChanged.connect(self._on_sel)
            self._on_select = on_select
            self._payload_role = Qt.ItemDataRole.UserRole

        def set_on_select(self, cb: Callable[[Any], None]) -> None:
            self._on_select = cb

        def _on_sel(self) -> None:
            if self._on_select is None:
                return
            payload = self.selected_payload()
            if payload is not None:
                self._on_select(payload)

        def selected_payload(self) -> Any:
            items = self.selectedItems()
            if not items:
                return None
            return items[0].data(0, self._payload_role)

        def clear_rows(self) -> None:
            self.clear()

        def set_rows(self, rows: Iterable[tuple[Sequence[str], Any]]) -> None:
            """Replace all rows: ``rows`` is iterable of ``(columns, payload)``."""
            self.blockSignals(True)
            self.clear()
            for columns, payload in rows:
                item = QTreeWidgetItem([str(c) for c in columns])
                item.setData(0, self._payload_role, payload)
                self.addTopLevelItem(item)
            self.blockSignals(False)
            self.resize_columns()

        def add_row(self, columns: Sequence[str], payload: Any) -> QTreeWidgetItem:
            item = QTreeWidgetItem([str(c) for c in columns])
            item.setData(0, self._payload_role, payload)
            self.addTopLevelItem(item)
            return item

        def resize_columns(self) -> None:
            for i in range(self.columnCount()):
                self.resizeColumnToContents(i)

        def select_payload(self, payload: Any, match: Callable[[Any, Any], bool] | None = None) -> None:
            eq = match or (lambda a, b: a == b)
            for i in range(self.topLevelItemCount()):
                it = self.topLevelItem(i)
                if eq(it.data(0, self._payload_role), payload):
                    self.setCurrentItem(it)
                    return

    return EntityTree()
