"""Model tree — read-only overview of Project state."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from ..controller.project_controller import ProjectController


def _avatar_rows(avatars, prefs) -> Optional[tuple[list[tuple[str, str]], str]]:
    if not prefs.show_avatars_in_tree:
        return None
    visible = list(avatars)
    if not prefs.show_granulo_individually:
        visible = [
            avatar for avatar in visible
            if getattr(avatar.origin, "value", avatar.origin) != "granulo"
        ]
    shown = visible[:max(0, int(prefs.max_tree_avatars))]
    rows = [
        (
            avatar.avatar_id[:8] + "…",
            f"{avatar.avatar_type.value} @ {avatar.center}",
        )
        for avatar in shown
    ]
    omitted = len(visible) - len(shown)
    if omitted:
        label = "avatar masqué" if omitted == 1 else "avatars masqués"
        rows.append(("…", f"{omitted} {label} (limite soft)"))
    return rows, f"{len(shown)}/{len(visible)}"


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

            def branch(
                title: str,
                rows: list[tuple[str, str]],
                count: Optional[str] = None,
            ) -> None:
                top = QTreeWidgetItem([title, count or str(len(rows))])
                for a, b in rows:
                    top.addChild(QTreeWidgetItem([a, b]))
                self.addTopLevelItem(top)
                top.setExpanded(True)

            branch("Materials", [(m.name, f"{m.material_type.value} ρ={m.density}") for m in p.materials])
            branch("Models", [(m.name, f"{m.physics}/{m.element} {m.dimension}D") for m in p.models])
            prefs = self.controller.prefs
            avatar_content = _avatar_rows(p.avatars, prefs)
            if avatar_content is not None:
                rows, count = avatar_content
                branch("Avatars (AoS)", rows, count)
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
