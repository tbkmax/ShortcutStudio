# Test Suite Changelog

## [Unreleased]

### Added

#### 2026-10-20 - Controller Lifecycle Regression Coverage
- Added UI tests in [`test_core.py`](../test_core.py) for releasing a completed scan worker and checking two saved libraries in sequence.

#### 2026-10-20 - Test Documentation Directory
- Created the `tests/doc/` directory with architecture, workflow, changelog, and backlog files based on the repository documentation templates.

#### 2026-10-20 - Icon and Tray Regression Coverage
- Added tests in [`test_core.py`](../test_core.py) for seven ICO sizes, PyInstaller `_MEIPASS` icon lookup, tray icon recovery, and clean exit when no system tray is available.

### Changed

#### 2026-10-20 - Tray Controller Patch Target
- Tray availability tests now patch [`shortcut_studio.ui.tray`](../../shortcut_studio/ui/tray.py), which owns the system tray check after the controller extraction.

#### 2026-10-20 - Deterministic Tray Tests
- Tray hide and close tests in [`test_core.py`](../test_core.py) now patch the availability report so they pass on desktops and headless runners.

## Migration and Upgrade Notes

No operator action required.
