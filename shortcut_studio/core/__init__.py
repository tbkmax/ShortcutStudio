from __future__ import annotations

from shortcut_studio.core.shell_link import (
    create_shortcut,
    install_launch_item,
    safe_shortcut_name,
    shortcut_path,
)
from shortcut_studio.core.worker import ScanWorker

__all__ = [
    "ScanWorker",
    "create_shortcut",
    "install_launch_item",
    "safe_shortcut_name",
    "shortcut_path",
]
