"""Post-processing avatar targets resolve to materialized rigid bodies."""
from __future__ import annotations

from types import SimpleNamespace

from lmgc90_core import PostProCommand, Project, pre
from lmgc90_engine import materialize as materialize_module


class _Container(list):
    def addMaterial(self, item):
        self.append(item)

    def addModel(self, item):
        self.append(item)

    def addAvatar(self, item):
        self.append(item)

    def addBehav(self, item):
        self.append(item)

    def addSeeTable(self, item):
        self.append(item)

    def addCommand(self, item):
        self.append(item)


class _Pre:
    material = staticmethod(lambda **kwargs: kwargs)
    model = staticmethod(lambda **kwargs: kwargs)
    postpro_command = staticmethod(lambda **kwargs: kwargs)

    @staticmethod
    def materials():
        return _Container()

    @staticmethod
    def models():
        return _Container()

    @staticmethod
    def avatars():
        return _Container()

    @staticmethod
    def tact_behavs():
        return _Container()

    @staticmethod
    def see_tables():
        return _Container()

    @staticmethod
    def postpro_commands():
        return _Container()


def test_materialize_resolves_avatar_target_to_rigid_set(monkeypatch):
    project = Project(name="postpro-avatar", dimension=2)
    project.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    project.add(pre.model(
        name="rigid", physics="MECAx", element="Rxx2D", dimension=2,
    ))
    avatar = project.add(pre.rigidDisk(
        r=0.1, center=[0.0, 0.0], model="rigid", material="STEEL",
    ))
    project.add(PostProCommand(
        name="BODY TRACKING", target_type="avatar", target_value=avatar.avatar_id,
    ))
    body = object()
    monkeypatch.setattr(materialize_module, "_pre", lambda: _Pre())
    monkeypatch.setattr(materialize_module, "_make_material", lambda _pre, _mat: object())
    monkeypatch.setattr(materialize_module, "_make_model", lambda _pre, _model: object())
    monkeypatch.setattr(materialize_module, "build_avatar", lambda *_args, **_kwargs: body)

    scene = materialize_module.materialize_project(project)

    assert scene.posts_container == [{"name": "BODY TRACKING", "step": 1, "rigid_set": [body]}]


def test_materialize_rejects_unknown_postpro_avatar_target(monkeypatch):
    project = Project(name="postpro-avatar-missing", dimension=2)
    project.add(PostProCommand(
        name="BODY TRACKING", target_type="avatar", target_value="missing-avatar",
    ))
    monkeypatch.setattr(materialize_module, "_pre", lambda: _Pre())

    try:
        materialize_module.materialize_project(project)
    except materialize_module.MaterializationError as exc:
        assert "missing-avatar" in str(exc)
    else:
        raise AssertionError("missing avatar target should fail materialization")
