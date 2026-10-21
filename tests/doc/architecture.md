# Test Suite Architecture

The `tests` directory contains the `unittest` suite for scanning, shortcut handling, SQLite persistence, worker behavior, and the PyQt window. It exercises the public facades as well as UI behavior that depends on the tray icon.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Controller behavior | [`test_ui_controllers.py`](../test_ui_controllers.py) | Verify library edits/failures, deletion, choice routing, backups, resize gestures, and Browse callbacks. | `ControllerTests` |
| Startup and paths | [`test_bootstrap.py`](../test_bootstrap.py) | Verify path policy, launcher exit codes, compatibility and dependency assembly. | `PathTests`, `BootstrapTests`, `WindowDependencyTests` |
| Import boundaries | [`test_architecture.py`](../test_architecture.py) | Guard lower-layer dependency direction and lightweight package import. | `ArchitectureTests` |
| Scanner tests | [`test_core.py`](../test_core.py) | Verify folder discovery, Unicode paths, and executable-named links. | `ScannerTests` |
| Shortcut tests | [`test_core.py`](../test_core.py) | Verify shortcut naming and preservation of existing links. | `ShortcutNameTests` |
| Database tests | [`test_core.py`](../test_core.py) | Verify pairs, run history, migration, and JSON settings backup. | `DatabaseTests` |
| Worker tests | [`test_core.py`](../test_core.py) | Verify check cleanup stays inside a temporary target folder. | `WorkerTests` |
| Window tests | [`test_core.py`](../test_core.py) | Verify framing, controls, tray hide/restore, icon lookup, worker completion, and sequential batch checks. | `MainWindowTests` |

## Ownership and Boundaries

Each test creates its own temporary filesystem or database fixture. `MainWindowTests.setUpClass()` owns a `QApplication` instance for widget tests. Tray availability is patched through `shortcut_studio.ui.tray` in the hide/close tests so their result does not depend on the host notification area. Workflow tests pump Qt events until the worker completes, covering signal delivery and sequential batch execution. The packaged icon test checks source ICO sizes and the `_MEIPASS/shortcut_studio/assets` path rule; the PyInstaller build is checked separately.

`BootstrapTests` mocks Qt and assembly dependencies to verify arguments and return
values without nesting event loops. `WindowDependencyTests` uses a shared real Qt
application and temporary database to verify dependency sharing and argument
validation. `PathTests` restores cwd and environment patches. `ArchitectureTests`
inspects static imports (including relative imports) and probes package import in
a fresh process. It does not claim to detect arbitrary dynamic imports.
The separate installed-wheel smoke test is owned by
[`scripts/verify_wheel.py`](../../scripts/verify_wheel.py).

`ControllerTests` constructs real windows with temporary databases and source/link
fixtures. It uses executable-named `.lnk` files to exercise real copying without
launching programs or requiring COM shortcut creation. Dialogs and worker methods
are patched at their owning controller; storage reads and writes remain real.
The resize test sends QMouseEvents through QApplication to the shell, exercising
the installed event filter. Cleanup hides the tray and disposes the window before
removing its temporary files.

## Invariants and Safeguards

- UI tests run with `QT_QPA_PLATFORM=offscreen` when no desktop is available.
- Temporary databases and shortcut files are isolated from user data.
- Close-to-tray tests cover a usable tray, recovery from a hidden or missing icon, and clean exit when no tray exists.
- The test suite preserves public imports through `shortcut_studio.app`, `shortcut_studio.database`, `shortcut_studio.shortcuts`, and `shortcut_studio.worker`.

## Verification

Run `.venv\Scripts\python.exe -m unittest discover -s tests -v` from the repository root. On a headless runner, set `QT_QPA_PLATFORM=offscreen` first.
