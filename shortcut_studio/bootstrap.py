"""Application composition root: assemble dependencies and run the Qt event loop."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication

from shortcut_studio.paths import app_icon_path, default_database_path
from shortcut_studio.storage.database import Database
from shortcut_studio.ui.theme import APP_NAME
from shortcut_studio.ui.window import MainWindow


def main(argv: Sequence[str] | None = None, *, database_path: Path | None = None) -> int:
    """Start one desktop process; callers embedding widgets should use MainWindow."""
    app = QApplication(list(sys.argv if argv is None else argv))
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    font = QFont("Segoe UI")
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    icon_path = app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    database = Database(database_path if database_path is not None else default_database_path())
    window = MainWindow(database=database)
    window.show()
    return app.exec()
