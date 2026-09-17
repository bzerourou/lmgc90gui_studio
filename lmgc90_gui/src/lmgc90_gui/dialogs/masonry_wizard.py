"""MasonryWizard — port of legacy masonery_wizard.py onto core + ProjectController.

Pages: Intro → Dimension → Material → Model → Brick dims → Layout → Transform → Summary.
Generation uses MasonryConfig / expand_masonry (rigidPolygon), no _pylmgc_* containers.
"""
from __future__ import annotations

from typing import Optional

from lmgc90_core import MasonryConfig, Material, MaterialType, Model, ValidationError, pre


_PATTERN_INFO = {
    "Standard": "Décalage ½ brique sur les rangs impairs (appareil courant).",
    "Running Bond": "Décalage progressif d'un tiers de brique par rang.",
    "Stack Bond": "Joints parfaitement alignés (colonnes verticales).",
    "Flemish Bond": "Alternance panneresse (lx) / boutisse (lx/2).",
}


def create_masonry_wizard(controller, parent=None):
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
        QHBoxLayout, QLabel, QLineEdit, QMessageBox, QRadioButton, QSpinBox,
        QTextEdit, QVBoxLayout, QWizard, QWizardPage,
    )

    class MasonryIntroPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Assistant de maçonnerie")
            self.setSubTitle("Génération de murs en briques (rigidPolygon)")
            lay = QVBoxLayout(self)
            lay.addWidget(QLabel(
                "<p>Flux aligné sur <b>masonery_wizard.py</b> :</p>"
                "<ol>"
                "<li>Dimension (2D recommandé)</li>"
                "<li>Matériau RIGID</li>"
                "<li>Modèle Rxx2D / Rxx3D</li>"
                "<li>Dimensions de brique</li>"
                "<li>Appareil + joint + groupe</li>"
                "<li>Transformations (translate / copies)</li>"
                "<li>Résumé et génération</li>"
                "</ol>"
                "<p>Appareils : Standard, Running Bond, Stack Bond, Flemish Bond.</p>"
                "<p>Les briques sont des <code>rigidPolygon</code> dans "
                "<code>lmgc90_core.Project</code> (pas d'injection pylmgc directe).</p>"
            ))
            lay.addStretch()

    class MasonryDimensionPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Dimension")
            lay = QVBoxLayout(self)
            self.dim_2d = QRadioButton("2D (plan)")
            self.dim_3d = QRadioButton("3D (métadonnées lz — géométrie encore 2D)")
            self.dim_2d.setChecked(True)
            lay.addWidget(self.dim_2d)
            lay.addWidget(self.dim_3d)
            self.hint = QLabel("")
            lay.addWidget(self.hint)
            lay.addStretch()

        def initializePage(self):
            d = self.wizard().controller.project.dimension
            (self.dim_3d if d == 3 else self.dim_2d).setChecked(True)
            self.hint.setText(f"Dimension projet : {d}D — le générateur core est 2D.")

        def dimension(self) -> int:
            return 2 if self.dim_2d.isChecked() else 3

    class MasonryMaterialPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Matériau")
            lay = QVBoxLayout(self)
            self.create_mat = QCheckBox("Créer un nouveau matériau RIGID")
            self.create_mat.setChecked(True)
            lay.addWidget(self.create_mat)
            self.existing = QComboBox()
            lay.addWidget(QLabel("Ou matériau existant :"))
            lay.addWidget(self.existing)
            form = QFormLayout()
            self.mat_name = QLineEdit("brick")
            self.mat_name.setMaxLength(5)
            self.density = QDoubleSpinBox()
            self.density.setRange(1, 1e5)
            self.density.setValue(1800.0)
            form.addRow("Nom", self.mat_name)
            form.addRow("Densité", self.density)
            lay.addLayout(form)
            self.create_mat.toggled.connect(self._toggle)
            self._toggle(True)

        def initializePage(self):
            mats = [m.name for m in self.wizard().controller.project.materials]
            self.existing.clear()
            self.existing.addItems(mats or ["(Aucun)"])

        def _toggle(self, on: bool):
            self.mat_name.setEnabled(on)
            self.density.setEnabled(on)
            self.existing.setEnabled(not on)

        def material_name(self) -> str:
            if self.create_mat.isChecked():
                return self.mat_name.text().strip()
            return self.existing.currentText().strip()

    class MasonryModelPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Modèle")
            lay = QVBoxLayout(self)
            self.create_mod = QCheckBox("Créer un nouveau modèle rigide")
            self.create_mod.setChecked(True)
            lay.addWidget(self.create_mod)
            self.existing = QComboBox()
            lay.addWidget(QLabel("Ou modèle existant :"))
            lay.addWidget(self.existing)
            form = QFormLayout()
            self.mod_name = QLineEdit("rigid")
            self.mod_name.setMaxLength(5)
            form.addRow("Nom", self.mod_name)
            lay.addLayout(form)
            self.create_mod.toggled.connect(lambda on: (
                self.mod_name.setEnabled(on), self.existing.setEnabled(not on)
            ))

        def initializePage(self):
            dim = self.wizard().page(MasonryWizard.PAGE_DIMENSION).dimension()
            el = "Rxx2D" if dim == 2 else "Rxx3D"
            mods = [
                m.name for m in self.wizard().controller.project.models
                if m.element in ("Rxx2D", "Rxx3D")
            ]
            self.existing.clear()
            self.existing.addItems(mods or [f"(Aucun modèle {el})"])
            self.mod_name.setToolTip(f"Élément forcé : {el}")

        def model_name(self) -> str:
            if self.create_mod.isChecked():
                return self.mod_name.text().strip()
            return self.existing.currentText().strip()

    class BrickDimensionsPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Dimensions de la brique")
            form = QFormLayout(self)
            self.brick_name = QLineEdit("std")
            self.lx = QDoubleSpinBox(); self.ly = QDoubleSpinBox(); self.lz = QDoubleSpinBox()
            self.lx.setRange(1e-4, 10); self.lx.setDecimals(4); self.lx.setValue(0.20)
            self.ly.setRange(1e-4, 10); self.ly.setDecimals(4); self.ly.setValue(0.065)
            self.lz.setRange(1e-4, 10); self.lz.setDecimals(4); self.lz.setValue(0.10)
            form.addRow("Nom brique", self.brick_name)
            form.addRow("lx (longueur)", self.lx)
            form.addRow("ly (hauteur)", self.ly)
            form.addRow("lz (profondeur / 3D meta)", self.lz)
            form.addRow(QLabel("Brique française courante : 0,20 × 0,065 m"))

    class LayoutPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Appareil / layout")
            lay = QVBoxLayout(self)
            form = QFormLayout()
            self.pattern = QComboBox()
            self.pattern.addItems(list(_PATTERN_INFO.keys()))
            self.pattern_info = QLabel(_PATTERN_INFO["Standard"])
            self.pattern_info.setWordWrap(True)
            self.rows = QSpinBox(); self.rows.setRange(1, 500); self.rows.setValue(8)
            self.cols = QSpinBox(); self.cols.setRange(1, 500); self.cols.setValue(5)
            self.joint = QDoubleSpinBox(); self.joint.setRange(0, 0.5); self.joint.setDecimals(4)
            self.joint.setValue(0.010)
            self.ox = QDoubleSpinBox(); self.oy = QDoubleSpinBox(); self.oz = QDoubleSpinBox()
            for s in (self.ox, self.oy, self.oz):
                s.setRange(-1e4, 1e4); s.setDecimals(4)
            self.color = QLineEdit("REEDx")
            self.store_group = QCheckBox("Enregistrer le groupe")
            self.store_group.setChecked(True)
            self.group_name = QLineEdit("mason")
            self.fill_ends = QCheckBox("Demi-briques aux extrémités (Standard)")
            self.add_law = QCheckBox("Ajouter loi IQS_CLB + see POLYG/POLYG")
            self.add_law.setChecked(True)
            self.law_name = QLineEdit("IQS")
            self.law_name.setMaxLength(5)
            self.fric = QDoubleSpinBox(); self.fric.setRange(0, 2); self.fric.setValue(0.6)
            self.fric.setDecimals(3)
            for label, w in (
                ("Appareil", self.pattern),
                ("Courses (rows)", self.rows),
                ("Colonnes", self.cols),
                ("Joint (m)", self.joint),
                ("Offset X", self.ox),
                ("Offset Y", self.oy),
                ("Offset Z", self.oz),
                ("Couleur", self.color),
                ("Nom de groupe", self.group_name),
                ("Loi", self.law_name),
                ("Friction", self.fric),
            ):
                form.addRow(label, w)
            lay.addLayout(form)
            lay.addWidget(self.pattern_info)
            lay.addWidget(self.fill_ends)
            lay.addWidget(self.store_group)
            lay.addWidget(self.add_law)
            self.pattern.currentTextChanged.connect(
                lambda t: self.pattern_info.setText(_PATTERN_INFO.get(t, ""))
            )

    class TransformPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Transformations")
            self.setSubTitle("Appliquées après placement des briques")
            lay = QVBoxLayout(self)
            self.translate = QCheckBox("Translation globale")
            self.tx = QDoubleSpinBox(); self.ty = QDoubleSpinBox(); self.tz = QDoubleSpinBox()
            for s in (self.tx, self.ty, self.tz):
                s.setRange(-1e4, 1e4); s.setDecimals(4)
            tf = QFormLayout()
            tf.addRow(self.translate)
            tf.addRow("tx", self.tx); tf.addRow("ty", self.ty); tf.addRow("tz", self.tz)
            lay.addLayout(tf)

            self.copy = QCheckBox("Copies additionnelles")
            self.n_copies = QSpinBox(); self.n_copies.setRange(0, 50); self.n_copies.setValue(0)
            self.cdx = QDoubleSpinBox(); self.cdy = QDoubleSpinBox(); self.cdz = QDoubleSpinBox()
            for s in (self.cdx, self.cdy, self.cdz):
                s.setRange(-1e4, 1e4); s.setDecimals(4)
            cf = QFormLayout()
            cf.addRow(self.copy)
            cf.addRow("Nombre de copies", self.n_copies)
            cf.addRow("dx", self.cdx); cf.addRow("dy", self.cdy); cf.addRow("dz", self.cdz)
            lay.addLayout(cf)
            lay.addWidget(QLabel(
                "Note : la rotation pure n'est pas appliquée côté core dans cette version "
                "(métadonnée conservée dans le journal)."
            ))
            lay.addStretch()

    class MasonrySummaryPage(QWizardPage):
        def __init__(self):
            super().__init__()
            self.setTitle("Résumé")
            lay = QVBoxLayout(self)
            self.text = QTextEdit()
            self.text.setReadOnly(True)
            lay.addWidget(self.text)

        def initializePage(self):
            w = self.wizard()
            dim_p = w.page(MasonryWizard.PAGE_DIMENSION)
            mat_p = w.page(MasonryWizard.PAGE_MATERIAL)
            mod_p = w.page(MasonryWizard.PAGE_MODEL)
            br_p = w.page(MasonryWizard.PAGE_BRICK_DIM)
            lay_p = w.page(MasonryWizard.PAGE_LAYOUT)
            tf_p = w.page(MasonryWizard.PAGE_TRANSFORM)
            lines = [
                f"Dimension UI : {dim_p.dimension()}D (générateur core = 2D)",
                f"Matériau : {mat_p.material_name()}",
                f"Modèle : {mod_p.model_name()}",
                f"Brique : {br_p.brick_name.text()}  "
                f"lx={br_p.lx.value()} ly={br_p.ly.value()} lz={br_p.lz.value()}",
                f"Appareil : {lay_p.pattern.currentText()}  "
                f"{lay_p.rows.value()}×{lay_p.cols.value()}  joint={lay_p.joint.value()}",
                f"Origine : ({lay_p.ox.value()}, {lay_p.oy.value()})",
                f"Groupe : {lay_p.group_name.text() if lay_p.store_group.isChecked() else '(aucun)'}",
                f"Loi IQS : {'oui' if lay_p.add_law.isChecked() else 'non'}",
            ]
            if tf_p.translate.isChecked():
                lines.append(f"Translation : ({tf_p.tx.value()}, {tf_p.ty.value()})")
            if tf_p.copy.isChecked() and tf_p.n_copies.value() > 0:
                lines.append(
                    f"Copies : {tf_p.n_copies.value()}  "
                    f"Δ=({tf_p.cdx.value()}, {tf_p.cdy.value()})"
                )
            self.text.setPlainText("\n".join(lines))

    class MasonryWizard(QWizard):
        PAGE_INTRO = 0
        PAGE_DIMENSION = 1
        PAGE_MATERIAL = 2
        PAGE_MODEL = 3
        PAGE_BRICK_DIM = 4
        PAGE_LAYOUT = 5
        PAGE_TRANSFORM = 6
        PAGE_SUMMARY = 7

        def __init__(self, controller, parent=None):
            super().__init__(parent)
            self.controller = controller
            self.setWindowTitle("Assistant de Maçonnerie")
            self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
            self.resize(780, 600)
            self.addPage(MasonryIntroPage())
            self.addPage(MasonryDimensionPage())
            self.addPage(MasonryMaterialPage())
            self.addPage(MasonryModelPage())
            self.addPage(BrickDimensionsPage())
            self.addPage(LayoutPage())
            self.addPage(TransformPage())
            self.addPage(MasonrySummaryPage())
            self.setButtonText(QWizard.WizardButton.NextButton, "Suivant")
            self.setButtonText(QWizard.WizardButton.BackButton, "Retour")
            self.setButtonText(QWizard.WizardButton.FinishButton, "Générer")
            self.setButtonText(QWizard.WizardButton.CancelButton, "Annuler")

        def accept(self):
            try:
                n = self._generate()
                QMessageBox.information(
                    self, "Succès", f"Structure maçonnée générée : {n} brique(s)."
                )
                super().accept()
            except Exception as exc:
                self.controller.journal.exception("MasonryWizard failed", exc)
                QMessageBox.critical(self, "Erreur", str(exc))

        def _generate(self) -> int:
            dim_p = self.page(self.PAGE_DIMENSION)
            mat_p = self.page(self.PAGE_MATERIAL)
            mod_p = self.page(self.PAGE_MODEL)
            br_p = self.page(self.PAGE_BRICK_DIM)
            lay_p = self.page(self.PAGE_LAYOUT)
            tf_p = self.page(self.PAGE_TRANSFORM)
            ctrl = self.controller
            dim = dim_p.dimension()

            if ctrl.project.dimension != 2 and not ctrl.project.avatars:
                ctrl.project.dimension = 2
            if ctrl.project.dimension != 2:
                raise ValidationError(
                    "Le générateur de maçonnerie core est 2D. "
                    "Passez le projet en 2D (File → New) ou videz les avatars 3D."
                )

            mat_name = mat_p.material_name()
            mod_name = mod_p.model_name()
            if not mat_name or mat_name.startswith("("):
                raise ValidationError("Matériau invalide")
            if not mod_name or mod_name.startswith("("):
                raise ValidationError("Modèle invalide")

            bond_map = {
                "Standard": "standard",
                "Running Bond": "running",
                "Stack Bond": "stack",
                "Flemish Bond": "flemish",
            }
            bond = bond_map.get(lay_p.pattern.currentText(), "standard")

            translate = None
            if tf_p.translate.isChecked():
                translate = (tf_p.tx.value(), tf_p.ty.value(), tf_p.tz.value())
            copy_offset = None
            n_copies = 0
            if tf_p.copy.isChecked() and tf_p.n_copies.value() > 0:
                copy_offset = (tf_p.cdx.value(), tf_p.cdy.value(), tf_p.cdz.value())
                n_copies = tf_p.n_copies.value()

            cfg = MasonryConfig(
                n_courses=lay_p.rows.value(),
                n_columns=lay_p.cols.value(),
                brick_lx=br_p.lx.value(),
                brick_ly=br_p.ly.value(),
                brick_lz=br_p.lz.value(),
                joint=lay_p.joint.value(),
                bond=bond,
                origin_x=lay_p.ox.value(),
                origin_y=lay_p.oy.value(),
                origin_z=lay_p.oz.value(),
                material_name=mat_name,
                model_name=mod_name,
                color=lay_p.color.text().strip() or "REEDx",
                group_name=(
                    lay_p.group_name.text().strip() or None
                    if lay_p.store_group.isChecked() else None
                ),
                brick_name=br_p.brick_name.text().strip() or "std",
                fill_ends=lay_p.fill_ends.isChecked(),
                translate=translate,
                copy_offset=copy_offset,
                n_copies=n_copies,
            )

            with ctrl.batch():
                if mat_p.create_mat.isChecked() and not any(
                    m.name == mat_name for m in ctrl.project.materials
                ):
                    ctrl.add_material(Material(
                        name=mat_name,
                        material_type=MaterialType.RIGID,
                        density=mat_p.density.value(),
                    ))
                if mod_p.create_mod.isChecked() and not any(
                    m.name == mod_name for m in ctrl.project.models
                ):
                    ctrl.add_model(Model(
                        name=mod_name,
                        physics="MECAx",
                        element="Rxx2D",
                        dimension=2,
                    ))

                bricks = ctrl.apply_masonry(cfg)

                if lay_p.add_law.isChecked():
                    law_name = lay_p.law_name.text().strip() or "IQS"
                    if not any(l.name == law_name for l in ctrl.project.laws):
                        ctrl.add_law(pre.tact_behav(
                            name=law_name, law="IQS_CLB", fric=lay_p.fric.value(),
                        ))
                    color = lay_p.color.text().strip() or "REEDx"
                    if not any(
                        r.candidate_color == color and r.antagonist_color == color
                        for r in ctrl.project.visibility
                    ):
                        ctrl.add_visibility(pre.see_table(
                            CorpsCandidat="RBDY2", candidat="POLYG", colorCandidat=color,
                            CorpsAntagoniste="RBDY2", antagoniste="POLYG",
                            colorAntagoniste=color,
                            behav=law_name, alert=0.02,
                        ))

            ctrl.journal.info(
                f"MasonryWizard: {bond} {len(bricks)} bricks group={cfg.group_name}"
            )
            return len(bricks)

    return MasonryWizard(controller, parent)
