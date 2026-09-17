"""Views package — import MainWindow only when Qt is available."""
from __future__ import annotations


def get_main_window_class():
    from .main_window import MainWindow
    return MainWindow
