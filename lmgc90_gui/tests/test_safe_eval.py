from lmgc90_gui.utils.safe_eval import safe_eval


def test_arithmetic():
    assert safe_eval("1 + 2 * 3") == 7
    assert safe_eval("sqrt(4)", {}) == 2.0
    assert abs(safe_eval("pi") - 3.1415) < 0.01


def test_context():
    assert safe_eval("n_bodies * 2", {"n_bodies": 5}) == 10


def test_rejects_import():
    import pytest
    with pytest.raises(Exception):
        safe_eval("__import__('os').system('echo x')")
