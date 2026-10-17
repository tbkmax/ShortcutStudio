from __future__ import annotations

"""Backwards-compatible shortcuts facade re-exporting from core.shell_link."""

from shortcut_studio.core.shell_link import (
    _INVALID_FILENAME_CHARS,
    _RESERVED_NAMES,
    _GUID,
    _check_hresult,
    _create_shell_link,
    _guid,
    _method,
    _release,
    create_shortcut,
    install_launch_item,
    safe_shortcut_name,
    shortcut_path,
)

__all__ = [
    "_INVALID_FILENAME_CHARS",
    "_RESERVED_NAMES",
    "_GUID",
    "_check_hresult",
    "_create_shell_link",
    "_guid",
    "_method",
    "_release",
    "create_shortcut",
    "install_launch_item",
    "safe_shortcut_name",
    "shortcut_path",
]
