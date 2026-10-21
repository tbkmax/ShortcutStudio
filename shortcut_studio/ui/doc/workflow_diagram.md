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
        +LibraryController library
        +SelectionController selection
        +SettingsController settings
        +FramelessController chrome
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
        +changeEvent(event)
        +closeEvent(event)
    }

    class HeaderBar {
        +MainWindow window
        +mousePressEvent(event)
        +mouseMoveEvent(event)
        +mouseReleaseEvent(event)
        +mouseDoubleClickEvent(event)
    }

    class FolderRow {
        +QLabel name_label
        +QLabel status_label
        +set_status(text, color)
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

    class LibraryController {
        +FolderPair current_pair
        +edit_pair(pair)
        +edit_item(pair_item)
        +save_choice(folder, chosen)
        +delete_pair(pair)
    }
    class SelectionController {
        +Path folder
        +list candidates
        +str context
        +show(raw_folder, raw_candidates, context)
        +submit()
        +cancel()
    }
    class SettingsController {
        +Database database
        +show()
        +apply()
        +export_data()
        +import_data()
    }
    class FramelessController {
        -int _resize_edge
        -QRect _drag_start_geom
        -QPoint _drag_start_pos
        +determine_edge(pos) int
        +eventFilter(obj, event) bool
        +change_event(event)
        +toggle_maximize()
    }

    MainWindow *-- HeaderBar : embeds as top bar
    MainWindow o-- Database : injected by bootstrap or legacy construction
    MainWindow *-- TrayController : owns
    MainWindow *-- WorkflowController : owns
    MainWindow *-- LibraryController : owns
    MainWindow *-- SelectionController : owns
    MainWindow *-- SettingsController : owns
    MainWindow *-- FramelessController : owns
    TrayController *-- QSystemTrayIcon : owns
    MainWindow ..> FolderRow : renders in progress & list pages
```

### Explanation
`MainWindow` hosts pages and Qt window events. `TrayController` owns the notification-area icon and determines whether the window can safely hide. `WorkflowController` owns worker lifetimes and batch state. Path resolution is implemented in `paths.app_icon_path()` and exposed through the legacy `_app_icon_path` alias; the normal minimize button uses `showMinimized()`. Bootstrap supplies the database in normal startup; both the window and workflow controller refer to that same instance.

LibraryController owns the edited pair; SelectionController owns candidate state;
SettingsController owns preference/backup actions; FramelessController owns resize
gestures. MainWindow keeps callback forwarding methods so page builders and worker
connections do not need to know every controller.

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

## 4. Edit Selection Sequence

```mermaid
sequenceDiagram
    participant UI as MainWindow callbacks
    participant Library as LibraryController
    participant Selection as SelectionController
    participant Link as shell_link
    participant DB as Database
    UI->>Library: edit_pair(pair), edit_item(pair_item)
    Library->>UI: _show_choice(folder, candidates, context="edit")
    UI->>Selection: show(folder, candidates, context)
    UI->>Selection: submit()
    Selection->>UI: _save_edited_choice(chosen)
    UI->>Library: save_choice(selection.folder, chosen)
    Library->>Link: install_launch_item(chosen, destination)
    alt Shortcut update succeeds
        Library->>DB: save_pair_item(...), touch_pair(...)
        Library->>Library: refresh_items()
        Library->>UI: display edit_detail_page
    else OSError
        Library->>UI: error dialog; retain choice page
    end
```

Only a successful shortcut write proceeds to updating the saved selection.
Workflow choices instead call `ScanWorker.choose()`; canceling an edit returns to
the detail page, while canceling a workflow delegates to WorkflowController.
