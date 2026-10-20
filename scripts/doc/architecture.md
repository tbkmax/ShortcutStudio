# Build Script Architecture

The `scripts` folder owns the repeatable Windows EXE build entry point. [`build.ps1`](../build.ps1) invokes the repository [`Shortcut Studio.spec`](../../Shortcut%20Studio.spec) with the local virtual environment and verifies the resulting one-file archive.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Build command | [`build.ps1`](../build.ps1) | Selects the project environment, runs PyInstaller, and checks the archive. | `.venv\Scripts\python.exe`, `PyInstaller`, `CArchiveReader` |
| Build definition | [`Shortcut Studio.spec`](../../Shortcut%20Studio.spec) | Declares application entrypoint, bundled ICO, windowed EXE, and Windows icon. | `Analysis`, `PYZ`, `EXE` |
| Runtime icon | [`icon.ico`](../../assest/icon.ico) | Supplies the EXE icon and the runtime window/tray icon. | `assest/icon.ico` archive entry |

## Ownership and Boundaries

`build.ps1` owns the build environment and verification; the spec owns PyInstaller's file list and EXE settings. The script temporarily limits `PATH` to the virtual environment and Windows directories so unrelated tools cannot supply conflicting DLLs. It restores the caller's `PATH` in `finally`. The script uses `.pyinstaller-build/` for intermediates and writes `dist/Shortcut Studio.exe`.

## Invariants and Safeguards

- Build only from the repository spec, so the runtime ICO remains included.
- The archive check requires `assest/icon.ico` and rejects a bundled `icuuc.dll`; Windows supplies the compatible ICU forwarder used by this Qt build.
- A failed PyInstaller process or archive check exits with an error instead of reporting success.
- Building changes only generated artifacts, not the user's SQLite database or game libraries.

## Verification

Run `.\scripts\build.ps1` from PowerShell, then launch `dist\Shortcut Studio.exe` and verify that the main window opens and Close hides it to the tray.
