"""GranuloTab — all deposit containers + avatar types by dimension (legacy parity)."""
from __future__ import annotations

from pathlib import Path

from lmgc90_core import GranuloConfig, ValidationError, lmgc5
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

_DISTRIBUTIONS = [
    ("granulo_Random", "Uniforme en nombre"),
    ("granulo_Uniform", "Uniforme en surface"),
    ("granulo_TwoSizesNumber", "Deux tailles (proportion en nombre)"),
    ("granulo_TwoSizesVolume", "Deux tailles (proportion en volume)"),
    ("granulo_BetaDistribution", "Distribution Beta"), #
    ("granulo_ReadFromFile", "Lire depuis un fichier"),
]


def create_granulo_tab(parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout,
        QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
        QPushButton, QWidget, QVBoxLayout,
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
            self.n_spin = QLineEdit("200")
            self.rmin = QLineEdit("0.05")
            self.rmax = QLineEdit("0.15")
            self.n_label = QLabel("N particules")
            self.distribution = QComboBox()
            for key, label in _DISTRIBUTIONS:
                self.distribution.addItem(label, key)
            self.distribution.currentIndexChanged.connect(self._on_distribution_changed)
            self.distribution_host = QWidget()
            self.distribution_form = QFormLayout(self.distribution_host)
            self.distribution_widgets: dict[str, QLineEdit] = {}
            self.distribution_file = QLineEdit()
            self.distribution_file.setPlaceholderText("Fichier texte de rayons")
            self.distribution_file_row = QWidget()
            file_layout = QHBoxLayout(self.distribution_file_row)
            file_layout.setContentsMargins(0, 0, 0, 0)
            file_layout.addWidget(self.distribution_file, 1)
            browse_file = QPushButton("Parcourir…")
            browse_file.clicked.connect(self._browse_distribution_file)
            file_layout.addWidget(browse_file)

            self.container = QComboBox()
            self.container.currentIndexChanged.connect(self._on_container_changed)

            # dynamic param widgets
            self._param_widgets: dict[str, QLineEdit] = {}
            self.param_host = QWidget()
            self.param_form = QFormLayout(self.param_host)

            self.type_combo = QComboBox()
            self.mat_combo = QComboBox()
            self.mod_combo = QComboBox()
            self.color_edit = QLineEdit("BLUEx")
            self.color_edit.setMaxLength(5)
            self.group_edit = QLineEdit("granx")
            self.group_edit.setMaxLength(5)
            self.seed_spin = QLineEdit("42")
            self.seed_spin.setPlaceholderText("entier, expression ou random")
            self.pylmgc_check = QCheckBox(
                "Utiliser dépôt pylmgc (engine) si disponible — sinon numpy SoA"
            )
            self.pylmgc_check.setChecked(False)
            self.distrib_only = QCheckBox(
                "Distribution seule (rayons) — sans avatars / sans population"
            )
            self.distrib_only.setChecked(False)
            self.distrib_only.setToolTip(
                "Comme l'ancien granulo_tab : tire N rayons [rmin, rmax] "
                "et enregistre la config, sans créer de ParticlePopulation ni d'avatars."
            )
            self.distrib_only.toggled.connect(
                lambda on: self.pylmgc_check.setEnabled(not on)
            )

            form.addRow(self.n_label, self.n_spin)
            form.addRow("Rayon min", self.rmin)
            form.addRow("Rayon max", self.rmax)
            form.addRow("Distribution", self.distribution)
            form.addRow(self.distribution_host)
            form.addRow("Fichier de rayons", self.distribution_file_row)
            form.addRow("Conteneur", self.container)
            form.addRow(self.param_host)
            form.addRow("Type d'avatar", self.type_combo)
            form.addRow("Matériau", self.mat_combo)
            form.addRow("Modèle", self.mod_combo)
            form.addRow("Couleur (5 car.)", self.color_edit)
            form.addRow("Groupe (5 car.)", self.group_edit)
            form.addRow("Seed", self.seed_spin)
            for field in (self.n_spin, self.rmin, self.rmax):
                field.setPlaceholderText("nombre ou expression")
                self.mark_expr_field(field)
            self.mark_expr_field(self.seed_spin)
            form.addRow("", self.pylmgc_check)
            form.addRow("", self.distrib_only)
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
            self._on_distribution_changed()

        def _browse_distribution_file(self) -> None:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Choisir un fichier de rayons",
                self.distribution_file.text().strip(),
                "Fichiers texte (*.txt *.dat);;Tous les fichiers (*)",
            )
            if filename:
                self.distribution_file.setText(filename)

        def _on_distribution_changed(self, *_a) -> None:
            while self.distribution_form.rowCount():
                self.distribution_form.removeRow(0)
            self.distribution_widgets.clear()
            dist = self.distribution.currentData()
            self.distribution_file_row.setVisible(dist == "granulo_ReadFromFile")
            self.rmin.setEnabled(dist != "granulo_ReadFromFile")
            self.rmax.setEnabled(dist != "granulo_ReadFromFile")
            if dist in ("granulo_TwoSizesNumber", "granulo_TwoSizesVolume"):
                p_min = QLineEdit("0.5")
                p_min.setPlaceholderText("entre 0 et 1")
                p_min.setToolTip(
                    "Fraction de la petite taille: en nombre ou en volume selon le choix."
                )
                self.distribution_widgets["p_min"] = p_min
                self.distribution_form.addRow("Proportion petite taille", p_min)
            if dist == "granulo_BetaDistribution":
                nb_t = QLineEdit("10")
                a = QLineEdit("2.0")
                b = QLineEdit("5.0")
                vol = QLineEdit("1.0")
                for w in (nb_t, a, b, vol):
                    w.setPlaceholderText("nombre ou expression > 0")
                self.distribution_widgets["nb_t"] = nb_t
                self.distribution_widgets["a"] = a
                self.distribution_widgets["b"] = b
                self.distribution_widgets["vol"] = vol
                self.distribution_form.addRow("Nombre de classes", nb_t)
                self.distribution_form.addRow("Paramètre a", a)
                self.distribution_form.addRow("Paramètre b", b)
                self.distribution_form.addRow("Volume total (m³)", vol)
            is_beta = dist == "granulo_BetaDistribution"
            self.n_spin.setEnabled(not is_beta)
            self.n_label.setText(
                "N particules" if not is_beta else "N (déduit du volume)"
            )
  
        def on_state_changed(self) -> None:
            if self.controller is None:
                return
            dim = int(self.controller.project.dimension)
            selected_type = self.type_combo.currentData()
            selected_material = self.mat_combo.currentText()
            selected_model = self.mod_combo.currentText()
            parameter_values = {
                name: widget.text() for name, widget in self._param_widgets.items()
            }
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
            for name, value in parameter_values.items():
                widget = self._param_widgets.get(name)
                if widget is not None:
                    widget.setText(value)

            # avatar types by dimension
            self.type_combo.blockSignals(True)
            self.type_combo.clear()
            for label, at in (_AVATARS_2D if dim == 2 else _AVATARS_3D):
                self.type_combo.addItem(label, at)
            self.type_combo.blockSignals(False)
            type_index = self.type_combo.findData(selected_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)

            self.mat_combo.clear()
            self.mod_combo.clear()
            for m in self.controller.project.materials:
                self.mat_combo.addItem(m.name)
            for m in self.controller.project.models:
                if int(getattr(m, "dimension", dim)) == dim:
                    self.mod_combo.addItem(m.name)
            material_index = self.mat_combo.findText(selected_material)
            if material_index >= 0:
                self.mat_combo.setCurrentIndex(material_index)
            model_index = self.mod_combo.findText(selected_model)
            if model_index >= 0:
                self.mod_combo.setCurrentIndex(model_index)

            self.list.clear()
            for pop in self.controller.project.populations:
                item = QListWidgetItem(
                    f"[SoA] {pop.population_id[:8]}…  N={len(pop)}  "
                    f"{getattr(pop, 'avatar_type', '?')}  "
                    f"{getattr(pop, 'group_name', '') or ''}"
                )
                item.setData(Qt.ItemDataRole.UserRole, (
                    "population", pop.population_id,
                ))
                self.list.addItem(item)
            for g in getattr(self.controller.project, "granulo", []) or []:
                if not getattr(g, "create_avatars", True):
                    nr = len(g.radii or [])
                    item = QListWidgetItem(
                        f"[dist] N={g.nb_particles} r∈[{g.radius_min:.4g},{g.radius_max:.4g}] "
                        f"→ {nr} rayons  ({g.container_type})"
                    )
                    item.setData(Qt.ItemDataRole.UserRole, (
                        "distribution", g.generation_id,
                    ))
                    self.list.addItem(item)

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
                sp = QLineEdit(str(default))
                sp.setPlaceholderText("nombre ou expression")
                self.mark_expr_field(sp)
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
            distribution = self.distribution.currentData() or "granulo_Random"
            try:
                radius_min = self.eval_float(self.rmin.text(), 0.05, "radius_min")
                radius_max = self.eval_float(self.rmax.text(), 0.15, "radius_max")
                distribution_params = {}
                for key, widget in self.distribution_widgets.items():
                    if key == "nb_t":
                        distribution_params[key] = self.eval_int(widget.text(), 10, key)
                    else:
                        distribution_params[key] = self.eval_float(
                            widget.text(), 0.5, key
                        )
                seed_text = self.seed_spin.text().strip()
                seed_value = (
                    -1 if seed_text.lower() == "random"
                    else self.eval_int(seed_text, 42, "seed")
                )
                params = {
                    k: self.eval_float(w.text(), 0.0, k)
                    for k, w in self._param_widgets.items()
                }
                nb_particles = self.eval_int(self.n_spin.text(), 200, "nb_particles")
            except (ValidationError, ValueError) as exc:
                QMessageBox.warning(self, "Granulo", str(exc))
                return
            if distribution != "granulo_ReadFromFile" and radius_min >= radius_max:
                QMessageBox.warning(self, "Granulo", "rmin doit être < rmax")
                return
            if "p_min" in distribution_params and not 0.0 <= distribution_params["p_min"] <= 1.0:
                QMessageBox.warning(self, "Granulo", "La proportion doit être entre 0 et 1")
                return
            distribution_file = None
            if distribution == "granulo_ReadFromFile":
                distribution_file = self.distribution_file.text().strip()
                if not distribution_file or not Path(distribution_file).is_file():
                    QMessageBox.warning(
                        self, "Granulo", "Sélectionnez un fichier de rayons existant."
                    )
                    return
            ctype = self.container.currentData()
            if not ctype:
                QMessageBox.warning(self, "Granulo", "Conteneur requis")
                return
            atype = self.type_combo.currentData()
            seed = None if seed_value < 0 else seed_value
            dim = int(self.controller.project.dimension)
            # container dim consistency
            meta = next((c for c in _CONTAINERS if c[0] == ctype), None)
            if meta and meta[2] != dim:
                QMessageBox.warning(
                    self, "Granulo",
                    f"Conteneur {ctype} est {meta[2]}D, projet en {dim}D.",
                )
                return
            # granulo_BetaDistribution requires a, b, vol > 0
            if distribution == "granulo_BetaDistribution":
                a = distribution_params.get("a", 0.0)
                b = distribution_params.get("b", 0.0)
                vol = distribution_params.get("vol", 0.0)
                if a <= 0 or b <= 0 or vol <= 0:
                    QMessageBox.warning(
                        self, "Granulo",
                        "Distribution Beta: a, b et volume total doivent être > 0.",
                    )
                    return
            color = lmgc5(self.color_edit.text(), "BLUEx")
            group = lmgc5(self.group_edit.text(), "granx")
            cfg = GranuloConfig(
                nb_particles=nb_particles,
                radius_min=radius_min,
                radius_max=radius_max,
                container_type=ctype,
                container_params=params,
                material_name=mat,
                model_name=mod,
                avatar_type=atype.value if hasattr(atype, "value") else str(atype),
                color=color,
                group_name=group,
                seed=seed,
                dimension=dim,
                create_avatars=not self.distrib_only.isChecked(),
                distribution_type=distribution,
                distribution_params=distribution_params,
                distribution_file=distribution_file,
            )
            try:
                if self.distrib_only.isChecked():
                    self.controller.deposit(cfg)
                    n = len(cfg.radii or [])
                    QMessageBox.information(
                        self, "Granulo",
                        f"Distribution seule : {n} rayons "
                        f"[{cfg.radius_min:.4g}, {cfg.radius_max:.4g}] "
                        f"(aucun avatar créé).",
                    )
                elif self.pylmgc_check.isChecked():
                    pop = self.controller.run_granulo_pylmgc(cfg, avatar_type=atype)
                    QMessageBox.information(
                        self, "Granulo",
                        f"Population {pop.population_id[:12]}… — {len(pop)} particules "
                        f"({ctype})",
                    )
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
            item = self.list.currentItem()
            if item is None:
                return
            item_type, item_id = item.data(Qt.ItemDataRole.UserRole) or (None, None)
            if item_type == "population":
                self.controller.remove_population(item_id)
            elif item_type == "distribution":
                self.controller.remove_granulo_config(item_id)

    return GranuloTab(parent)
