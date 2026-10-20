# Engineering Backlog: UI Subpackage

This backlog tracks prioritized improvements, enhancements, and technical debt specific to the `shortcut_studio.ui` presentation layer.

---

## High Priority

### - [x] Implement FIX-2 Custom Frameless Window & System Tray Integration
- **Completed**: 2026-10-19
- **Outcome**: Custom frameless window with 12px rounded corners on 4 sides, custom window buttons (minimize, resize, close), and system tray integration with left click restore and right click quit.

---

## Medium Priority

### - [ ] Windows 11 Snap Layouts Native Hit Testing
- **Problem or opportunity**: Windows 11 displays a hover layout menu over native maximize buttons (`WM_NCHITTEST` `HTMAXBUTTON`). With the frameless custom maximize button, native OS snap flyouts are not automatically triggered by hover.
- **Desired outcome**: When hovering over `windowMaxButton` on Windows 11, the native Snap Layouts menu appears, allowing quick desktop tiling.
- **Scope**: `shortcut_studio/ui/window.py` (Windows `nativeEvent` filtering with `ctypes.wintypes.MSG`).
- **Acceptance criteria**:
  1. On Windows 11, hovering over `max_button` returns `HTMAXBUTTON` in `WM_NCHITTEST`.
  2. Clicking or selecting a tile snaps the window accordingly.
  3. Headless tests on non-Windows/CI run without error.
- **Dependencies and risks**: Requires platform-specific Windows message handling; must fallback gracefully on older OS or CI environments.
- **Verification**: Manual hover test on Windows 11 desktop.
- **Priority**: Medium (Impact: Improved native OS feel on Windows 11).

---

## Low Priority

### - [ ] Animated Tray Icon Indicator During Batch Scanning
- **Problem or opportunity**: When the window is hidden in the tool bar during an active batch scan or check, the user has no direct visual feedback of sync progress from the tray icon.
- **Desired outcome**: The system tray icon alternates or pulses subtly while `ScanWorker` is running in the background.
- **Scope**: `shortcut_studio/ui/window.py`.
- **Acceptance criteria**:
  1. Tray icon tooltip updates with current progress percentage when hidden.
  2. Tray icon reverts to standard icon when the worker completes.
- **Dependencies and risks**: Minimal; UI timer only.
- **Verification**: Run a multi-pair check, minimize to tray, verify tooltip.
- **Priority**: Low (Nice-to-have visual enhancement).
