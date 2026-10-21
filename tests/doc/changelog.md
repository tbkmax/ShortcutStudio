# Test Suite Changelog

## [Unreleased]

### Added

#### 2026-10-21 - Composed UI Controller Behavior Coverage
- [test_ui_controllers.py](../test_ui_controllers.py) verifies saved launcher
  updates, failed-write preservation, confirmed/canceled deletion, choice routing,
  edit/workflow cancellation, backup round trips and malformed JSON handling.
- Real Qt event delivery verifies the new resize filter; a Browse click verifies
  the shared path-field factory updates the correct input.

#### 2026-10-21 - Startup and Dependency Boundary Coverage
- [test_bootstrap.py](../test_bootstrap.py) covers path policy, package/legacy
  launchers, exit codes, default startup arguments, database injection, and
  ambiguous constructor arguments.
- [test_architecture.py](../test_architecture.py) guards static lower-layer imports
  and verifies package import avoids loading Qt and storage.


#### 2026-10-20 - Controller Lifecycle Regression Coverage
- Added UI tests in [`test_core.py`](../test_core.py) for releasing a completed scan worker and checking two saved libraries in sequence.

#### 2026-10-20 - Test Documentation Directory
- Created the `tests/doc/` directory with architecture, workflow, changelog, and backlog files based on the repository documentation templates.

#### 2026-10-20 - Icon and Tray Regression Coverage
- Added tests in [`test_core.py`](../test_core.py) for seven ICO sizes, PyInstaller `_MEIPASS` icon lookup, tray icon recovery, and clean exit when no system tray is available.

### Changed

#### 2026-10-21 - Package Icon Test Path
- Updated [`test_core.py`](../test_core.py) to assert the PyInstaller icon location under `shortcut_studio/assets/`.

#### 2026-10-20 - Tray Controller Patch Target
- Tray availability tests now patch [`shortcut_studio.ui.tray`](../../shortcut_studio/ui/tray.py), which owns the system tray check after the controller extraction.

#### 2026-10-20 - Deterministic Tray Tests
- Tray hide and close tests in [`test_core.py`](../test_core.py) now patch the availability report so they pass on desktops and headless runners.

## Migration and Upgrade Notes

No operator action required.

No operator action required.
