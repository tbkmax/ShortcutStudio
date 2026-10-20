# Changelog: UI Subpackage

All notable changes to the `shortcut_studio.ui` module are documented in this file.

---

## [Unreleased]

### Fixed

#### 2026-10-20 - Reliable Packaged Tray Icon and Close Behavior
- [`window.py`](../window.py) now resolves the icon from PyInstaller's `_MEIPASS` directory when packaged, so the EXE's tray and window icons load from bundled runtime data.
- Follow-up fix: Close now re-shows a hidden tray icon and supplies a Qt fallback icon if the runtime icon is missing. If Windows reports no notification area, Close quits cleanly instead of doing nothing.
- Added regression coverage for both close paths and packaged icon lookup in [`tests/test_core.py`](../../../../tests/test_core.py).
- The supported [`scripts/build.ps1`](../../../scripts/build.ps1) build keeps an incompatible third-party ICU DLL out of the EXE, allowing the Qt UI to start.

#### 2026-10-19 - Close Button Always Hides to System Tray (Discord-Style)
- **Bug fix**: Clicking the close (✕) button now always hides the window to the system tray instead of depending on a user-controlled setting. Previously, if the `minimize_to_tray_on_close` database setting was `false` (e.g. from a legacy install), the app would fully quit, leaving no tray presence even though the process remained running.
- Removed the `minimize_to_tray_on_close` setting check from `closeEvent` in [`window.py`](../window.py). The behavior is now unconditional: close → hide to tray; only "Quit" from the right-click tray menu actually exits the process.
- Removed the "Minimize to the tool bar when closing window" checkbox from [`settings_page.py`](../pages/settings_page.py) since the behavior is no longer configurable.
- Removed corresponding `close_to_tray_setting` widget references from `_show_settings_page()` and `_apply_settings()` in [`window.py`](../window.py).
- Added a one-time balloon notification (`QSystemTrayIcon.showMessage`) on the first hide-to-tray so the user knows where to find the app (tracked via `_tray_hint_shown` instance flag).
- Updated `test_close_event_always_hides_to_tray` in [`tests/test_core.py`](../../../../tests/test_core.py) to reflect the new unconditional behavior.

### Added

#### 2026-10-20 - Scalable Application Icon
- Added [`icon.svg`](../../../assest/icon.svg) as the editable game launcher artwork and replaced [`icon.ico`](../../../assest/icon.ico) with seven rendered sizes for Windows.
- Updated [`Shortcut Studio.spec`](../../../Shortcut%20Studio.spec) to embed the ICO in the EXE and bundle it for Qt at runtime; [`scripts/build.ps1`](../../../scripts/build.ps1) verifies the archive.

#### 2026-10-19 - Module Documentation Directory
- Created UI subpackage documentation directory (`shortcut_studio/ui/doc/`) adhering to engineering templates.

#### 2026-10-19 - FIX-2 Window Behavior & Frameless Rounded Theme
- Converted [`MainWindow`](../window.py) to a frameless window using `Qt.WindowType.FramelessWindowHint` with `WindowMinimizeButtonHint`, `WindowMaximizeButtonHint`, `WindowSystemMenuHint`, and translucent background `Qt.WidgetAttribute.WA_TranslucentBackground`.
- Applied antialiased 12px rounded corner styling across all 4 sides of the application shell adhering to [`DESIGN.md`](../../doc/DESIGN.md).
- Replaced OS title bar controls with custom vector-drawn [`WindowControlButton`](../components/header.py) elements (38x28px with consistent 10x10px stroke geometries):
  - Minimize button (`windowMinButton`) performs standard window minimization (`showMinimized()`), keeping the application reachable in Alt + Tab and visible on the Windows taskbar.
  - Resize / maximize toggle button (`windowMaxButton`) toggles between maximize and restore with balanced vector square icons.
  - Close button (`windowCloseButton`) always hides the window to the system tray (Discord-style); the app never quits on close — only via "Quit" from the tray menu.
  - Right-click tray menu "Quit" explicitly terminates the application.
- Implemented system tray integration via [`QSystemTrayIcon`](../window.py) supporting:
  - Left-click activation to restore and focus the window.
  - Right-click context menu offering "Open Shortcut Studio", "Hide to tool bar", and "Quit".
- Added 4-border and corner mouse edge resizing via event filter on `#shell`.
- Added header dragging and double-click to maximize/restore on [`HeaderBar`](../components/header.py).
- Added dark QSS styles for `#shell`, `#pages`, `#header`, window controls, and right-click tray context menu in [`shortcut_studio.ui.theme`](../theme.py).

#### 2026-10-17 - UI Subpackage Modularization
- Split presentation layer into modular packages: `theme.py`, `window.py`, `components/`, and `pages/`.

---

## Migration and Upgrade Notes

Use a rebuilt EXE to receive the new icon and bundled tray resource. No database migration is required.
