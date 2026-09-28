"""GranuloTab — all deposit containers + avatar types by dimension (legacy parity)."""
from __future__ import annotations

from lmgc90_core import GranuloConfig, ValidationError
from lmgc90_core.types import AvatarType

from .base_tab import BaseTab
from ...utils.naming import suggest_group_name

# container_type → (label, dim, param_keys with defaults)
_CONTAINERS = [
    ("Box2D", "Box2D (rectangle)", 2, (("lx", 1.0), ("ly", 1.0))),
    ("Disk2D", "Disk2D (disque)", 2, (("r", 1.0),)),
    ("Drum2D", "Drum2D (tambour)", 2, (("r", 1.0),)),
    ("Couette2D", "Couette2D (anneau)", 2, (("rint", 0.5), ("rext", 1.0))),
    ("Box3D", "Box3D (boîte)", 3, (("lx", 1.0), ("ly", 1.0), ("lz", 1.0))),
    ("Sphere3D", "Sphere3D (sphère)", 3, (("r", 1.0),)),
    ("Cylinder3D", "Cylinder3D (cylindre)", 3, (("r", 1.0), ("lz", 2.0))),
]

_AVATARS_2D = [
    ("rigidDisk", AvatarType.RIGID_DISK),
    ("rigidDiscreteDisk", AvatarType.RIGID_DISCRETE),
    ("rigidPolygon", AvatarType.RIGID_POLYGON),
]
_AVATARS_3D = [
    ("rigidSphere", AvatarType.RIGID_SPHERE),
    ("rigidPolyhedron", AvatarType.RIGID_POLYHEDRON),
]


def _lmgc5(name: str, default: str = "XXXXX") -> str:
    s = (name or "").strip() or default
    if len(s) > 5:
        s = s[:5]
    if len(s) < 5:
        s = s + ("x" * (5 - len(s)))
    return s


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
            layout.addWidget(QLabel(
                "<b>Granulométrie</b> — dépôts 2D/3D (Box, Disk, Drum, Couette, "
                "Sphere, Cylinder) · numpy SoA ou pylmgc <code>depositIn*</code>"
            ))
            self.list = QListWidget()
            layout.addWidget(self.list)

            form = QFormLayout()
            self.n_spin = QSpinBox()
            self.n_spin.setRange(1, 500_000)
            self.n_spin.setValue(200)
            self.rmin = QDoubleSpinBox()
            self.rmax = QDoubleSpinBox()
            for s, v in ((self.rmin, 0.05), (self.rmax, 0.15)):
                s.setRange(1e-6, 1e3)
                s.setDecimals(6)
                s.setValue(v)

            self.container = QComboBox()
            self.container.currentIndexChanged.connect(self._on_container_changed)

            # dynamic param widgets
            self._param_widgets: dict[str, QDoubleSpinBox] = {}
            self.param_host = QWidget()
            self.param_form = QFormLayout(self.param_host)

            self.type_combo = QComboBox()
            self.mat_combo = QComboBox()
            self.mod_combo = QComboBox()
            self.color_edit = QLineEdit("BLUEx")
            self.color_edit.setMaxLength(5)
            self.group_edit = QLineEdit("granx")
            self.group_edit.setMaxLength(5)
            self.seed_spin = QSpinBox()
            self.seed_spin.setRange(-1, 2**31 - 1)
            self.seed_spin.setValue(42)
            self.seed_spin.setSpecialValueText("random")
            self.pylmgc_check = QCheckBox(
                "Utiliser dépôt pylmgc (engine) si disponible — sinon numpy SoA"
            )
            self.pylmgc_check.setChecked(False)

            form.addRow("N particules", self.n_spin)
            form.addRow("Rayon min", self.rmin)
            form.addRow("Rayon max", self.rmax)
            form.addRow("Conteneur", self.container)
            form.addRow(self.param_host)
            form.addRow("Type d'avatar", self.type_combo)
            form.addRow("Matériau", self.mat_combo)
            form.addRow("Modèle", self.mod_combo)
            form.addRow("Couleur (5 car.)", self.color_edit)
            form.addRow("Groupe (5 car.)", self.group_edit)
            form.addRow("Seed", self.seed_spin)
            form.addRow("", self.pylmgc_check)
            layout.addLayout(form)

            row = QHBoxLayout()
            btn_add = QPushButton("Générer le dépôt")
            btn_add.clicked.connect(self._on_deposit)
            btn_rm = QPushButton("Supprimer sélection")
            btn_rm.clicked.connect(self._on_remove)
            row.addWidget(btn_add)
            row.addWidget(btn_rm)
            layout.addLayout(row)
            layout.addStretch()

        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            dim = int(self.controller.project.dimension)
            # containers for this dimension (+ allow 2D containers always documented)
            cur = self.container.currentData()
            self.container.blockSignals(True)
            self.container.clear()
            for key, label, cdim, _params in _CONTAINERS:
                if cdim == dim or (dim == 3 and cdim == 2):
                    # doc: 2D containers available regardless; still filter by dim preference
                    if cdim == dim:
                        self.container.addItem(label, key)
            # if dim 3 only 3D; if dim 2 only 2D
            if self.container.count() == 0:
                for key, label, cdim, _ in _CONTAINERS:
                    if cdim == dim:
                        self.container.addItem(label, key)
            # restore selection
            if cur:
                idx = self.container.findData(cur)
                if idx >= 0:
                    self.container.setCurrentIndex(idx)
            self.container.blockSignals(False)
            self._on_container_changed()

            # avatar types by dimension
            self.type_combo.blockSignals(True)
            self.type_combo.clear()
            for label, at in (_AVATARS_2D if dim == 2 else _AVATARS_3D):
                self.type_combo.addItem(label, at)
            self.type_combo.blockSignals(False)

            self.mat_combo.clear()
            self.mod_combo.clear()
            for m in self.controller.project.materials:
                self.mat_combo.addItem(m.name)
            for m in self.controller.project.models:
                if int(getattr(m, "dimension", dim)) == dim:
                    self.mod_combo.addItem(m.name)

            self.list.clear()
            for pop in self.controller.project.populations:
                self.list.addItem(
                    f"{pop.population_id[:8]}…  N={len(pop)}  "
                    f"{getattr(pop, 'avatar_type', '?')}  "
                    f"{getattr(pop, 'group_name', '') or ''}"
                )
            for g in getattr(self.controller.project, "granulo_configs", []) or []:
                pass

        def _on_container_changed(self, *_a) -> None:
            key = self.container.currentData()
            # clear form
            while self.param_form.rowCount():
                self.param_form.removeRow(0)
            self._param_widgets.clear()
            if not key:
                return
            meta = next((c for c in _CONTAINERS if c[0] == key), None)
            if not meta:
                return
            _k, _lab, _cdim, params = meta
            for pname, default in params:
                sp = QDoubleSpinBox()
                sp.setRange(1e-6, 1e6)
                sp.setDecimals(6)
                sp.setValue(float(default))
                self._param_widgets[pname] = sp
                self.param_form.addRow(pname, sp)

        def _on_deposit(self) -> None:
            if self.controller is None:
                return
            mat = self.mat_combo.currentText()
            mod = self.mod_combo.currentText()
            if not mat or not mod:
                QMessageBox.warning(self, "Granulo", "Matériau et modèle requis")
                return
            if self.rmin.value() >= self.rmax.value():
                QMessageBox.warning(self, "Granulo", "rmin doit être < rmax")
                return
            ctype = self.container.currentData()
            if not ctype:
                QMessageBox.warning(self, "Granulo", "Conteneur requis")
                return
            atype = self.type_combo.currentData()
            seed = None if self.seed_spin.value() < 0 else self.seed_spin.value()
            params = {k: w.value() for k, w in self._param_widgets.items()}
            dim = int(self.controller.project.dimension)
            # container dim consistency
            meta = next((c for c in _CONTAINERS if c[0] == ctype), None)
            if meta and meta[2] != dim:
                QMessageBox.warning(
                    self, "Granulo",
                    f"Conteneur {ctype} est {meta[2]}D, projet en {dim}D.",
                )
                return
            color = _lmgc5(self.color_edit.text(), "BLUEx")
            group = _lmgc5(self.group_edit.text(), "granx")
            cfg = GranuloConfig(
                nb_particles=self.n_spin.value(),
                radius_min=self.rmin.value(),
                radius_max=self.rmax.value(),
                container_type=ctype,
                container_params=params,
                material_name=mat,
                model_name=mod,
                avatar_type=atype.value if hasattr(atype, "value") else str(atype),
                color=color,
                group_name=group,
                seed=seed,
                dimension=dim,
            )
            try:
                if self.pylmgc_check.isChecked():
                    pop = self.controller.run_granulo_pylmgc(cfg, avatar_type=atype)
                else:
                    pop = self.controller.deposit(cfg)
                QMessageBox.information(
                    self, "Granulo",
                    f"Population {pop.population_id[:12]}… — {len(pop)} particules "
                    f"({ctype})",
                )
            except (ValidationError, ValueError, RuntimeError) as exc:
                QMessageBox.warning(self, "Granulo", str(exc))
            except Exception as exc:
                QMessageBox.critical(self, "Granulo", str(exc))

        def _on_remove(self) -> None:
            if self.controller is None:
                return
            row = self.list.currentRow()
            pops = self.controller.project.populations
            if row < 0 or row >= len(pops):
                return
            self.controller.remove_population(pops[row].population_id)

    return GranuloTab(parent)
