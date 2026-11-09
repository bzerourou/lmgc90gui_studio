import sys
from types import SimpleNamespace

import pytest

from lmgc90_engine import datbox
from lmgc90_engine.errors import DatboxError


def _scene():
    return SimpleNamespace(
        dimension=2,
        materials_container=object(),
        models_container=object(),
        tacts_container=object(),
        sees_container=object(),
        bodies_container=object(),
        posts_container=object(),
    )


def test_write_datbox_passes_path_when_supported(tmp_path, monkeypatch):
    calls = []

    def write_datbox(
        *, dim, mats, mods, tacts, sees, bodies, post, datbox_path,
    ):
        calls.append((
            dim, mats, mods, tacts, sees, bodies, post, datbox_path,
        ))

    monkeypatch.setitem(
        sys.modules,
        "pylmgc90",
        SimpleNamespace(pre=SimpleNamespace(writeDatbox=write_datbox)),
    )

    result = datbox.write_datbox(_scene(), tmp_path / "DATBOX")

    assert result == tmp_path / "DATBOX"
    assert len(calls) == 1
    assert calls[0][-1] == str(result)


def test_write_datbox_legacy_api_runs_in_subprocess_cwd(tmp_path, monkeypatch):
    run_calls = []

    def write_datbox(*args, **kwargs):
        return args, kwargs

    def run(*args, **kwargs):
        run_calls.append((args, kwargs))

    monkeypatch.setitem(
        sys.modules,
        "pylmgc90",
        SimpleNamespace(pre=SimpleNamespace(writeDatbox=write_datbox)),
    )
    monkeypatch.setattr(datbox.subprocess, "run", run)
    monkeypatch.setattr(datbox, "emit_pre", lambda _: "write datbox")
    project = object()

    result = datbox.write_datbox(_scene(), tmp_path / "DATBOX", project=project)

    assert result == tmp_path / "DATBOX"
    assert len(run_calls) == 1
    args, kwargs = run_calls[0]
    assert args[0][0:2] == [sys.executable, "-c"]
    assert args[0][-1] == "write datbox"
    assert kwargs["cwd"] == result
    assert kwargs["check"] is True


def test_write_datbox_does_not_retry_write_type_error(tmp_path, monkeypatch):
    calls = []

    def write_datbox(
        *, dim, mats, mods, tacts, sees, bodies, post, datbox_path,
    ):
        calls.append(datbox_path)
        raise TypeError("invalid container data")

    monkeypatch.setitem(
        sys.modules,
        "pylmgc90",
        SimpleNamespace(pre=SimpleNamespace(writeDatbox=write_datbox)),
    )
    monkeypatch.setattr(
        datbox.subprocess, "run",
        lambda *args, **kwargs: pytest.fail("unexpected retry"),
    )

    with pytest.raises(DatboxError, match="invalid container data"):
        datbox.write_datbox(_scene(), tmp_path / "DATBOX", project=object())

    assert len(calls) == 1
