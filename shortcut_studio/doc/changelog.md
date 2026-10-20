# Changelog

All notable changes to the Shortcut Studio codebase are documented in this file.

---

## [Unreleased]

### Added

#### 2026-10-20 - Scalable Game Launcher Icon
- Added vector source [`icon.svg`](../../assest/icon.svg) and replaced [`icon.ico`](../../assest/icon.ico) with seven sizes from 16 to 256 pixels, matching the game launcher direction in `About.txt`.
- [`Shortcut Studio.spec`](../../Shortcut%20Studio.spec) includes the ICO as runtime data for the app window and notification area. [`scripts/build.ps1`](../../scripts/build.ps1) is the supported build entry point and verifies the packaged resource.

#### 2026-10-19 - FIX-2 Window Behavior & Frameless Rounded Theme
- Transformed [`MainWindow`](../ui/window.py) into a frameless window (`FramelessWindowHint` with `WindowMinimizeButtonHint`, `WindowMaximizeButtonHint`, `WindowSystemMenuHint`) with translucent background (`WA_TranslucentBackground`) and smooth 12px rounded corner styling across all 4 sides adhering to [`DESIGN.md`](./DESIGN.md).
- Replaced native Windows titlebar controls with custom vector-rendered [`WindowControlButton`](../ui/components/header.py) elements (38x28px with consistent 10x10px stroke geometries) in [`HeaderBar`](../ui/components/header.py):
  - Minimize button (`windowMinButton`) performs standard window minimization (`showMinimized()`), keeping the application reachable in Alt + Tab and visible on the Windows taskbar.
  - Resize / maximize toggle button (`windowMaxButton`) toggles between maximize and restore with balanced vector square icons.
  - Close button (`windowCloseButton`) minimizes the window to the tool bar by default, keeping background processes active.
  - Added "Minimize to the tool bar when closing window" toggle checkbox to Settings page (backed by `minimize_to_tray_on_close` default `true`).
  - Right-click tray menu "Quit" explicitly terminates the application.
- Implemented system tray integration (`QSystemTrayIcon`) supporting left-click restoration and right-click context menu with "Open Shortcut Studio", "Hide to tool bar", and "Quit".
- Added frameless edge resizing (mouse tracking across 4 borders and corners) and header bar dragging / double-click maximize toggle.
- Added dark QSS styles for `#shell`, `#pages`, `#header`, window controls, and right-click tray context menu in [`shortcut_studio.ui.theme`](../ui/theme.py).

#### 2026-10-18 - Agent Operating Guidelines (AGENTS.md)
- Created root [`AGENTS.md`](../../AGENTS.md) defining standard operating procedures, documentation templates usage, mandatory per-folder `doc/` hierarchy, zero-guess target file navigation, and quality assurance checklists for AI agents.

#### 2026-10-17 - Package Documentation Directory
- Created package documentation directory (`shortcut_studio/doc/`) containing architectural specification, workflow diagrams, changelog, and backlog per engineering standards.

#### 2026-10-17 - Core Subpackage
- Extracted Windows COM ShellLink ctypes interface and path sanitization into [`shortcut_studio.core.shell_link`](../core/shell_link.py).
- Extracted background synchronization engine into [`shortcut_studio.core.worker`](../core/worker.py).
- Created [`shortcut_studio.core`](../core/__init__.py) namespace package.

#### 2026-10-17 - Storage Subpackage
- Modularized database operations into [`shortcut_studio.storage`](../storage/__init__.py).
- Created [`shortcut_studio.storage.connection`](../storage/connection.py) for SQLite connection management and path normalization.
- Created [`shortcut_studio.storage.schema`](../storage/schema.py) for DDL tables and legacy migrations.
- Created [`shortcut_studio.storage.repository`](../storage/repository.py) with dedicated `PairRepository`, `RunRepository`, and `SettingsRepository`.
- Created [`shortcut_studio.storage.backup`](../storage/backup.py) for JSON export and import handling.
- Created [`shortcut_studio.storage.database`](../storage/database.py) providing the unified Database facade.

#### 2026-10-17 - UI Subpackage
- Extracted dark QSS stylesheet and design constants into [`shortcut_studio.ui.theme`](../ui/theme.py).
- Modularized UI components into [`shortcut_studio.ui.components`](../ui/components/__init__.py) (`folder_row.py`, `header.py`, `cards.py`, `widgets.py`).
- Modularized application page views into 10 separate modules in [`shortcut_studio.ui.pages`](../ui/pages/__init__.py).
- Streamlined [`shortcut_studio.ui.window`](../ui/window.py) as an orchestrator for navigation and worker lifecycle.

### Changed

#### 2026-10-20 - UI Lifecycle Controllers
- Extracted [`TrayController`](../ui/tray.py) and [`WorkflowController`](../ui/workflow.py) from `MainWindow` to own notification-area behavior and scan worker lifetimes respectively. [`MainWindow`](../ui/window.py) remains the page host and Qt window-event handler.

#### 2026-10-17 - Architectural Refactoring & Backward-Compatibility Facades
- Refactored `shortcut_studio/database.py`, `shortcut_studio/shortcuts.py`, `shortcut_studio/worker.py`, and `shortcut_studio/app.py` to serve as backward-compatible facades re-exporting public symbols.
- Preserved 100% public API compatibility across all existing imports, PyInstaller specs, and unit tests.

### Fixed

#### 2026-10-20 - Build Verification Quoting
- [`scripts/build.ps1`](../../scripts/build.ps1) now runs [`scripts/verify_build.py`](../../scripts/verify_build.py) as a file so PowerShell preserves the archive check's Python syntax.

#### 2026-10-20 - Packaged Close-to-Tray Visibility
- [`MainWindow`](../ui/window.py) now locates the bundled icon in PyInstaller's extraction directory, repairs a missing or hidden tray icon, and quits cleanly when Windows has no notification area.
- [`tests/test_core.py`](../../tests/test_core.py) covers packaged icon resolution, multiple ICO sizes, and close behavior with and without a tray.

#### 2026-10-20 - Packaged QtCore Startup Failure
- The build previously copied an incompatible `icuuc.dll` from another tool on `PATH`; the packaged app failed before its main window opened. [`scripts/build.ps1`](../../scripts/build.ps1) now uses a controlled `PATH` and rejects EXEs that bundle that DLL.
- Removed `build.txt` and made the repository [`Shortcut Studio.spec`](../../Shortcut%20Studio.spec) the sole build definition.

---

## Migration and Upgrade Notes

Use a rebuilt EXE to receive the new icon and bundled tray resource. No database migration is required; existing configuration databases, exported JSON backups, and public module import paths remain compatible.
