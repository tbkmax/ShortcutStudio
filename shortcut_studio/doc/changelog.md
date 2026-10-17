# Changelog

All notable changes to the Shortcut Studio codebase are documented in this file.

---

## [Unreleased]

### Added

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

#### 2026-10-17 - Architectural Refactoring & Backward-Compatibility Facades
- Refactored `shortcut_studio/database.py`, `shortcut_studio/shortcuts.py`, `shortcut_studio/worker.py`, and `shortcut_studio/app.py` to serve as backward-compatible facades re-exporting public symbols.
- Preserved 100% public API compatibility across all existing imports, PyInstaller specs, and unit tests.

---

## Migration and Upgrade Notes

No operator or database migration actions are required. All existing configuration databases, exported JSON backups, and public module import paths remain fully compatible.
