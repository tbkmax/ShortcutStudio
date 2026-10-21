# Build Script Architecture

The `scripts` folder owns the repeatable Windows EXE build entry point. [`build.ps1`](../build.ps1) invokes [`Shortcut Studio.spec`](../Shortcut%20Studio.spec) with the local virtual environment, then runs [`verify_build.py`](../verify_build.py) to inspect the resulting one-file archive.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Build command | [`build.ps1`](../build.ps1) | Selects the project environment, runs PyInstaller, and calls archive verification. | `.venv\Scripts\python.exe`, `PyInstaller` |
| Archive verification | [`verify_build.py`](../verify_build.py) | Confirms the runtime icon is present and the conflicting ICU DLL is absent. | `CArchiveReader`, `main` |
| Wheel verification | [`verify_wheel.py`](../verify_wheel.py) | Installs a local wheel in a disposable directory and starts its window/event loop outside the checkout. | `main`, `PROBE` |
| Build definition | [`Shortcut Studio.spec`](../Shortcut%20Studio.spec) | Declares application entrypoint, bundled ICO, windowed EXE, and Windows icon. | `Analysis`, `PYZ`, `EXE` |
| Runtime icon | [`icon.ico`](../../shortcut_studio/assets/icon.ico) | Supplies the EXE icon and the runtime window/tray icon. | `shortcut_studio/assets/icon.ico` archive entry |

## Ownership and Boundaries

`build.ps1` owns the build environment and invokes verification; `verify_build.py` owns the archive checks; the spec owns PyInstaller's file list and EXE settings. The PowerShell script temporarily limits `PATH` to the virtual environment and Windows directories so unrelated tools cannot supply conflicting DLLs. It restores the caller's `PATH` in `finally`. The script uses `.pyinstaller-build/` for intermediates and writes `dist/Shortcut Studio.exe`.

The spec uses `shortcut_studio/__main__.py` as its entry script and the repository
root as the package search path. There is no root `run.py` launcher.
`verify_wheel.py` accepts one local wheel path, installs it with `--no-index
--no-deps` into a temporary target, and probes it from a temporary cwd using
Python `-I`. It verifies the imported package origin, facade imports, GUI entry
point, packaged icon sizes, visible offscreen window, event loop, and temporary
database creation. It uses the invoking environment's PyQt6 dependency and does
not install into that environment. Both pip and the probe have bounded timeouts.

## Invariants and Safeguards

- Build only from the repository spec, so the runtime ICO remains included.
- The archive check requires `shortcut_studio/assets/icon.ico` and rejects a bundled `icuuc.dll`; Windows supplies the compatible ICU forwarder used by this Qt build.
- A failed PyInstaller process or archive check exits with an error instead of reporting success.
- Building changes only generated artifacts, not the user's SQLite database or game libraries.

## Verification

Run `.\scripts\build.ps1` from PowerShell, then launch `dist\Shortcut Studio.exe` and verify that the main window opens and Close hides it to the tray.

For wheel verification, run `.venv\Scripts\python.exe -m pip wheel --no-deps
--no-build-isolation . --wheel-dir dist`, then `.venv\Scripts\python.exe
scripts/verify_wheel.py dist/shortcut_studio-1.0.0-py3-none-any.whl`.
