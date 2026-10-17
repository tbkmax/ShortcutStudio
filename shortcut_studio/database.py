from __future__ import annotations

"""Backwards-compatible database module facade re-exporting from storage."""

from shortcut_studio.storage.database import Database
from shortcut_studio.storage.schema import DEFAULT_SETTINGS
from shortcut_studio.storage.connection import _now, _path_key, _pair_from_row

__all__ = [
    "Database",
    "DEFAULT_SETTINGS",
    "_now",
    "_path_key",
    "_pair_from_row",
]
