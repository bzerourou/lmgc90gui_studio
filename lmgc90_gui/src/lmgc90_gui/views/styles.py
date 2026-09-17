"""Application theme — soft colours, tab logos, expression hints in green."""
from __future__ import annotations

# Unicode “logos” for tabs / menus (no external icon assets required)
TAB_ICONS = {
    "Materials": "🧪",
    "Models": "📐",
    "Avatars": "🔵",
    "Loops": "🔁",
    "ForLoop": "🔢",
    "Granulo": "⚪",
    "Contact": "🤝",
    "Visibility": "👁️",
    "DOF": "📌",
    "Post-pro": "📊",
    "Viewer": "🎨",
    "Visualisation 3D": "🎨",
    "Groups": "📁",
    "Contactors": "🔗",
    "Deformable": "🧩",
    "Masonry": "🧱",
}

MENU_ICONS = {
    "file": "📄",
    "edit": "✏️",
    "view": "👁️",
    "project": "🗂️",
    "computation": "⚙️",
    "tools": "🛠️",
    "help": "❓",
    "new": "🆕",
    "open": "📂",
    "save": "💾",
    "export": "📤",
    "run": "▶️",
    "datbox": "📦",
    "journal": "📋",
    "prefs": "⚙️",
    "pipeline": "🚀",
    "mesh": "🔷",
    "masonry": "🧱",
    "dynvars": "𝑥",
    "undo": "↩️",
    "redo": "↪️",
    "about": "ℹ️",
    "refresh": "🔄",
}

APP_STYLESHEET = """
/* --- global --- */
QMainWindow, QDialog {
    background-color: #f4f6f9;
    color: #1a1a2e;
    font-size: 13px;
}
QMenuBar {
    background-color: #1f2a44;
    color: #eef2ff;
    padding: 4px;
    font-weight: 600;
}
QMenuBar::item:selected {
    background-color: #3d5a80;
    border-radius: 4px;
}
QMenu {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #c5d0e0;
}
QMenu::item:selected {
    background-color: #dbe7ff;
    color: #0b1c3d;
}
QToolBar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #2b3a55, stop:1 #1f2a44);
    spacing: 6px;
    padding: 4px;
    border: none;
}
QToolBar QToolButton {
    color: #eef2ff;
    background: transparent;
    padding: 6px 10px;
    border-radius: 6px;
    font-weight: 600;
}
QToolBar QToolButton:hover {
    background-color: #3d5a80;
}
QStatusBar {
    background-color: #1f2a44;
    color: #c8d6f0;
    font-size: 12px;
}
QTabWidget::pane {
    border: 1px solid #c5d0e0;
    border-radius: 6px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #e8eef8;
    color: #1f2a44;
    padding: 8px 14px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #0b3d91;
    border-bottom: 3px solid #3d7cff;
}
QTabBar::tab:hover:!selected {
    background: #d5e3ff;
}
QDockWidget {
    titlebar-close-icon: none;
    color: #1f2a44;
    font-weight: 600;
}
QDockWidget::title {
    background: #3d5a80;
    color: white;
    padding: 6px;
    border-radius: 4px;
}
QGroupBox {
    font-weight: 600;
    border: 1px solid #c5d0e0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    background: #fafbfd;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #2b4c7e;
}
QPushButton {
    background-color: #3d7cff;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2f6ae0;
}
QPushButton:pressed {
    background-color: #1f4fb8;
}
QPushButton:disabled {
    background-color: #b0b8c8;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #c5d0e0;
    border-radius: 5px;
    padding: 4px 6px;
    selection-background-color: #3d7cff;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #3d7cff;
}
/* expression-capable fields */
QLineEdit[exprField="true"] {
    border: 1px solid #2e9e6a;
    background: #f3fff8;
    color: #0d5c3a;
}
QListWidget, QTreeWidget, QTableWidget {
    background: #ffffff;
    border: 1px solid #c5d0e0;
    border-radius: 6px;
    alternate-background-color: #f0f5ff;
}
QHeaderView::section {
    background: #3d5a80;
    color: white;
    padding: 5px;
    border: none;
}
QLabel#exprHint {
    color: #1b7a4a;
    background-color: #e8f8ef;
    border: 1px solid #a8dfc0;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 11px;
}
QLabel#banner {
    color: #1f2a44;
    background: #e8eef8;
    border-radius: 8px;
    padding: 10px;
}
"""

EXPR_HINT_HTML = (
    "<span style='color:#1b7a4a'><b>Expressions dynamiques</b> — "
    "nombres, <code>thickness</code>, <code>avatar[0].x</code>, "
    "<code>group['mur'][0].y</code>, <code>material['STEEL'].density</code>, "
    "<code>2*pi*r</code> · <b>Ctrl+V</b> pour le gestionnaire</span>"
)


def tab_title(name: str) -> str:
    icon = TAB_ICONS.get(name, "•")
    return f"{icon}  {name}"


def apply_app_style(window) -> None:
    window.setStyleSheet(APP_STYLESHEET)
