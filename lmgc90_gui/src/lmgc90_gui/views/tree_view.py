"""Model tree — read-only overview of Project state."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def create_tree_view(parent=None):
    from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

    class TreeView(QTreeWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setHeaderLabels(["Model", "Detail"])
            self.setColumnCount(2)

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.clear()

            def branch(title: str, rows: list[tuple[str, str]]) -> None:
                top = QTreeWidgetItem([title, str(len(rows))])
                for a, b in rows:
                    top.addChild(QTreeWidgetItem([a, b]))
                self.addTopLevelItem(top)
                top.setExpanded(True)

            branch("Materials", [(m.name, f"{m.material_type.value} ρ={m.density}") for m in p.materials])
            branch("Models", [(m.name, f"{m.physics}/{m.element} {m.dimension}D") for m in p.models])
            branch(
                "Avatars (AoS)",
                [
                    (a.avatar_id[:8] + "…", f"{a.avatar_type.value} @ {a.center}")
                    for a in p.avatars
                ],
            )
            branch(
                "Populations (SoA)",
                [
                    (pop.population_id[:12] + "…", f"n={len(pop)} {pop.avatar_type.value}")
                    for pop in p.populations
                ],
            )
            branch("Laws", [(l.name, l.law_type.value) for l in p.laws])
            branch("Visibility", [(f"see[{i}]", r.behavior_name) for i, r in enumerate(p.visibility)])
            branch("DOF", [(op.operation_type, f"{op.target_type}={op.target_value}") for op in p.operations])
            branch("Groups", [(n, f"{len(ids)} ids") for n, ids in p.avatar_groups.items()])

    return TreeView(parent)
