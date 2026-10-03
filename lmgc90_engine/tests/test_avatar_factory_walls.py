"""Wall avatar factory calls must match the supported pre constructors."""
from __future__ import annotations

from lmgc90_core import pre
from lmgc90_engine.avatar_factory import build_avatar


class _WallPre:
    def fineWall(
        self, *, l, r, center, model, material, color="BLUEx", nb_vertex=10,
    ):
        return {
            "kind": "fineWall", "l": l, "r": r, "center": center,
            "model": model, "material": material, "color": color,
            "nb_vertex": nb_vertex,
        }

    def granuloRoughWall(
        self, *, l, rmin, rmax, center, model, material, color="BLUEx",
        nb_vertex=10,
    ):
        return {
            "kind": "granuloRoughWall", "l": l, "rmin": rmin, "rmax": rmax,
            "center": center, "model": model, "material": material,
            "color": color, "nb_vertex": nb_vertex,
        }


def test_fine_wall_factory_uses_supported_parameters(monkeypatch):
    monkeypatch.setattr("lmgc90_engine.avatar_factory._pre", _WallPre)
    avatar = pre.fineWall(
        l=2.0, r=0.04, nb_vertex=16, center=[0.0, 0.0],
        model="rigid", material="WALL",
    )

    body = build_avatar(
        avatar, materials={"WALL": object()}, models={"rigid": object()},
    )

    assert body["kind"] == "fineWall"
    assert (body["l"], body["r"], body["nb_vertex"]) == (2.0, 0.04, 16)


def test_granulo_rough_wall_factory_uses_supported_parameters(monkeypatch):
    monkeypatch.setattr("lmgc90_engine.avatar_factory._pre", _WallPre)
    avatar = pre.granuloRoughWall(
        l=2.0, rmin=0.01, rmax=0.03, nb_vertex=18, center=[0.0, 0.0],
        model="rigid", material="WALL",
    )

    body = build_avatar(
        avatar, materials={"WALL": object()}, models={"rigid": object()},
    )

    assert body["kind"] == "granuloRoughWall"
    assert (body["l"], body["rmin"], body["rmax"], body["nb_vertex"]) == (
        2.0, 0.01, 0.03, 18,
    )
