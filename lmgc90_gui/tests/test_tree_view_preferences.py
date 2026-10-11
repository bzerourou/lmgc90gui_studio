from types import SimpleNamespace

from lmgc90_core import AvatarOrigin, AvatarType
from lmgc90_gui.utils.preferences import Preferences
from lmgc90_gui.views.tree_view import _avatar_rows


def _avatar(avatar_id: str, origin: AvatarOrigin = AvatarOrigin.MANUAL):
    return SimpleNamespace(
        avatar_id=avatar_id,
        avatar_type=AvatarType.RIGID_DISK,
        center=[0.0, 0.0],
        origin=origin,
    )


def test_avatar_rows_respect_visibility_granulo_and_limit():
    avatars = [
        _avatar("manual-1"),
        _avatar("granulo-1", AvatarOrigin.GRANULO),
        _avatar("manual-2"),
    ]
    prefs = Preferences(max_tree_avatars=1)

    rows, count = _avatar_rows(avatars, prefs)

    assert count == "1/2"
    assert rows[0][0] == "manual-1…"
    assert rows[1] == ("…", "1 avatar masqué (limite soft)")
    assert _avatar_rows(avatars, Preferences(show_avatars_in_tree=False)) is None

    prefs.show_granulo_individually = True
    rows, count = _avatar_rows(avatars, prefs)
    assert count == "1/3"
