# UI Subpackage Architecture: Shortcut Studio Presentation Layer

The `shortcut_studio.ui` package manages the visual presentation, window framing, navigation state machine, and desktop integration for Shortcut Studio. It is built entirely on PyQt6 and follows the design system specified in [`DESIGN.md`](../../doc/DESIGN.md).

---

## 1. Subsystem Boundaries and Responsibilities

- **Window Framing & Presentation Engine**: [`MainWindow`](../window.py) runs as a frameless, translucent window (`FramelessWindowHint`, `WA_TranslucentBackground`) with custom 12px rounded corner rendering on all 4 sides.
- **Top Chrome & Window Controls**: [`HeaderBar`](../components/header.py) provides custom window management controls (standard taskbar minimize, maximize/restore toggle, close), drag-to-move window interaction, double-click maximize toggle, and high-level page navigation.
- **System Tray Integration**: [`TrayController`](../tray.py) owns the `QSystemTrayIcon`, its menu, and hide/restore behavior. `MainWindow.closeEvent()` asks it to hide the window when the tray is available. If Windows has no tray, Close quits cleanly. A one-time balloon notification is shown on first hide.
- **Workflow Coordination**: [`WorkflowController`](../workflow.py) owns the active `ScanWorker`, batch-check queue and totals, and worker cancellation. `MainWindow` retains progress rendering and the page widget tree.
- **Library Management**: [`LibraryController`](../library.py) owns the current edited pair, saved-library display, deletion confirmation, candidate discovery for edits, and shortcut updates with persistence.
- **Executable Selection**: [`SelectionController`](../selection.py) owns the choice folder, candidates, and workflow/edit context. It renders choices, forwards workflow choices to the worker, and delegates edited choices through the window to the library controller.
- **Settings and Backups**: [`SettingsController`](../settings.py) owns preference loading/saving and JSON import/export dialogs. Storage still owns backup serialization and transactions.
- **Frameless Interaction**: [`FramelessController`](../frameless.py) owns resize gesture state and the shell event filter. The window forwards state-change events for maximize styling.
- **Application Icon**: [`icon.svg`](../../assets/icon.svg) is the scalable source artwork. [`icon.ico`](../../assets/icon.ico) contains 16, 24, 32, 48, 64, 128, and 256 pixel renderings for the EXE, window, and tray. [`app_icon_path()`](../../paths.py) resolves source/wheel/frozen locations; `window._app_icon_path` remains a compatibility alias. The build spec bundles the same ICO.
- **Startup Boundary**: [`bootstrap.main()`](../../bootstrap.py) owns QApplication setup, dependency assembly, and the event loop. `MainWindow` accepts a keyword-only `database` instance, shares it with WorkflowController, and rejects simultaneous `database_path`. Legacy path-based construction still initializes a database using [paths.py](../../paths.py) for the default. `window.main()` and `ui.main()` are compatibility forwarding functions.
- **Page Navigation State Machine**: `QStackedWidget` hosts 10 specialized pages with centralized page routing orchestrated by `MainWindow`.
- **Theming & Design Contracts**: [`theme.py`](../theme.py) defines strict color tokens, typography scales, border radii, and dark QSS stylesheets matching [`DESIGN.md`](../../doc/DESIGN.md).

---

## 2. Component Inventory

| Component | Source Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| **Window Orchestrator** | [`window.py`](../window.py) | Compose controllers, host pages, route callbacks, render progress, coordinate shutdown. | `MainWindow(database_path=None, *, database=None)`, legacy `main()` |
| **Library Controller** | [`library.py`](../library.py) | Saved-library lists, dashboard, edit state, deletion and launcher updates. | `LibraryController`, `edit_pair()`, `edit_item()`, `save_choice()`, `delete_pair()` |
| **Selection Controller** | [`selection.py`](../selection.py) | Choice state, candidate rendering, submission, cancellation, executable testing. | `SelectionController`, `show()`, `submit()`, `cancel()` |
| **Settings Controller** | [`settings.py`](../settings.py) | Preferences and JSON backup dialogs. | `SettingsController`, `show()`, `apply()`, `export_data()`, `import_data()` |
| **Frameless Controller** | [`frameless.py`](../frameless.py) | Edge hit testing, resize gesture state, maximize button/style synchronization. | `FramelessController`, `eventFilter()`, `determine_edge()`, `change_event()` |
| **Tray Controller** | [`tray.py`](../tray.py) | Owns the notification-area icon, menu, hide/restore actions, and first-hide hint. | `TrayController`, `hide_window()`, `restore_window()` |
| **Workflow Controller** | [`workflow.py`](../workflow.py) | Owns scan worker lifetimes, batch-check queue, completion totals, and bounded shutdown wait. | `WorkflowController`, `launch()`, `cancel()`, `stop_for_shutdown()` |
| **Theme & Stylesheet** | [`theme.py`](../theme.py) | Dark color tokens, border radius scale, and unified QSS stylesheet. | `CANVAS`, `CARD`, `SURFACE_ELEVATED`, `STYLESHEET` |
| **Compatibility Exports** | [`__init__.py`](../__init__.py) | Preserve window, entry-point, widget, and theme imports. | `MainWindow`, legacy `main()` |

### Child Folder Guides

- [components/doc/architecture.md](../components/doc/architecture.md) owns the
  header, folder rows, cards, and widget factory inventory and contracts.
- [pages/doc/architecture.md](../pages/doc/architecture.md) owns the ten page
  builders and their window callback/attribute contracts.

Use those local guides for component/page implementation changes. This document
owns window coordination, workflow/tray boundaries, theme, and UI exports.

### Controller Ownership and Callback Contract

All controllers are QObjects parented to MainWindow and run on the GUI thread.
Library and settings receive the same Database facade as the workflow controller.
`library.current_pair` owns edit selection; `selection.folder`, `candidates`, and
`context` own executable-choice state; `chrome` owns drag edge and geometry.
These states no longer live on MainWindow.

The window keeps existing callback methods such as `_edit_pair_item()`,
`_submit_choice()`, and `_apply_settings()` as explicit forwarding methods, so page
builders and worker signal connections retain their contracts. Controllers access
the window's widget tree; they are UI controllers, not independent business
services. There are no mixins, dynamic method injection, or new UI inheritance
layers. Progress rows stay in the window because they are presentation state.

When changing behavior, use `library.py` for saved-library operations,
`selection.py` for choice routing, `settings.py` for preferences/backups, and
`frameless.py` for resize/maximize interaction. Change `window.py` for assembly,
navigation, progress presentation, or top-level lifecycle. The path input uses
the existing component factory rather than duplicating its widget construction.

---

## 3. Frameless Window & Edge Resizing Architecture

The window operates without native OS chrome:
1. **Rounded Antialiased Corners**: Outer `QMainWindow` is transparent (`WA_TranslucentBackground`). Inner `#shell` container renders background `#0a0a0a` with a `1px solid #2c2f34` border and `12px` border radius (`rounded.lg`). Top `#header` and bottom `#pages` apply matching `12px` radii to prevent rectangular clipping.
2. **Dynamic Maximize State**: When maximized, `#shell`, `#header`, and `#pages` dynamic properties update to `maximized="true"`, resetting radii to `0px` and removing outer borders.
3. **Four-Border Edge Resizing**: `FramelessController.eventFilter()` is installed on `#shell` and tracks mouse movement within `RESIZE_MARGIN = 6px` of all borders and corners, updating cursor shapes and recalculating window geometry on drag. Its gesture state is separate from the window's page state.
4. **Header Dragging**: Mouse press on [`HeaderBar`](../components/header.py) tracks `globalPosition() - window.pos()` and moves the window. Double-clicking header bar toggles maximize/restore.

---

## 4. System Tray Integration

- **Close button hides to tray when available**: `closeEvent` delegates to `TrayController.hide_window()`. The controller checks `QSystemTrayIcon.isSystemTrayAvailable()`, supplies a Qt standard icon if necessary, and re-shows a hidden tray icon before hiding the window. If Windows has no tray, the close event follows normal shutdown through `WorkflowController.stop_for_shutdown()`.
- **One-time balloon hint**: `TrayController.show_first_hide_hint()` displays a `showMessage()` balloon after the first successful hide.
- `QApplication.setQuitOnLastWindowClosed(False)` ensures the Qt event loop continues running while hidden.
- **Left-Click (Activation)**: Invokes `_restore_from_tray()`, restoring the window, bringing it to the front, and activating focus.
- **Right-Click (Context Menu)**: Displays `QMenu` offering bold "Open Shortcut Studio", "Hide to tool bar" (toggle), and "Quit".
- **Minimize button** (`windowMinButton`): Calls `showMinimized()` — standard Windows taskbar minimize (unchanged).
- **Clean Shutdown**: `_quit_application()` sets `_is_quitting = True`, calls `WorkflowController.stop_for_shutdown()` for bounded worker cancellation, hides the tray icon, and calls `QApplication.instance().quit()`.
