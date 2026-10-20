# UI Workflow & Architectural Diagrams

This document illustrates the visual hierarchy, window state transitions, and system tray interactions within the `shortcut_studio.ui` subpackage.

---

## 1. UI Class Diagram

The class diagram outlines the ownership boundaries between the window, custom framing chrome, tray controller, and workflow controller.

```mermaid
classDiagram
    class MainWindow {
        +Database database
        +WorkflowController workflow
        +TrayController tray
        +HeaderBar header_widget
        +QStackedWidget pages
        +QPushButton min_button
        +QPushButton max_button
        +QPushButton close_button
        +_setup_tray_icon()
        +_restore_from_tray()
        +_hide_to_tray() bool
        +_start_workflow()
        +_cancel_workflow()
        +_toggle_maximize()
        +_quit_application()
        +_determine_edge(pos) int
        +eventFilter(obj, event) bool
        +changeEvent(event)
        +closeEvent(event)
    }

    class HeaderBar {
        +MainWindow window
        +QLabel brand
        +QPushButton min_btn
        +QPushButton max_btn
        +QPushButton close_btn
        +mousePressEvent(event)
        +mouseMoveEvent(event)
        +mouseReleaseEvent(event)
        +mouseDoubleClickEvent(event)
    }

    class FolderRow {
        +Path folder_path
        +QLabel name_label
        +QLabel status_pill
        +update_status(status)
    }

    class QSystemTrayIcon {
        +setIcon(icon)
        +setContextMenu(menu)
        +show()
        +hide()
    }

    class TrayController {
        +QSystemTrayIcon icon
        +hide_window() bool
        +restore_window()
        +show_first_hide_hint()
        +hide_icon()
    }

    class WorkflowController {
        +ScanWorker worker
        +list check_queue
        +int batch_check_total
        +launch(source, target, pair_id, check_only)
        +cancel()
        +stop_for_shutdown() bool
    }

    MainWindow *-- HeaderBar : embeds as top bar
    MainWindow *-- TrayController : owns
    MainWindow *-- WorkflowController : owns
    TrayController *-- QSystemTrayIcon : owns
    MainWindow ..> FolderRow : renders in progress & list pages
```

### Explanation
`MainWindow` hosts pages and Qt window events. `TrayController` owns the notification-area icon and determines whether the window can safely hide. `WorkflowController` owns worker lifetimes and batch state. `_app_icon_path()` locates the bundled ICO for the window and tray; the normal minimize button uses `showMinimized()`.

---

## 2. Window Lifecycle & Tray State Diagram

```mermaid
stateDiagram-v2
    [*] --> NormalVisible : Application Launch

    NormalVisible --> HiddenInTray : Click Close Button (X), tray available
    Maximized --> HiddenInTray : Click Close Button (X), tray available
    HiddenInTray --> NormalVisible : Left-Click Tray Icon
    NormalVisible --> [*] : Click Close Button (X), tray unavailable
    Maximized --> [*] : Click Close Button (X), tray unavailable
    
    NormalVisible --> Maximized : Click Maximize Button (□) or Double-Click Header
    Maximized --> NormalVisible : Click Restore Button (❐) or Double-Click Header

    HiddenInTray --> [*] : Right-Click Tray -> Quit
    NormalVisible --> Minimized : Click Minimize Button (_)
    Maximized --> Minimized : Click Minimize Button (_)
    Minimized --> NormalVisible : Restore window
```

### Explanation
The window transitions between three primary presentation states:
1. **NormalVisible**: Frameless window with 12px rounded corners on all 4 sides.
2. **Maximized**: Borderless full-screen view with `border-radius: 0px`.
3. **Minimized**: Window remains present in the taskbar and Alt+Tab.
4. **HiddenInTray**: Hidden from screen and taskbar when the notification area exists; a hidden or missing tray icon is restored before hiding. With no tray, Close exits. The background loop is preserved via `QApplication.setQuitOnLastWindowClosed(False)`.

---

## 3. Close to Tray and Restore Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Header as HeaderBar
    participant Window as MainWindow
    participant Controller as TrayController
    participant Tray as QSystemTrayIcon
    participant Workflow as WorkflowController
    participant Menu as QMenu

    User->>Header: Click Close Button (X)
    Header->>Window: close()
    Window->>Controller: hide_window()
    Controller->>Tray: isSystemTrayAvailable()
    alt Tray available
        Controller->>Tray: Restore missing icon and show if hidden
        Controller->>Window: hide()
        Window->>Controller: show_first_hide_hint()
        Note over Window: Window hidden from screen & taskbar.<br/>App remains running in background.
    else Tray unavailable
        Window->>Workflow: stop_for_shutdown()
        Window->>Window: Accept close, app.quit()
    end

    alt User Left-Clicks Tray
        User->>Tray: Left-Click Tray Icon
        Tray->>Controller: activated (Trigger)
        Controller->>Window: showNormal(), raise_(), activateWindow()
        Note over Window: Window restored & focused
    else User Right-Clicks Tray
        User->>Tray: Right-Click Tray Icon
        Tray->>Menu: Show Context Menu
        User->>Menu: Click "Quit"
        Menu->>Window: _quit_application()
        Window->>Workflow: stop_for_shutdown()
        Window->>Controller: hide_icon()
        Window->>Window: app.quit()
    end
```

### Explanation
The close action checks for a usable tray icon before hiding. Once hidden, a left-click restores the window; the right-click menu can shut down cleanly.
