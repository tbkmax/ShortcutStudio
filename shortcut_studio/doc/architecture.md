# Package Architecture: Shortcut Studio

Shortcut Studio is an offline Windows 10/11 desktop application using Python
3.11+, PyQt6, SQLite, and Windows ShellLink COM. The flat installable package keeps
application code under `shortcut_studio/`; there is no root Python launcher.
This guide describes this folder's modules and boundaries. Detailed architecture
belongs to each child folder's own `doc/`.

## Local Module Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Package exports | [__init__.py](../__init__.py) | Version and immutable model exports; no application construction | `__version__`, model types |
| Package launcher | [__main__.py](../__main__.py) | Invoke bootstrap for `python -m shortcut_studio` and PyInstaller | `main()` |
| Bootstrap | [bootstrap.py](../bootstrap.py) | Configure Qt, assemble dependencies, show window, run event loop | `main(argv=None, *, database_path=None)` |
| Path policy | [paths.py](../paths.py) | Resolve database and icon paths without writing files | `default_database_path()`, `app_icon_path()` |
| Models | [models.py](../models.py) | Immutable, slotted records and result enum | `FolderPair`, `PairItem`, `FolderResult`, `ResultStatus` |
| Scanner | [scanner.py](../scanner.py) | List immediate source folders and recursively find launch candidates | `source_folders()`, `find_executables()` |
| UI compatibility facade | [app.py](../app.py) | Preserve legacy window, entry point, widget, and theme imports | `MainWindow`, `main`, `FolderRow` |
| Storage compatibility facade | [database.py](../database.py) | Preserve persistence imports | `Database`, `DEFAULT_SETTINGS` |
| Shortcut compatibility facade | [shortcuts.py](../shortcuts.py) | Preserve native shortcut utility imports | `create_shortcut()`, `install_launch_item()`, `shortcut_path()`, `safe_shortcut_name()` |
| Worker compatibility facade | [worker.py](../worker.py) | Preserve worker import | `ScanWorker` |

## Child Package Boundaries

| Folder | Local Architecture | Owned Responsibility |
| :--- | :--- | :--- |
| `core/` | [Core architecture](../core/doc/architecture.md) | Qt background execution and Windows COM adapter |
| `storage/` | [Storage architecture](../storage/doc/architecture.md) | Connections, schema, repositories, JSON backup |
| `ui/` | [UI architecture](../ui/doc/architecture.md) | Window/page coordination, tray, workflow controller, theme |
| `assets/` | [icon.svg](../assets/icon.svg), [icon.ico](../assets/icon.ico) | Installed artwork and multi-resolution runtime icon; no Python code |

Use each child's inventory to locate its implementation; do not maintain a second
copy of its detailed architecture here.

## Ownership and Dependency Direction

Bootstrap owns QApplication configuration and the event loop. It constructs a
Database using the explicit or default path, passes it to
`MainWindow(database=database)`, shows the window, and returns Qt's exit code.
MainWindow owns its UI controllers; the workflow controller owns its active worker.
Library editing, executable choice, settings/backups, and frameless interaction
have dedicated state owners described in the [UI architecture](../ui/doc/architecture.md).
The window and controller share the injected database facade, while storage opens
and closes a separate connection for each operation.

Models, scanner, paths, and storage do not import Qt. Core is an execution layer
that uses QtCore and Windows COM, not a framework-free domain layer. Lower
layers must not import UI or bootstrap. Architecture tests guard those import
boundaries. The compatibility `ui.window.main()` wrapper imports bootstrap only
when called to avoid an import cycle.

## Local Runtime Flows

1. `python -m shortcut_studio`, the installed `shortcut-studio` GUI command, and
   the EXE converge on `bootstrap.main()`.
2. `default_database_path()` uses LOCALAPPDATA, or
   `Path.home()/AppData/Local` when missing or empty, then appends
   `ShortcutStudio/shortcut_studio.db`.
3. `app_icon_path()` resolves assets beside the installed/source module, or under
   `sys._MEIPASS/shortcut_studio/assets` in a PyInstaller bundle.
4. The window delegates scans to its workflow controller. The worker calls scanner
   functions and uses model values to report outcomes. See the child guides for
   worker sequencing, transactions, and UI transitions.

## Invariants and Compatibility

- Package import exports models/version without constructing Qt or opening a DB.
- Path lookup has no filesystem-write side effects and is independent of cwd.
- `source_folders()` returns immediate directories sorted case-insensitively.
  `find_executables()` searches for `.exe` and `.exe.lnk` candidates with
  `os.walk(..., followlinks=False)`.
- Public facade imports remain supported. Legacy
  `MainWindow(database_path=...)` construction remains supported; supplying both
  a database path and instance raises ValueError.
- Default user-data location, schema, shortcut processing, and cooperative worker
  cancellation are unchanged by the migration.
- Root `doc/` is reserved for user-facing documents. Engineering architecture is
  kept here and in the corresponding code folders. Plans link to these guides.

## Distribution and Verification

[pyproject.toml](../../pyproject.toml) declares the GUI entry point, explicit
Python packages, and icon package data. The
[PyInstaller spec](../../scripts/Shortcut%20Studio.spec) starts the package's
`__main__.py`. See [scripts architecture](../../scripts/doc/architecture.md)
for build and installed-wheel checks, and [test architecture](../../tests/doc/architecture.md)
for regression coverage. Reinstall the package or rebuild the EXE to distribute
changes; callers of the removed `run.py` should use `python -m shortcut_studio`.

The [review and migration plan](../../plan/ARCHITECTURE.md) records why the flat
layout was retained. Page builders still use window callbacks, which explicitly
delegate to the owning controllers; release automation remains a tracked improvement.
