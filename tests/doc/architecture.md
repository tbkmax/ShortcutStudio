# Test Suite Architecture

The `tests` directory contains the `unittest` suite for scanning, shortcut handling, SQLite persistence, worker behavior, and the PyQt window. It exercises the public facades as well as UI behavior that depends on the tray icon.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Scanner tests | [`test_core.py`](../test_core.py) | Verify folder discovery, Unicode paths, and executable-named links. | `ScannerTests` |
| Shortcut tests | [`test_core.py`](../test_core.py) | Verify shortcut naming and preservation of existing links. | `ShortcutNameTests` |
| Database tests | [`test_core.py`](../test_core.py) | Verify pairs, run history, migration, and JSON settings backup. | `DatabaseTests` |
| Worker tests | [`test_core.py`](../test_core.py) | Verify check cleanup stays inside a temporary target folder. | `WorkerTests` |
| Window tests | [`test_core.py`](../test_core.py) | Verify framing, controls, tray hide/restore, and icon lookup. | `MainWindowTests` |

## Ownership and Boundaries

Each test creates its own temporary filesystem or database fixture. `MainWindowTests.setUpClass()` owns a `QApplication` instance for widget tests. Tray availability is patched in the hide/close tests so their result does not depend on the host notification area. The packaged icon test checks source ICO sizes and the `_MEIPASS` path rule; the PyInstaller build is checked separately.

## Invariants and Safeguards

- UI tests run with `QT_QPA_PLATFORM=offscreen` when no desktop is available.
- Temporary databases and shortcut files are isolated from user data.
- Close-to-tray tests cover a usable tray, recovery from a hidden or missing icon, and clean exit when no tray exists.
- The test suite preserves public imports through `shortcut_studio.app`, `shortcut_studio.database`, `shortcut_studio.shortcuts`, and `shortcut_studio.worker`.

## Verification

Run `.venv\Scripts\python.exe -m unittest discover -s tests -v` from the repository root. On a headless runner, set `QT_QPA_PLATFORM=offscreen` first.
