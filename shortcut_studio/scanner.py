from __future__ import annotations

import os
from pathlib import Path


def source_folders(source: Path) -> list[Path]:
    """Return immediate source children in a stable, Unicode-aware order."""
    try:
        folders = [entry for entry in source.iterdir() if entry.is_dir()]
    except OSError as exc:
        raise OSError(f"Could not read source folder: {exc}") from exc
    return sorted(folders, key=lambda path: path.name.casefold())


def find_executables(folder: Path) -> list[Path]:
    """Find real executables and Windows links whose visible name ends in .exe."""
    found: list[Path] = []
    try:
        for root, directories, files in os.walk(folder, followlinks=False):
            directories.sort(key=str.casefold)
            for name in sorted(files, key=str.casefold):
                lowered = name.casefold()
                is_executable = lowered.endswith(".exe")
                is_executable_link = lowered.endswith(".exe.lnk")
                if is_executable or is_executable_link:
                    found.append(Path(root) / name)
    except OSError as exc:
        raise OSError(f"Could not scan {folder.name}: {exc}") from exc
    return found
