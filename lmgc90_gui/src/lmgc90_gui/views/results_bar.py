"""Barre « Résultats » du Viewer3D : slider de pas de temps, lecture, couleur."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QWidget,
)
from PyQt6.QtCore import Qt

from ..utils.display_reader import DisplaySeries

_UNIFORM = "(uniforme)"


class ResultsBar(QWidget):
    def __init__(self, viewer):
        super().__init__(viewer)
        self.viewer = viewer
        self.series: Optional[DisplaySeries] = None
        self._names: set[str] = set()          # acteurs posés ("res:<pvd>")
        self._clim: Optional[tuple] = None
        self._first = True

        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 0, 2, 0)
        self.btn_load = QPushButton("📂 Résultats…")
        self.btn_load.setToolTip("Charger DISPLAY/*.pvd d'un calcul")
        self.btn_play = QPushButton("▶")
        self.btn_play.setCheckable(True)
        self.btn_play.setFixedWidth(34)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.label = QLabel("—")
        self.label.setMinimumWidth(150)
        self.field = QComboBox()
        self.field.setToolTip("Champ utilisé pour la couleur")
        self.field.addItem(_UNIFORM)
        self.fps = QSpinBox()
        self.fps.setRange(1, 60)
        self.fps.setValue(15)
        self.fps.setSuffix(" i/s")
        self.follow = QCheckBox("Suivre")
        self.follow.setToolTip("Recharger les .pvd pendant le calcul")
        for w in (self.btn_load, self.btn_play, self.slider, self.label,
                  self.field, self.fps, self.follow):
            lay.addWidget(w, 1 if w is self.slider else 0)

        self.timer = QTimer(self)
        self.watch = QTimer(self)
        self.watch.setInterval(2000)
        self.btn_load.clicked.connect(self.choose_and_load)
        self.btn_play.toggled.connect(self._toggle_play)
        self.slider.valueChanged.connect(self.show_frame)
        self.timer.timeout.connect(self._tick)
        self.watch.timeout.connect(self._refresh_series)
        self.follow.toggled.connect(
            lambda on: self.watch.start() if on else self.watch.stop())
        self.fps.valueChanged.connect(self._set_interval)
        self.field.currentTextChanged.connect(self._on_field)
        self._set_interval()

    # ------------------------------------------------------------ chargement
    def choose_and_load(self) -> None:
        wd = getattr(self.viewer.controller, "work_dir", None)
        start = str(Path(wd) / "DISPLAY") if wd else ""
        path = QFileDialog.getExistingDirectory(
            self, "Dossier DISPLAY d'un calcul", start)
        if path:
            self.load(path)

    def load(self, display_dir) -> None:
        try:
            series = DisplaySeries(display_dir)
        except Exception as exc:
            self.viewer._status(f"❌ Résultats : {exc}")
            return
        self.viewer.clear()          # remet aussi cette barre à zéro (on_cleared)
        self.series = series
        self._first, self._clim = True, None
        self.slider.blockSignals(True)
        self.slider.setRange(0, len(series) - 1)
        self.slider.setValue(0)
        self.slider.setEnabled(True)
        self.slider.blockSignals(False)
        ds = next(iter(series.frame(0).values()), None)
        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem(_UNIFORM)
        if ds is not None:
            for n in ds.point_data.keys():
                self.field.addItem(f"point:{n}")
            for n in ds.cell_data.keys():
                self.field.addItem(f"cell:{n}")
        self.field.blockSignals(False)
        self.show_frame(0)
        self.viewer._status(
            f"Résultats : {len(series)} pas, fichiers {', '.join(series.names)}")

    # --------------------------------------------------------------- affichage
    def _scalars(self, ds):
        txt = self.field.currentText()
        if txt == _UNIFORM or ":" not in txt:
            return None, None
        kind, name = txt.split(":", 1)
        data = ds.point_data if kind == "point" else ds.cell_data
        if name not in data:
            return None, None
        return name, kind

    def show_frame(self, i: int) -> None:
        if self.series is None or not (0 <= i < len(self.series)):
            return
        pl = self.viewer.plotter
        frame = self.series.frame(i)
        seen = set()
        for pvd, ds in frame.items():
            actor_name = f"res:{pvd}"
            seen.add(actor_name)
            name, kind = self._scalars(ds)
            kw = dict(name=actor_name, reset_camera=False, render=False,
                      pickable=False, show_edges=True, edge_color="#223344")
            if name is not None:
                if self._clim is None:
                    lo, hi = ds[name].min(), ds[name].max()
                    self._clim = (float(lo), float(hi if hi > lo else lo + 1))
                kw.update(scalars=name, preference=kind, clim=self._clim,
                          cmap="viridis", show_scalar_bar=False)
            else:
                kw["color"] = "#4287f5"
            pl.add_mesh(ds, **kw)
        for stale in self._names - seen:
            pl.remove_actor(stale, render=False)
        self._names = seen
        if self._first and seen:
            self._first = False
            self.viewer._reset_camera()   # une seule fois : pas de saut ensuite
        pl.render()
        self.label.setText(f"pas {i + 1}/{len(self.series)}  t = {self.series.time(i):.6g} s")

    def _on_field(self, _):
        self._clim = None
        if self.series is not None:
            self.show_frame(self.slider.value())

    # ---------------------------------------------------------------- lecture
    def _set_interval(self, *_):
        self.timer.setInterval(max(1, int(1000 / self.fps.value())))

    def _toggle_play(self, on: bool) -> None:
        self.btn_play.setText("⏸" if on else "▶")
        if on and self.series is not None:
            if self.slider.value() >= self.slider.maximum():
                self.slider.setValue(0)
            self.timer.start()
        else:
            self.timer.stop()

    def _tick(self) -> None:
        v = self.slider.value()
        if v >= self.slider.maximum():
            self.btn_play.setChecked(False)
        else:
            self.slider.setValue(v + 1)      # déclenche show_frame

    def _refresh_series(self) -> None:
        if self.series is None:
            return
        current = self.slider.value()
        follow_latest = current == self.slider.maximum()
        try:
            n = self.series.reload()
        except Exception:
            return                            # fichier en cours d'écriture
        latest = n - 1
        if latest != self.slider.maximum():
            self.slider.setMaximum(latest)
        target = latest if follow_latest else min(current, latest)
        if self.slider.value() != target:
            self.slider.setValue(target)
        elif target == current:
            self.show_frame(target)

    # ------------------------------------------------------------ appelé par clear()
    def on_cleared(self) -> None:
        self.timer.stop()
        self.btn_play.blockSignals(True)
        self.btn_play.setChecked(False)
        self.btn_play.setText("▶")
        self.btn_play.blockSignals(False)
        self._names.clear()
        self.series = None
        self.slider.setEnabled(False)
        self.label.setText("—")