# Architecture Specification: Shortcut Studio

Shortcut Studio is a desktop application for Windows that organizes and automates the creation, verification, and maintenance of application shortcut libraries. Given a root source directory containing individual application folders, Shortcut Studio scans for launch targets (`.exe` or `.exe.lnk`), disambiguates multiple candidates interactively or via saved choices, and creates native Windows shortcuts in a designated target directory using the Windows COM ShellLink API.

---

## 1. System Overview & Boundaries

- **Target OS & Runtime**: Windows 10/11 (`nt`), Python 3.12+ (PyQt6 6.9+).
- **Execution Mode**: Local desktop client; operates entirely offline with no external network dependencies.
- **Persistence Boundary**: Local SQLite database stored by default at `%LOCALAPPDATA%\ShortcutStudio\shortcut_studio.db`.
- **System Integration**:
  - Windows Shell Link COM Interface (`IShellLinkW`, `IPersistFile`) invoked directly via `ctypes.windll.ole32`.
  - Windows file launching via `os.startfile`.
  - Native Windows file icons via `PyQt6.QtWidgets.QFileIconProvider`.
  - System tray integration via `PyQt6.QtWidgets.QSystemTrayIcon` supporting close-to-tray when available, left-click restoration, and right-click exit context menu.
  - Scalable icon source (`assest/icon.svg`) with a multi-resolution ICO bundled into the PyInstaller EXE and as runtime data for the window and tray.
  - [`scripts/build.ps1`](../../scripts/build.ps1) builds the EXE with a controlled Windows/virtual-environment `PATH` so third-party ICU DLLs do not replace the system ICU used by Qt.
  - Frameless custom window framing (`FramelessWindowHint`, `WA_TranslucentBackground`) with 12px rounded corners adhering to `DESIGN.md`.

---

## 2. Package Architecture & Component Organization

Shortcut Studio is organized into three specialized domain subpackages alongside root compatibility facades:

```
shortcut_studio/
├── __init__.py           # Package version and domain model exports
├── app.py                # Backward-compatible presentation facade
├── database.py           # Backward-compatible storage facade
├── models.py             # Shared dataclasses and enums
├── scanner.py            # Filesystem directory inspection utilities
├── shortcuts.py          # Backward-compatible COM shortcut creation facade
├── worker.py             # Backward-compatible concurrency facade
│
├── core/                 # Concurrency and OS platform integration
│   ├── __init__.py
│   ├── shell_link.py     # Native Windows COM ShellLink interface & path sanitization
│   └── worker.py         # Background ScanWorker (QThread) synchronization engine
│
├── storage/              # Persistence layer
│   ├── __init__.py
│   ├── connection.py     # SQLite connection provider and path canonicalization
│   ├── schema.py         # DDL table creation and migration scripts
│   ├── repository.py     # Repositories for pairs, items, runs, and settings
│   ├── backup.py         # JSON export and import services
│   └── database.py       # Unified Database facade wrapping repositories
│
├── ui/                   # Presentation and user interface
│   ├── __init__.py
│   ├── theme.py          # Color constants and dark QSS stylesheet
│   ├── window.py         # MainWindow orchestrator & main() entry point
│   ├── components/       # Reusable UI widgets and element factories
│   │   ├── __init__.py
│   │   ├── folder_row.py # FolderRow frame with status pill
│   │   ├── header.py     # Top navigation bar
│   │   ├── cards.py      # Action, pair, and item card renderers
│   │   └── widgets.py    # Common typography and input builders
│   └── pages/            # 10 modular application page builders
│       ├── __init__.py
│       ├── home_page.py
│       ├── setup_page.py
│       ├── check_page.py
│       ├── list_page.py
│       ├── edit_page.py
│       ├── edit_detail_page.py
│       ├── settings_page.py
│       ├── progress_page.py
│       ├── choice_page.py
│       └── done_page.py
│
└── doc/                  # Package-level documentation
    ├── architecture.md
    ├── workflow_diagram.md
    ├── changelog.md
    └── backlog.md
```

> [!NOTE]
> Each subpackage (`core/`, `storage/`, `ui/`) is designed to host its own focused documentation in future iterations. This document serves as the high-level system architectural blueprint.

---

## 3. Component Inventory & Responsibilities

| Subsystem | Primary Source Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| **Domain Models** | [`models.py`](../models.py) | Defines pure value types, status enums, and dataclasses. | `FolderPair`, `PairItem`, `FolderResult`, `ResultStatus` |
| **Scanner** | [`scanner.py`](../scanner.py) | Discovers folders and `.exe` / `.exe.lnk` files recursively. | `source_folders()`, `find_executables()` |
| **Platform COM** | [`core/shell_link.py`](../core/shell_link.py) | Interacts with Windows COM to create `.lnk` shortcuts and sanitizes filenames. | `install_launch_item()`, `create_shortcut()`, `safe_shortcut_name()` |
| **Worker Engine** | [`core/worker.py`](../core/worker.py) | Background `QThread` executing scanning, sync, and condition-variable pause. | `ScanWorker`, `choose()`, `cancel()` |
| **Storage Engine** | [`storage/database.py`](../storage/database.py) | Manages SQLite connection, schema DDL, repository operations, and JSON backups. | `Database`, `PairRepository`, `RunRepository`, `SettingsRepository` |
| **UI Presentation** | [`ui/window.py`](../ui/window.py) | Coordinates navigation across 10 pages, renders themes, and handles window lifecycle. | `MainWindow`, `main()` |
| **Application Icon** | [`../assest/icon.svg`](../../assest/icon.svg), [`../assest/icon.ico`](../../assest/icon.ico) | Source artwork and multi-resolution Windows icon used by the EXE, window, and tray. | `_app_icon_path()` in `ui/window.py` |
| **Windows Build** | [`../scripts/build.ps1`](../../scripts/build.ps1) | Builds and verifies the one-file EXE from the checked-in spec. | `PyInstaller`, `CArchiveReader` |

---

## 4. Runtime & Data Flows

1. **Setup & Scan Initiation**:
   - The user selects `source_folder` and `target_folder` on [`setup_page.py`](../ui/pages/setup_page.py).
   - [`MainWindow`](../ui/window.py) queries or registers the pair with [`Database.get_or_create_pair()`](../storage/database.py).
   - An asynchronous [`ScanWorker`](../core/worker.py) thread is spawned, moving the UI to the processing view.

2. **Folder Processing & Candidate Disambiguation**:
   - For each subfolder discovered by [`source_folders()`](../scanner.py), the worker invokes [`find_executables()`](../scanner.py).
   - If a single executable is found, it is automatically selected.
   - If multiple candidates are found and no saved choice exists, `ScanWorker` emits `choice_required` and pauses using `threading.Condition.wait_for()`.
   - The UI displays [`choice_page.py`](../ui/pages/choice_page.py). The user selects an option, and [`MainWindow._submit_choice()`](../ui/window.py) calls `ScanWorker.choose()`, which notifies the condition variable and resumes processing.

3. **Shortcut Creation & Recording**:
   - The worker invokes [`install_launch_item()`](../core/shell_link.py) to generate or copy the `.lnk` file into `target_folder`.
   - Persistence updates are executed: [`save_pair_item()`](../storage/repository.py) and [`save_result()`](../storage/repository.py).
   - The folder row status is emitted to update [`FolderRow`](../ui/components/folder_row.py) in real time.

4. **Maintenance ("Check") Workflow**:
   - Compares existing shortcuts against source directories.
   - Validates that previously configured launch items remain intact.
   - Identifies stale items whose source folders were deleted and cleans up shortcuts that strictly reside inside `target_folder`.

---

## 5. Invariants & Security Boundaries

1. **Target Confinement Safeguard**:
   - Before deleting any obsolete shortcut file during a check or sync, the application verifies `item.shortcut.resolve() == expected_shortcut.resolve()`. No files outside `target_folder` can ever be deleted.
2. **Path Normalization Invariant**:
   - Folder paths are indexed using `os.path.normcase(os.path.abspath(path))` (`_path_key`) to prevent duplicate records on case-insensitive Windows filesystems.
3. **Database Concurrency & Foreign Keys**:
   - Every SQLite connection explicitly enables `PRAGMA foreign_keys = ON` to enforce cascade deletion of runs, results, and pair items.
4. **Tray Visibility Safeguard**:
   - `MainWindow` restores a missing tray icon before hiding on close. If no system tray exists, Close quits cleanly instead of leaving an unresponsive window.
5. **Graceful Thread Shutdown**:
   - `MainWindow.closeEvent` invokes `worker.cancel()` and performs a bounded wait (`worker.wait(3000)`), preventing crashes or resource leaks upon closing during active processing.
