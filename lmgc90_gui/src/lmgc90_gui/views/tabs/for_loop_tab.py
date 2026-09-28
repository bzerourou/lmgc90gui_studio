"""ForLoopTab — multi-target parametric loops (legacy parity).

Targets: avatar, material, model, dof, visibility, granulo, granulo_dist.
"""
from __future__ import annotations

from lmgc90_core import ForLoop, ValidationError

from .base_tab import BaseTab
from ...utils.naming import suggest_group_name

_TARGETS = [
    ("avatar", "Avatars (template géométrie)"),
    ("material", "Matériaux (densité / nom)"),
    ("model", "Modèles"),
    ("dof", "DOF / conditions aux limites"),
    ("visibility", "Tables de visibilité (see)"),
    ("granulo", "Granulo — dépôt avec avatars/SoA"),
    ("granulo_dist", "Granulo — distribution rayons seule"),
]


def create_for_loop_tab(parent=None):
    from PyQt6.QtWidgets import (
        QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
        QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget,
    )

    class ForLoopTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "<b>ForLoop</b> — boucles paramétriques multi-cibles "
                "(matériaux, modèles, avatars, DOF, see-tables, granulo)."
            ))
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.kind = QComboBox()
            for key, label in _TARGETS:
                self.kind.addItem(label, key)
            self.kind.currentIndexChanged.connect(self._on_kind_changed)

            self.var_edit = QLineEdit("i")
            self.start = QDoubleSpinBox(); self.stop = QDoubleSpinBox(); self.step = QDoubleSpinBox()
            self.start.setRange(-1e6, 1e6); self.stop.setRange(-1e6, 1e6)
            self.step.setRange(-1e6, 1e6)
            self.start.setValue(0); self.stop.setValue(10); self.step.setValue(1)
            self.step.setDecimals(6)

            self.template_combo = QComboBox()  # avatar / material / model / dof / see
            self.expr_x = QLineEdit("i * 0.1")
            self.expr_y = QLineEdit("0.0")
            self.expr_z = QLineEdit("0.0")
            self.expr_r = QLineEdit("")
            self.expr_r.setPlaceholderText("rayon (avatars) — vide = template")
            self.expr_density = QLineEdit("")
            self.expr_density.setPlaceholderText("ex. 1000 + 10*i")
            self.expr_alert = QLineEdit("")
            self.expr_alert.setPlaceholderText("ex. 0.01 * (i+1)")
            self.expr_nb = QLineEdit("")
            self.expr_nb.setPlaceholderText("nb particules granulo")
            self.expr_rmin = QLineEdit("")
            self.expr_rmax = QLineEdit("")
            self.group_edit = QLineEdit("")

            form.addRow("Cible de la boucle", self.kind)
            form.addRow("Variable", self.var_edit)
            form.addRow("start", self.start)
            form.addRow("stop (exclu)", self.stop)
            form.addRow("step", self.step)
            form.addRow("Template", self.template_combo)
            form.addRow("expr X (avatar)", self.expr_x)
            form.addRow("expr Y (avatar)", self.expr_y)
            form.addRow("expr Z (avatar)", self.expr_z)
            form.addRow("expr rayon", self.expr_r)
            form.addRow("expr densité (matériau)", self.expr_density)
            form.addRow("expr alert (see)", self.expr_alert)
            form.addRow("expr N (granulo)", self.expr_nb)
            form.addRow("expr rmin (granulo)", self.expr_rmin)
            form.addRow("expr rmax (granulo)", self.expr_rmax)
            form.addRow("Groupe", self.group_edit)
            layout.addLayout(form)

            row = QHBoxLayout()
            btn = QPushButton("Appliquer la boucle")
            btn.clicked.connect(self._on_apply)
            row.addWidget(btn)
            layout.addLayout(row)
            layout.addStretch()
            self._on_kind_changed()

        def _kind_key(self) -> str:
            return self.kind.currentData() or "avatar"

        def _on_kind_changed(self, *_a) -> None:
            k = self._kind_key()
            avatarish = k == "avatar"
            mat = k == "material"
            see = k == "visibility"
            gran = k in ("granulo", "granulo_dist")
            for w, vis in (
                (self.expr_x, avatarish),
                (self.expr_y, avatarish),
                (self.expr_z, avatarish),
                (self.expr_r, avatarish),
                (self.expr_density, mat),
                (self.expr_alert, see),
                (self.expr_nb, gran),
                (self.expr_rmin, gran),
                (self.expr_rmax, gran),
            ):
                w.setEnabled(vis)
            self._refill_templates()

        def _refill_templates(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            k = self._kind_key()
            self.template_combo.blockSignals(True)
            self.template_combo.clear()
            if k == "avatar":
                for a in p.avatars:
                    self.template_combo.addItem(
                        f"{a.avatar_id[:8]}… {a.avatar_type.value}", a.avatar_id,
                    )
            elif k == "material":
                for m in p.materials:
                    self.template_combo.addItem(m.name, m.name)
            elif k == "model":
                for m in p.models:
                    self.template_combo.addItem(f"{m.name} ({m.element})", m.name)
            elif k == "dof":
                for i, op in enumerate(p.operations):
                    self.template_combo.addItem(
                        f"[{i}] {op.operation_type} → {op.target_type}:{op.target_value}",
                        i,
                    )
            elif k == "visibility":
                for i, r in enumerate(p.visibility):
                    self.template_combo.addItem(
                        f"[{i}] {r.candidate_contactor}/{r.antagonist_contactor} "
                        f"{r.candidate_color}",
                        i,
                    )
            elif k in ("granulo", "granulo_dist"):
                if p.granulo:
                    for i, g in enumerate(p.granulo):
                        self.template_combo.addItem(
                            f"[{i}] {g.container_type} N={g.nb_particles}",
                            i,
                        )
                else:
                    self.template_combo.addItem("(paramètres du formulaire granulo / défauts)", -1)
            self.template_combo.blockSignals(False)

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.list.clear()
            for fl in getattr(p, "for_loops", []):
                kind = getattr(fl, "target_kind", "avatar")
                self.list.addItem(
                    f"[{kind}] {fl.var_name}=[{fl.start}:{fl.stop}:{fl.step}]  "
                    f"n≈{len(fl.generated_ids)}"
                )
            self._refill_templates()
            existing = list(p.avatar_groups.keys())
            suggested = suggest_group_name("forlp", existing)
            cur = self.group_edit.text().strip()
            if not cur or getattr(self, "_last_auto_group", "") == cur:
                self.group_edit.setText(suggested)
                self._last_auto_group = suggested

        def _on_apply(self) -> None:
            if self.controller is None:
                return
            k = self._kind_key()
            tid = self.template_combo.currentData()
            expressions = {}
            if self.expr_density.text().strip():
                expressions["density"] = self.expr_density.text().strip()
            if self.expr_alert.text().strip():
                expressions["alert"] = self.expr_alert.text().strip()
            if self.expr_nb.text().strip():
                expressions["nb_particles"] = self.expr_nb.text().strip()
            if self.expr_rmin.text().strip():
                expressions["radius_min"] = self.expr_rmin.text().strip()
            if self.expr_rmax.text().strip():
                expressions["radius_max"] = self.expr_rmax.text().strip()

            fl = ForLoop(
                var_name=self.var_edit.text().strip() or "i",
                start=self.start.value(),
                stop=self.stop.value(),
                step=self.step.value(),
                target_kind=k,
                model_avatar_id=str(tid) if k == "avatar" and tid else "",
                template_name=str(tid) if k in ("material", "model") and tid is not None else "",
                template_index=int(tid) if k in ("dof", "visibility", "granulo", "granulo_dist") and isinstance(tid, int) else -1,
                expr_x=self.expr_x.text().strip() or "0",
                expr_y=self.expr_y.text().strip() or "0",
                expr_z=self.expr_z.text().strip() or "0",
                expr_radius=(self.expr_r.text().strip() or None),
                expressions=expressions,
                group_name=self.group_edit.text().strip() or None,
            )
            if k == "avatar" and not fl.model_avatar_id:
                QMessageBox.warning(self, "ForLoop", "Sélectionnez un avatar template")
                return
            if k == "material" and not fl.template_name:
                QMessageBox.warning(self, "ForLoop", "Sélectionnez un matériau template")
                return
            if k == "model" and not fl.template_name:
                QMessageBox.warning(self, "ForLoop", "Sélectionnez un modèle template")
                return
            try:
                generated = self.controller.apply_for_loop(fl)
                n = len(generated) if generated is not None else 0
                QMessageBox.information(
                    self, "ForLoop",
                    f"Cible [{k}] — {n} élément(s) généré(s).",
                )
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "ForLoop", str(exc))
            except Exception as exc:
                QMessageBox.critical(self, "ForLoop", str(exc))

    return ForLoopTab(parent)
