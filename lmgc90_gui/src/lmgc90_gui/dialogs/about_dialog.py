"""About / shortcuts dialog."""
from __future__ import annotations


def create_about_dialog(parent=None):
    from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextEdit, QVBoxLayout

    try:
        from lmgc90_core import __version__ as core_v
    except Exception:
        core_v = "?"
    try:
        from lmgc90_gui import __version__ as gui_v
    except Exception:
        gui_v = "?"

    class AboutDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("About LMGC90_GUI v0.5.8")
            self.resize(520, 420)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(f"<b>LMGC90_GUI v0.5.8</b>  gui={gui_v}  core={core_v}"))
            text = QTextEdit()
            text.setReadOnly(True)
            text.setHtml("""
<h3>Architecture</h3>
<ul>
<li><b>lmgc90_core</b> — pure scene (Project, pre, SoA populations)</li>
<li><b>lmgc90_engine</b> — pylmgc90 bridge (EngineSession)</li>
<li><b>lmgc90_gui</b> — Qt client of core + engine</li>
</ul>
<h3>Shortcuts</h3>
<table>
<tr><td>Ctrl+N</td><td>New project</td></tr>
<tr><td>Ctrl+O</td><td>Open</td></tr>
<tr><td>Ctrl+S</td><td>Save</td></tr>
<tr><td>Ctrl+Z / Ctrl+Y</td><td>Undo / Redo</td></tr>
<tr><td>F5</td><td>Run computation</td></tr>
<tr><td>Ctrl+F5</td><td>Generate DATBOX / scripts</td></tr>
<tr><td>F6</td><td>Refresh viewer</td></tr>
<tr><td>F7</td><td>Application journal</td></tr>
<tr><td>Ctrl+,</td><td>Preferences</td></tr>
</table>
<h3>Crédit : Bachir Zerourou</h3>
<p>© 2026 - Open Source"</p>
""")
            layout.addWidget(text)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            buttons.accepted.connect(self.accept)
            layout.addWidget(buttons)

    return AboutDialog(parent)
