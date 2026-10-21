from __future__ import annotations

"""Backwards-compatible app module facade re-exporting from the ui subpackage."""

from shortcut_studio.ui.components.folder_row import FolderRow
from shortcut_studio.ui.theme import (
    APP_NAME,
    BODY,
    CANVAS,
    CARD,
    GREEN,
    HAIRLINE,
    MUTED,
    ORANGE,
    RED,
    SOFT,
    STYLESHEET,
    SURFACE_ELEVATED,
    WHITE,
)
from shortcut_studio.bootstrap import main
from shortcut_studio.ui.window import MainWindow

__all__ = [
    "MainWindow",
    "main",
    "FolderRow",
    "APP_NAME",
    "CANVAS",
    "CARD",
    "SOFT",
    "HAIRLINE",
    "WHITE",
    "BODY",
    "MUTED",
    "GREEN",
    "ORANGE",
    "RED",
    "SURFACE_ELEVATED",
    "STYLESHEET",
]


if __name__ == "__main__":
    raise SystemExit(main())
