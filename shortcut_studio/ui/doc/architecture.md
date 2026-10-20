# UI Subpackage Architecture: Shortcut Studio Presentation Layer

The `shortcut_studio.ui` package manages the visual presentation, window framing, navigation state machine, and desktop integration for Shortcut Studio. It is built entirely on PyQt6 and follows the design system specified in [`DESIGN.md`](../../doc/DESIGN.md).

---

## 1. Subsystem Boundaries and Responsibilities

- **Window Framing & Presentation Engine**: [`MainWindow`](../window.py) runs as a frameless, translucent window (`FramelessWindowHint`, `WA_TranslucentBackground`) with custom 12px rounded corner rendering on all 4 sides.
- **Top Chrome & Window Controls**: [`HeaderBar`](../components/header.py) provides custom window management controls (standard taskbar minimize, maximize/restore toggle, close), drag-to-move window interaction, double-click maximize toggle, and high-level page navigation.
- **System Tray Integration**: [`QSystemTrayIcon`](../window.py) maintains background desktop presence in the Windows notification area. The close button restores a missing tray icon and hides the window when the tray is available. If Windows has no tray, Close quits cleanly. A one-time balloon notification is shown on first hide. Left-click the tray icon to restore; right-click for "Open Shortcut Studio", "Hide to tool bar", or "Quit".
- **Application Icon**: [`icon.svg`](../../../assest/icon.svg) is the scalable source artwork. [`icon.ico`](../../../assest/icon.ico) contains 16, 24, 32, 48, 64, 128, and 256 pixel renderings for the EXE, window, and tray. [`_app_icon_path()`](../window.py) resolves the icon from source or PyInstaller's `_MEIPASS` extraction directory; [`Shortcut Studio.spec`](../../../Shortcut%20Studio.spec) bundles the ICO and [`scripts/build.ps1`](../../../scripts/build.ps1) verifies it in the EXE.
- **Page Navigation State Machine**: `QStackedWidget` hosts 10 specialized pages with centralized page routing orchestrated by `MainWindow`.
- **Theming & Design Contracts**: [`theme.py`](../theme.py) defines strict color tokens, typography scales, border radii, and dark QSS stylesheets matching [`DESIGN.md`](../../doc/DESIGN.md).

---

## 2. Component Inventory

| Component | Source Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| **Window Orchestrator** | [`window.py`](../window.py) | Frameless window host, system tray manager, edge resizer, worker thread synchronization. | `MainWindow`, `main()` |
| **Header Chrome** | [`components/header.py`](../components/header.py) | Custom header bar with dragging, double-click maximize, nav buttons, and custom window controls. | `HeaderBar`, `build_header()` |
| **Theme & Stylesheet** | [`theme.py`](../theme.py) | Dark color tokens, border radius scale, and unified QSS stylesheet. | `CANVAS`, `CARD`, `SURFACE_ELEVATED`, `STYLESHEET` |
| **Folder Row Widget** | [`components/folder_row.py`](../components/folder_row.py) | Item row rendering source folder, target shortcut, and status badge pill. | `FolderRow` |
| **Card Components** | [`components/cards.py`](../components/cards.py) | Metric cards, dashboard action cards, and edit item frames. | `build_dashboard_action()`, `build_pair_card()`, `build_edit_item_card()` |
| **Widget Factories** | [`components/widgets.py`](../components/widgets.py) | Typography builders, path inputs, buttons, and page container layouts. | `page_container()`, `title_label()`, `primary_button()` |
| **Page Modules** | [`pages/`](../pages/) | 10 modular application page views (Home, Setup, Check, Edit, List, Progress, Choice, etc.). | `build_home_page()`, `build_setup_page()`, etc. |

---

## 3. Frameless Window & Edge Resizing Architecture

The window operates without native OS chrome:
1. **Rounded Antialiased Corners**: Outer `QMainWindow` is transparent (`WA_TranslucentBackground`). Inner `#shell` container renders background `#0a0a0a` with a `1px solid #2c2f34` border and `12px` border radius (`rounded.lg`). Top `#header` and bottom `#pages` apply matching `12px` radii to prevent rectangular clipping.
2. **Dynamic Maximize State**: When maximized, `#shell`, `#header`, and `#pages` dynamic properties update to `maximized="true"`, resetting radii to `0px` and removing outer borders.
3. **Four-Border Edge Resizing**: An event filter on `#shell` tracks mouse movement within `RESIZE_MARGIN = 6px` of all borders and corners, updating cursor shapes (`SizeHorCursor`, `SizeVerCursor`, `SizeFDiagCursor`, `SizeBDiagCursor`) and recalculating window geometry on drag.
4. **Header Dragging**: Mouse press on [`HeaderBar`](../components/header.py) tracks `globalPosition() - window.pos()` and moves the window. Double-clicking header bar toggles maximize/restore.

---

## 4. System Tray Integration

- **Close button hides to tray when available**: `closeEvent` calls `_hide_to_tray()`. That method checks `QSystemTrayIcon.isSystemTrayAvailable()`, supplies a Qt standard icon if necessary, and re-shows a hidden tray icon before hiding the window. If Windows has no tray, the close event follows normal shutdown, including bounded worker cancellation. The tray menu's "Quit" also exits the process.
- **One-time balloon hint**: The first time the window hides to tray (tracked by `_tray_hint_shown`), a `showMessage()` balloon is displayed so the user knows to look in the system tray.
- `QApplication.setQuitOnLastWindowClosed(False)` ensures the Qt event loop continues running while hidden.
- **Left-Click (Activation)**: Invokes `_restore_from_tray()`, restoring the window, bringing it to the front, and activating focus.
- **Right-Click (Context Menu)**: Displays `QMenu` offering bold "Open Shortcut Studio", "Hide to tool bar" (toggle), and "Quit".
- **Minimize button** (`windowMinButton`): Calls `showMinimized()` — standard Windows taskbar minimize (unchanged).
- **Clean Shutdown**: `_quit_application()` sets `_is_quitting = True`, cancels any running worker (bounded `worker.wait(3000)`), hides the tray icon, and calls `QApplication.instance().quit()`.
