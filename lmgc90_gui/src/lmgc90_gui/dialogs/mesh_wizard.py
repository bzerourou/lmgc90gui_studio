"""MeshWizard — assistant multi-pages corps déformables (EF).

Port of the legacy `mesh_wiz_def.MeshWizard` onto lmgc90_core + ProjectController:
* no direct pylmgc containers (`_bodies_container`, `_pylmgc_materials`, …)
* Avatar(MESH_DEFORMABLE) + mesh_params for persistence / pre.py emission
* structured rectangle uses ``pre.meshed_rectangle``; other shapes store intent in mesh_params
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from lmgc90_core import Avatar, Material, MaterialType, Model, ValidationError, pre
from lmgc90_core.types import AvatarOrigin, AvatarType, MATERIAL_PROPERTY_SCHEMA

# ---------------------------------------------------------------------------
_ELEMENTS_2D = ["T3xxx", "Q4xxx", "T6xxx", "Q8xxx", "Q9xxx"]
_ELEMENTS_3D = ["H8xxx", "H20xx", "TE4xx", "TE10x", "PRI6x"]
_ELEMENT_INFO = {
    "T3xxx": "Triangle linéaire à 3 nœuds",
    "Q4xxx": "Quadrangle bilinéaire à 4 nœuds",
    "T6xxx": "Triangle quadratique à 6 nœuds",
    "Q8xxx": "Quadrangle serendipity à 8 nœuds",
    "Q9xxx": "Quadrangle biquadratique complet à 9 nœuds",
    "H8xxx": "Hexaèdre trilinéaire à 8 nœuds",
    "H20xx": "Hexaèdre triquadratique à 20 nœuds",
    "TE4xx": "Tétraèdre linéaire à 4 nœuds",
    "TE10x": "Tétraèdre quadratique à 10 nœuds",
    "PRI6x": "Prisme à 6 nœuds",
}
_MESH_TYPES_2D = ["2T3", "Q4", "4T3", "Q8"]
_MESH_TYPES_3D = ["H8"]
_ANISOTROPY = ["iso__", "ortho"]
_KINEMATIC = ["small", "large"]
_FORMULATION = ["UpdtL", "TotaL"]
_MASS_STORAGE = ["lump_", "coher"]

_MAT_DEFAULTS = {
    "ELAS": {"elas": "standard", "young": 70e9, "nu": 0.3, "anisotropy": "isotropic"},
    "ELAS_DILA": {
        "elas": "standard", "young": 70e9, "nu": 0.3, "anisotropy": "isotropic",
        "alpha": 1e-5,
    },
    "VISCO_ELAS": {
        "elas": "standard", "young": 1.17e11, "nu": 0.35, "anisotropy": "isotropic",
        "eta": 1e6,
    },
    "ELAS_PLAS": {
        "elas": "standard", "young": 1.17e11, "nu": 0.35, "anisotropy": "isotropic",
        "sigc": 3e8, "hard": 0.0,
    },
    "THERMO_ELAS": {
        "elas": "standard", "young": 70e9, "nu": 0.3, "anisotropy": "isotropic",
        "alpha": 1e-5, "conductivity": 50.0, "capacity": 500.0,
    },
    "PORO_ELAS": {
        "elas": "standard", "young": 70e9, "nu": 0.3, "anisotropy": "isotropic",
        "permeability": 1e-12, "biot": 1.0,
    },
}
_ELASTIC_TYPES = list(_MAT_DEFAULTS.keys())
_GEOM_2D = ["Rectangle", "Disque", "Fichier externe"]
_GEOM_3D = ["Boîte (H8)", "Sphère", "Cylindre", "Fichier externe"]


def create_mesh_wizard(controller, parent=None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
        QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QRadioButton,
        QSpinBox, QTextEdit, QVBoxLayout, QWidget, QWizard, QWizardPage,
    )

    # ===================================================================== pages
    class MeshIntroPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Assistant corps déformable (EF)")
            self.setSubTitle("Création guidée d'un avatar maillé MAILx")
            lay = QVBoxLayout(self)
            lay.addWidget(QLabel(
                "<p>Cet assistant reprend le flux de <b>mesh_wiz_def</b> :</p>"
                "<ol>"
                "<li>Dimension (2D / 3D)</li>"
                "<li>Matériau élastique (ELAS…)</li>"
                "<li>Modèle éléments finis</li>"
                "<li>Géométrie</li>"
                "<li>Raffinement du maillage</li>"
                "<li>Contacteurs de bord</li>"
                "<li>Résumé et génération</li>"
                "</ol>"
                "<p>Les données sont enregistrées dans <code>lmgc90_core.Project</code> "
                "(Avatar MESH_DEFORMABLE + mesh_params). "
                "La matérialisation pylmgc se fait plus tard via lmgc90_engine.</p>"
            ))
            lay.addStretch()

    class MeshDimensionPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Dimension")
            self.setSubTitle("2D ou 3D — doit rester cohérente avec le projet")
            lay = QVBoxLayout(self)
            self.dim_2d = QRadioButton("2D (plan)")
            self.dim_3d = QRadioButton("3D")
            self.dim_2d.setChecked(True)
            lay.addWidget(self.dim_2d)
            lay.addWidget(self.dim_3d)
            self.hint = QLabel("")
            lay.addWidget(self.hint)
            lay.addStretch()

        def initializePage(self):
            wiz = self.wizard()
            dim = wiz.controller.project.dimension
            if dim == 3:
                self.dim_3d.setChecked(True)
            else:
                self.dim_2d.setChecked(True)
            self.hint.setText(f"Dimension actuelle du projet : {dim}D")

        def dimension(self) -> int:
            return 2 if self.dim_2d.isChecked() else 3

    class MeshMaterialPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Matériau")
            self.setSubTitle("Créer un matériau élastique ou en réutiliser un")
            lay = QVBoxLayout(self)
            self.create_mat = QCheckBox("Créer un nouveau matériau")
            self.create_mat.setChecked(True)
            lay.addWidget(self.create_mat)
            self.existing = QComboBox()
            lay.addWidget(QLabel("Ou choisir un matériau existant :"))
            lay.addWidget(self.existing)

            form = QFormLayout()
            self.mat_name = QLineEdit("ELAS1")
            self.mat_name.setMaxLength(5)
            self.mat_type = QComboBox()
            self.mat_type.addItems(_ELASTIC_TYPES)
            self.density = QDoubleSpinBox()
            self.density.setRange(1, 1e6)
            self.density.setValue(2500.0)
            form.addRow("Nom", self.mat_name)
            form.addRow("Type", self.mat_type)
            form.addRow("Densité", self.density)
            self.prop_box = QGroupBox("Propriétés")
            self.prop_form = QFormLayout(self.prop_box)
            self._prop_widgets: Dict[str, Any] = {}
            lay.addLayout(form)
            lay.addWidget(self.prop_box)
            self.mat_type.currentTextChanged.connect(self._rebuild_props)
            self.create_mat.toggled.connect(self._toggle)
            self._rebuild_props()
            self._toggle(True)

        def initializePage(self):
            mats = [
                m.name for m in self.wizard().controller.project.materials
                if m.material_type.value in _ELASTIC_TYPES or m.material_type.value == "ELAS"
            ]
            self.existing.clear()
            if mats:
                self.existing.addItems(mats)
            else:
                self.existing.addItem("(Aucun matériau élastique)")

        def _toggle(self, on: bool):
            self.mat_name.setEnabled(on)
            self.mat_type.setEnabled(on)
            self.density.setEnabled(on)
            self.prop_box.setEnabled(on)
            self.existing.setEnabled(not on)

        def _rebuild_props(self, *_a):
            while self.prop_form.count():
                item = self.prop_form.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._prop_widgets.clear()
            key = self.mat_type.currentText()
            defaults = dict(_MAT_DEFAULTS.get(key, {}))
            schema = MATERIAL_PROPERTY_SCHEMA.get(key, ())
            # prefer schema order
            names = [n for n, _, _ in schema] if schema else list(defaults.keys())
            for name in names:
                default = defaults.get(name, 0.0)
                if isinstance(default, (int, float)):
                    w = QDoubleSpinBox()
                    w.setRange(-1e30, 1e30)
                    w.setDecimals(6)
                    w.setValue(float(default))
                else:
                    w = QLineEdit(str(default))
                self.prop_form.addRow(name, w)
                self._prop_widgets[name] = w

        def collect_props(self) -> dict:
            out = {}
            for k, w in self._prop_widgets.items():
                if isinstance(w, QDoubleSpinBox):
                    out[k] = float(w.value())
                else:
                    out[k] = w.text().strip()
            return out

        def material_name(self) -> str:
            if self.create_mat.isChecked():
                return self.mat_name.text().strip()
            return self.existing.currentText().strip()

    class MeshModelPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Modèle EF")
            self.setSubTitle("Élément, physique et options numériques")
            lay = QVBoxLayout(self)
            self.create_mod = QCheckBox("Créer un nouveau modèle")
            self.create_mod.setChecked(True)
            lay.addWidget(self.create_mod)
            self.existing = QComboBox()
            lay.addWidget(QLabel("Ou choisir un modèle existant :"))
            lay.addWidget(self.existing)
            form = QFormLayout()
            self.mod_name = QLineEdit("femxx")
            self.mod_name.setMaxLength(5)
            self.physics = QComboBox()
            self.physics.addItems(["MECAx", "MULTI", "THERx", "POROx"])
            self.element = QComboBox()
            self.element_info = QLabel("")
            self.anisotropy = QComboBox(); self.anisotropy.addItems(_ANISOTROPY)
            self.kinematic = QComboBox(); self.kinematic.addItems(_KINEMATIC)
            self.formulation = QComboBox(); self.formulation.addItems(_FORMULATION)
            self.mass = QComboBox(); self.mass.addItems(_MASS_STORAGE)
            form.addRow("Nom", self.mod_name)
            form.addRow("Physique", self.physics)
            form.addRow("Élément", self.element)
            form.addRow("", self.element_info)
            form.addRow("Anisotropy", self.anisotropy)
            form.addRow("Kinematic", self.kinematic)
            form.addRow("Formulation", self.formulation)
            form.addRow("Mass storage", self.mass)
            lay.addLayout(form)
            self.element.currentTextChanged.connect(
                lambda t: self.element_info.setText(_ELEMENT_INFO.get(t, ""))
            )
            self.create_mod.toggled.connect(self._toggle)
            self._toggle(True)

        def initializePage(self):
            dim = self.wizard().page(MeshWizard.PAGE_DIM).dimension()
            elems = _ELEMENTS_2D if dim == 2 else _ELEMENTS_3D
            self.element.clear()
            self.element.addItems(elems)
            models = [
                m.name for m in self.wizard().controller.project.models
                if m.dimension == dim and m.element in (set(_ELEMENTS_2D) | set(_ELEMENTS_3D))
            ]
            self.existing.clear()
            if models:
                self.existing.addItems(models)
            else:
                self.existing.addItem(f"(Aucun modèle {dim}D)")

        def _toggle(self, on: bool):
            for w in (self.mod_name, self.physics, self.element,
                      self.anisotropy, self.kinematic, self.formulation, self.mass):
                w.setEnabled(on)
            self.existing.setEnabled(not on)

        def model_name(self) -> str:
            if self.create_mod.isChecked():
                return self.mod_name.text().strip()
            return self.existing.currentText().strip()

    class MeshGeometryPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Géométrie")
            self.setSubTitle("Forme du domaine à mailler")
            self.form = QFormLayout()
            self.geom_type = QComboBox()
            self.form.addRow("Type", self.geom_type)
            self.cx = QDoubleSpinBox(); self.cy = QDoubleSpinBox(); self.cz = QDoubleSpinBox()
            for s in (self.cx, self.cy, self.cz):
                s.setRange(-1e6, 1e6); s.setDecimals(6)
            self.lx = QDoubleSpinBox(); self.ly = QDoubleSpinBox(); self.lz = QDoubleSpinBox()
            for s, v in ((self.lx, 1.0), (self.ly, 0.4), (self.lz, 1.0)):
                s.setRange(1e-6, 1e6); s.setDecimals(6); s.setValue(v)
            self.radius = QDoubleSpinBox(); self.radius.setRange(1e-6, 1e6); self.radius.setValue(0.5)
            self.height = QDoubleSpinBox(); self.height.setRange(1e-6, 1e6); self.height.setValue(1.0)
            self.file_path = QLineEdit()
            self.color = QLineEdit("CYANx")
            self.form.addRow("Centre X", self.cx)
            self.form.addRow("Centre Y", self.cy)
            self.form.addRow("Centre Z", self.cz)
            self.form.addRow("lx", self.lx)
            self.form.addRow("ly", self.ly)
            self.form.addRow("lz", self.lz)
            self.form.addRow("Rayon", self.radius)
            self.form.addRow("Hauteur", self.height)
            row = QHBoxLayout()
            row.addWidget(self.file_path)
            btn = __import__("PyQt6.QtWidgets", fromlist=["QPushButton"]).QPushButton("Parcourir…")
            btn.clicked.connect(self._browse)
            row.addWidget(btn)
            wrap = QWidget(); wrap.setLayout(row)
            self.form.addRow("Fichier (.msh / .brep / .step…)", wrap)
            self.form.addRow("Couleur", self.color)
            lay = QVBoxLayout(self)
            lay.addLayout(self.form)
            self.geom_type.currentTextChanged.connect(self._update_visibility)
            lay.addStretch()

        def initializePage(self):
            dim = self.wizard().page(MeshWizard.PAGE_DIM).dimension()
            self.geom_type.blockSignals(True)
            self.geom_type.clear()
            self.geom_type.addItems(_GEOM_2D if dim == 2 else _GEOM_3D)
            self.geom_type.blockSignals(False)
            self.cz.setEnabled(dim == 3)
            self._update_visibility()

        def _browse(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Maillage / CAD", "",
                "Maillage (*.msh *.vtk);;CAD OpenCASCADE (*.brep *.brp);;STEP (*.step *.stp);;IGES (*.iges *.igs);;Gmsh geo (*.geo);;Tous (*)"
            )
            if path:
                self.file_path.setText(path)

        def _update_visibility(self, *_a):
            g = self.geom_type.currentText()
            rect = g in ("Rectangle", "Boîte (H8)")
            disk = g in ("Disque", "Sphère")
            cyl = g == "Cylindre"
            external = g == "Fichier externe"
            for w, vis in (
                (self.lx, rect), (self.ly, rect or cyl), (self.lz, g == "Boîte (H8)"),
                (self.radius, disk or cyl), (self.height, cyl),
                (self.file_path, external),
            ):
                w.setEnabled(vis)

        def get_center(self, dimension: int) -> List[float]:
            c = [self.cx.value(), self.cy.value()]
            if dimension == 3:
                c.append(self.cz.value())
            return c

    class MeshRefinementPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Raffinement")
            self.setSubTitle("Subdivision du maillage")
            form = QFormLayout(self)
            self.mesh_type = QComboBox()
            self.nx = QSpinBox(); self.ny = QSpinBox(); self.nz = QSpinBox()
            for s, v in ((self.nx, 6), (self.ny, 3), (self.nz, 3)):
                s.setRange(1, 500); s.setValue(v)
            self.nr = QSpinBox(); self.ntheta = QSpinBox(); self.nphi = QSpinBox()
            for s, v in ((self.nr, 4), (self.ntheta, 16), (self.nphi, 12)):
                s.setRange(1, 500); s.setValue(v)
            form.addRow("mesh_type (2D)", self.mesh_type)
            form.addRow("nx", self.nx)
            form.addRow("ny", self.ny)
            form.addRow("nz", self.nz)
            form.addRow("nr (radial)", self.nr)
            form.addRow("ntheta", self.ntheta)
            form.addRow("nphi", self.nphi)

        def initializePage(self):
            dim = self.wizard().page(MeshWizard.PAGE_DIM).dimension()
            self.mesh_type.clear()
            self.mesh_type.addItems(_MESH_TYPES_2D if dim == 2 else _MESH_TYPES_3D)
            geom = self.wizard().page(MeshWizard.PAGE_GEOM).geom_type.currentText()
            structured = geom in ("Rectangle", "Boîte (H8)")
            polar = geom in ("Disque", "Sphère", "Cylindre")
            self.nx.setEnabled(structured)
            self.ny.setEnabled(structured)
            self.nz.setEnabled(structured and dim == 3)
            self.nr.setEnabled(polar)
            self.ntheta.setEnabled(polar)
            self.nphi.setEnabled(geom == "Sphère")
            self.mesh_type.setEnabled(dim == 2 and structured)

    class MeshBoundaryPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Contacteurs de bord")
            self.setSubTitle("Surfaces de contact sur le maillage (CLxxx / CSpxx…)")
            form = QFormLayout(self)
            self.add_tact = QCheckBox("Ajouter un contacteur de bord")
            self.add_tact.setChecked(True)
            self.shape = QComboBox()
            self.color = QLineEdit("CYANx")
            self.by_group = QLineEdit()
            self.by_group.setPlaceholderText("optionnel — groupe de nœuds/faces")
            form.addRow(self.add_tact)
            form.addRow("Shape", self.shape)
            form.addRow("Color", self.color)
            form.addRow("by group", self.by_group)

        def initializePage(self):
            dim = self.wizard().page(MeshWizard.PAGE_DIM).dimension()
            self.shape.clear()
            if dim == 2:
                self.shape.addItems(["CLxxx", "ALpxx", "PT2Dx"])
            else:
                self.shape.addItems(["CSpxx", "ASpxx", "PT3Dx"])

        def contactors(self) -> List[dict]:
            if not self.add_tact.isChecked():
                return []
            entry = {
                "shape": self.shape.currentText(),
                "color": self.color.text().strip() or "CYANx",
            }
            byg = self.by_group.text().strip()
            if byg:
                entry["by"] = byg
            return [entry]

    class MeshSummaryPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Résumé")
            self.setSubTitle("Vérifiez avant de générer")
            lay = QVBoxLayout(self)
            self.text = QTextEdit()
            self.text.setReadOnly(True)
            lay.addWidget(self.text)

        def initializePage(self):
            w = self.wizard()
            dim_p = w.page(MeshWizard.PAGE_DIM)
            mat_p = w.page(MeshWizard.PAGE_MAT)
            mod_p = w.page(MeshWizard.PAGE_MODEL)
            geom_p = w.page(MeshWizard.PAGE_GEOM)
            ref_p = w.page(MeshWizard.PAGE_REFINE)
            bound_p = w.page(MeshWizard.PAGE_BOUNDARY)
            dim = dim_p.dimension()
            lines = [
                f"Dimension : {dim}D",
                f"Matériau  : {mat_p.material_name()} "
                f"{'(nouveau)' if mat_p.create_mat.isChecked() else '(existant)'}",
                f"Modèle    : {mod_p.model_name()} "
                f"{'(nouveau)' if mod_p.create_mod.isChecked() else '(existant)'}",
            ]
            if mod_p.create_mod.isChecked():
                lines.append(f"  élément={mod_p.element.currentText()}  physics={mod_p.physics.currentText()}")
            lines.append(f"Géométrie : {geom_p.geom_type.currentText()}  centre={geom_p.get_center(dim)}")
            g = geom_p.geom_type.currentText()
            if g in ("Rectangle", "Boîte (H8)"):
                lines.append(
                    f"  lx={geom_p.lx.value()} ly={geom_p.ly.value()} "
                    f"nx={ref_p.nx.value()} ny={ref_p.ny.value()} "
                    f"mesh_type={ref_p.mesh_type.currentText()}"
                )
            lines.append(f"Contacteurs : {bound_p.contactors()}")
            self.text.setPlainText("\n".join(lines))

    # ===================================================================== wizard
    class MeshWizard(QWizard):
        PAGE_INTRO = 0
        PAGE_DIM = 1
        PAGE_MAT = 2
        PAGE_MODEL = 3
        PAGE_GEOM = 4
        PAGE_REFINE = 5
        PAGE_BOUNDARY = 6
        PAGE_SUMMARY = 7

        def __init__(self, controller, parent=None):
            super().__init__(parent)
            self.controller = controller
            self.setWindowTitle("Assistant Corps Déformable (EF)")
            self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
            self.resize(780, 560)
            self.addPage(MeshIntroPage())
            self.addPage(MeshDimensionPage())
            self.addPage(MeshMaterialPage())
            self.addPage(MeshModelPage())
            self.addPage(MeshGeometryPage())
            self.addPage(MeshRefinementPage())
            self.addPage(MeshBoundaryPage())
            self.addPage(MeshSummaryPage())
            self.setButtonText(QWizard.WizardButton.NextButton, "Suivant")
            self.setButtonText(QWizard.WizardButton.BackButton, "Retour")
            self.setButtonText(QWizard.WizardButton.FinishButton, "Générer le maillage")
            self.setButtonText(QWizard.WizardButton.CancelButton, "Annuler")

        def accept(self):
            try:
                av = self._generate()
                QMessageBox.information(
                    self, "Succès",
                    f"Corps déformable créé.\n"
                    f"avatar_id={av.avatar_id[:12]}…\n"
                    f"type={av.avatar_type.value}\n"
                    f"mesh_params keys={list((av.mesh_params or {}).keys())}",
                )
                super().accept()
            except Exception as exc:
                self.controller.journal.exception("MeshWizard failed", exc)
                QMessageBox.critical(self, "Erreur", str(exc))

        def _generate(self) -> Avatar:
            dim_p = self.page(self.PAGE_DIM)
            mat_p = self.page(self.PAGE_MAT)
            mod_p = self.page(self.PAGE_MODEL)
            geom_p = self.page(self.PAGE_GEOM)
            ref_p = self.page(self.PAGE_REFINE)
            bound_p = self.page(self.PAGE_BOUNDARY)
            dim = dim_p.dimension()
            ctrl = self.controller

            if dim != ctrl.project.dimension:
                # align project dimension if empty-ish, else warn via validation later
                if not ctrl.project.avatars and not ctrl.project.models:
                    ctrl.project.dimension = dim
                elif dim != ctrl.project.dimension:
                    raise ValidationError(
                        f"Projet en {ctrl.project.dimension}D — "
                        f"choisissez la même dimension ou File→New."
                    )

            with ctrl.batch():
                # material
                mat_name = mat_p.material_name()
                if not mat_name or mat_name.startswith("("):
                    raise ValidationError("Nom de matériau invalide")
                if mat_p.create_mat.isChecked():
                    if not any(m.name == mat_name for m in ctrl.project.materials):
                        ctrl.add_material(Material(
                            name=mat_name,
                            material_type=MaterialType(mat_p.mat_type.currentText()),
                            density=mat_p.density.value(),
                            properties=mat_p.collect_props(),
                        ))
                # model
                mod_name = mod_p.model_name()
                if not mod_name or mod_name.startswith("("):
                    raise ValidationError("Nom de modèle invalide")
                if mod_p.create_mod.isChecked():
                    if not any(m.name == mod_name for m in ctrl.project.models):
                        ctrl.add_model(Model(
                            name=mod_name,
                            physics=mod_p.physics.currentText(),
                            element=mod_p.element.currentText(),
                            dimension=dim,
                            options={
                                "anisotropy": mod_p.anisotropy.currentText(),
                                "kinematic": mod_p.kinematic.currentText(),
                                "formulation": mod_p.formulation.currentText(),
                                "mass_storage": mod_p.mass.currentText(),
                                "material": "elas_",
                                "external_model": "no___",
                            },
                        ))

                center = geom_p.get_center(dim)
                color = geom_p.color.text().strip() or "CYANx"
                contactors = bound_p.contactors()
                geom = geom_p.geom_type.currentText()

                if geom == "Rectangle" and dim == 2:
                    av = pre.meshed_rectangle(
                        lx=geom_p.lx.value(), ly=geom_p.ly.value(),
                        nx=ref_p.nx.value(), ny=ref_p.ny.value(),
                        center=center, model=mod_name, material=mat_name,
                        color=color, mesh_type=ref_p.mesh_type.currentText(),
                        contactors=contactors,
                    )
                else:
                    # generic mesh avatar — intent stored for engine / pre emission
                    mp: Dict[str, Any] = {
                        "geom": geom, "dim": dim,
                        "cx": center[0], "cy": center[1],
                    }
                    if dim == 3:
                        mp["cz"] = center[2]
                    if geom in ("Rectangle", "Boîte (H8)"):
                        mp.update({
                            "lx": geom_p.lx.value(), "ly": geom_p.ly.value(),
                            "nx": ref_p.nx.value(), "ny": ref_p.ny.value(),
                        })
                        if dim == 3:
                            mp["lz"] = geom_p.lz.value()
                            mp["nz"] = ref_p.nz.value()
                        if dim == 2:
                            mp["mesh_type"] = ref_p.mesh_type.currentText()
                    elif geom in ("Disque", "Sphère"):
                        mp.update({
                            "r": geom_p.radius.value(),
                            "nr": ref_p.nr.value(), "ntheta": ref_p.ntheta.value(),
                        })
                        if geom == "Sphère":
                            mp["nphi"] = ref_p.nphi.value()
                    elif geom == "Cylindre":
                        mp.update({
                            "r": geom_p.radius.value(), "h": geom_p.height.value(),
                            "nr": ref_p.nr.value(), "ntheta": ref_p.ntheta.value(),
                            "nz": ref_p.nz.value(),
                        })
                    elif geom == "Fichier externe":
                        mp["filepath"] = geom_p.file_path.text().strip()
                        if not mp["filepath"]:
                            raise ValidationError("Chemin de fichier maillage requis")
                        mp["geom"] = "Fichier externe"
                        mp["dim"] = int(dim)
                        # characteristic length for gmsh when converting .brep/.step
                        try:
                            if hasattr(ref_p, "lc") and ref_p.lc is not None:
                                mp["mesh_size"] = float(ref_p.lc.value())
                        except Exception:
                            pass
                        # fallback from nx-like controls if present
                        if "mesh_size" not in mp and hasattr(ref_p, "nx"):
                            try:
                                # crude: smaller nx → coarser; use 1/nx of unit box as hint
                                mp["mesh_size"] = max(1e-4, 1.0 / max(1, int(ref_p.nx.value())))
                            except Exception:
                                pass
                    av = Avatar(
                        avatar_type=AvatarType.MESH_DEFORMABLE,
                        center=center,
                        material_name=mat_name,
                        model_name=mod_name,
                        color=color,
                        origin=AvatarOrigin.MANUAL,
                        mesh_params=mp,
                        contactors=list(contactors),
                    )
                ctrl.add_avatar(av)
            ctrl.journal.info(
                f"MeshWizard: {geom} → {av.avatar_id[:12]}… mat={mat_name} mod={mod_name}"
            )
            return av

    return MeshWizard(controller, parent)
