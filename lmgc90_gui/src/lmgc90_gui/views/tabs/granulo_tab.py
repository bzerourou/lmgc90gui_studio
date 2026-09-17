"""GranuloTab — granulometric deposit (numpy SoA by default, optional pylmgc path)."""
from __future__ import annotations

from lmgc90_core import GranuloConfig, ValidationError
from lmgc90_core.types import AvatarType

from .base_tab import BaseTab
from ...utils.naming import suggest_group_name


def create_granulo_tab(parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
        QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox,
        QVBoxLayout, QWidget,
    )

    class GranuloTab(QWidget, BaseTab):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.n_spin = QSpinBox()
            self.n_spin.setRange(1, 500_000)
            self.n_spin.setValue(100)
            self.rmin = QDoubleSpinBox(); self.rmax = QDoubleSpinBox()
            for s, v in ((self.rmin, 0.01), (self.rmax, 0.03)):
                s.setRange(1e-6, 1e3)
                s.setDecimals(6)
                s.setValue(v)
            self.lx = QDoubleSpinBox(); self.ly = QDoubleSpinBox(); self.lz = QDoubleSpinBox()
            for s, v in ((self.lx, 1.0), (self.ly, 1.0), (self.lz, 1.0)):
                s.setRange(1e-6, 1e6)
                s.setDecimals(4)
                s.setValue(v)
            self.mat_combo = QComboBox()
            self.mod_combo = QComboBox()
            self.type_combo = QComboBox()
            self.type_combo.addItem("rigidDisk", AvatarType.RIGID_DISK)
            self.type_combo.addItem("rigidSphere", AvatarType.RIGID_SPHERE)
            self.color_edit = QLineEdit("BLUEx")
            self.group_edit = QLineEdit("gran")
            self.seed_spin = QSpinBox()
            self.seed_spin.setRange(-1, 2**31 - 1)
            self.seed_spin.setValue(42)
            self.seed_spin.setSpecialValueText("random")
            self.soa_check = QCheckBox("Store as ParticlePopulation (SoA) — recommended")
            self.soa_check.setChecked(True)
            self.soa_check.setEnabled(False)  # core deposit always produces SoA population
            self.pylmgc_check = QCheckBox("Use pylmgc deposit (engine) if available")
            self.pylmgc_check.setChecked(False)

            form.addRow("N particles", self.n_spin)
            form.addRow("Radius min", self.rmin)
            form.addRow("Radius max", self.rmax)
            form.addRow("Box lx", self.lx)
            form.addRow("Box ly", self.ly)
            form.addRow("Box lz (3D)", self.lz)
            form.addRow("Material", self.mat_combo)
            form.addRow("Model", self.mod_combo)
            form.addRow("Avatar type", self.type_combo)
            form.addRow("Color", self.color_edit)
            form.addRow("Group", self.group_edit)
            form.addRow("Seed", self.seed_spin)
            layout.addLayout(form)
            layout.addWidget(self.soa_check)
            layout.addWidget(self.pylmgc_check)
            layout.addWidget(QLabel(
                "SoA: one ParticlePopulation (numpy arrays). "
                "Always used by core.deposit / engine.run_granulo."
            ))

            row = QHBoxLayout()
            btn_run = QPushButton("Generate deposit")
            btn_rm = QPushButton("Remove selected population")
            btn_run.clicked.connect(self._on_generate)
            btn_rm.clicked.connect(self._on_remove)
            row.addWidget(btn_run)
            row.addWidget(btn_rm)
            layout.addLayout(row)

        def _suggest_group(self) -> None:
            if self.controller is None:
                return
            existing = list(self.controller.project.avatar_groups.keys()) + list(
                getattr(self.controller.project, "population_groups", {}).keys()
            )
            suggested = suggest_group_name("granulo", existing)
            cur = self.group_edit.text().strip()
            if not cur or cur in ("granulo", "gran") or getattr(self, "_last_auto_group", "") == cur:
                self.group_edit.setText(suggested)
                self._last_auto_group = suggested

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            p = self.controller.project
            self.list.clear()
            for pop in p.populations:
                self.list.addItem(
                    f"{pop.population_id[:12]}…  n={len(pop)}  "
                    f"{pop.avatar_type.value}  [{pop.material_name}/{pop.model_name}]  "
                    f"group={pop.group_name or '—'}"
                )
            for g in p.granulo:
                self.list.addItem(
                    f"  cfg: n={g.nb_particles} r=[{g.radius_min},{g.radius_max}] "
                    f"→ pop={g.population_id}"
                )
            cur_m, cur_o = self.mat_combo.currentText(), self.mod_combo.currentText()
            self.mat_combo.clear()
            self.mat_combo.addItems([m.name for m in p.materials])
            self.mod_combo.clear()
            self.mod_combo.addItems([m.name for m in p.models])
            if cur_m:
                i = self.mat_combo.findText(cur_m)
                if i >= 0:
                    self.mat_combo.setCurrentIndex(i)
            if cur_o:
                i = self.mod_combo.findText(cur_o)
                if i >= 0:
                    self.mod_combo.setCurrentIndex(i)
            self._suggest_group()

        def _on_generate(self) -> None:
            if self.controller is None:
                return
            mat = self.mat_combo.currentText()
            mod = self.mod_combo.currentText()
            if not mat or not mod:
                QMessageBox.warning(self, "Granulo", "Material and model required")
                return
            atype = self.type_combo.currentData()
            seed = None if self.seed_spin.value() < 0 else self.seed_spin.value()
            params = {"lx": self.lx.value(), "ly": self.ly.value()}
            if self.controller.project.dimension == 3:
                params["lz"] = self.lz.value()
            cfg = GranuloConfig(
                nb_particles=self.n_spin.value(),
                radius_min=self.rmin.value(),
                radius_max=self.rmax.value(),
                container_type="Box2D" if self.controller.project.dimension == 2 else "Box3D",
                container_params=params,
                material_name=mat,
                model_name=mod,
                avatar_type=atype.value if hasattr(atype, "value") else str(atype),
                color=self.color_edit.text().strip() or "BLUEx",
                group_name=self.group_edit.text().strip() or None,
                seed=seed,
                dimension=self.controller.project.dimension,
            )
            try:
                if self.pylmgc_check.isChecked():
                    pop = self.controller.run_granulo_pylmgc(cfg, avatar_type=atype)
                else:
                    pop = self.controller.deposit(cfg)
                QMessageBox.information(
                    self, "Granulo",
                    f"Population {pop.population_id[:12]}… created with {len(pop)} particles",
                )
            except (ValidationError, ValueError, RuntimeError) as exc:
                QMessageBox.warning(self, "Granulo", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            row = self.list.currentRow()
            pops = self.controller.project.populations
            if row < 0 or row >= len(pops):
                # might have selected a cfg line — ignore
                return
            self.controller.remove_population(pops[row].population_id)

    return GranuloTab(parent)
