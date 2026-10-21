"""Filesystem locations shared by startup and presentation.

Resolving a path does not create directories or open the database.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def default_database_path() -> Path:
    """Keep the existing per-user Windows database location."""
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ShortcutStudio" / "shortcut_studio.db"


def app_icon_path() -> Path:
    """Locate the ICO in a source tree, installed wheel, or PyInstaller bundle."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    package_root = (
        Path(bundle_root) / "shortcut_studio"
        if bundle_root is not None
        else Path(__file__).resolve().parent
    )
    return package_root / "assets" / "icon.ico"
