# Changelog: UI Subpackage

All notable changes to the `shortcut_studio.ui` module are documented in this file.

---

## [Unreleased]

### Added

#### 2026-10-19 - Module Documentation Directory
- Created UI subpackage documentation directory (`shortcut_studio/ui/doc/`) adhering to engineering templates.

#### 2026-10-19 - FIX-2 Window Behavior & Frameless Rounded Theme
- Converted [`MainWindow`](../window.py) to a frameless window using `Qt.WindowType.FramelessWindowHint` and translucent background `Qt.WidgetAttribute.WA_TranslucentBackground`.
- Applied antialiased 12px rounded corner styling across all 4 sides of the application shell adhering to [`DESIGN.md`](../../doc/DESIGN.md).
- Replaced OS title bar controls with custom header controls in [`HeaderBar`](../components/header.py):
  - Minimize button (`windowMinButton` / `—`) to hide window into the tool bar.
  - Resize / maximize toggle button (`windowMaxButton` / `□` and `❐`).
  - Close button (`windowCloseButton` / `✕`) with accent rose hover styling.
- Implemented system tray integration via [`QSystemTrayIcon`](../window.py) supporting:
  - Hiding window into tool bar / notification area on minimize.
  - Left-click activation to restore and focus the window.
  - Right-click context menu offering "Open Shortcut Studio" and "Quit".
- Added 4-border and corner mouse edge resizing via event filter on `#shell`.
- Added header dragging and double-click to maximize/restore on [`HeaderBar`](../components/header.py).
- Added dark QSS styles for `#shell`, `#pages`, `#header`, window controls, and right-click tray context menu in [`shortcut_studio.ui.theme`](../theme.py).

#### 2026-10-17 - UI Subpackage Modularization
- Split presentation layer into modular packages: `theme.py`, `window.py`, `components/`, and `pages/`.

---

## Migration and Upgrade Notes

No operator action required. All styling and window framing changes are applied at runtime.
