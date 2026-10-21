"""Check the resources and DLLs inside a built Shortcut Studio executable."""

import sys

from PyInstaller.archive.readers import CArchiveReader


def main(executable: str) -> None:
    archive = CArchiveReader(executable)
    entries = {name.replace("/", "\\").lower() for name in archive.toc}
    if "shortcut_studio\\assets\\icon.ico" not in entries:
        raise SystemExit("Build is missing the runtime tray icon")
    if "icuuc.dll" in entries:
        raise SystemExit(
            "Build contains a PATH-sourced ICU DLL; "
            "remove the conflicting DLL from the bundle"
        )
    print("Verified bundled tray icon and clean Qt dependencies")


if __name__ == "__main__":
    main(sys.argv[1])
