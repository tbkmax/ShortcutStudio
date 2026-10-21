# Workflow & Architectural Diagrams

This document details the object relationships, execution sequences, data entities, and state transitions of **Shortcut Studio** using Mermaid diagrams.

---

## 1. Class Hierarchy & Architecture Diagram

The class diagram below depicts the primary types and their ownership boundaries across the presentation, background execution, and persistence layers.

```mermaid
classDiagram
    direction TB
    class MainWindow {
        -Database database
        -WorkflowController workflow
        -TrayController tray
        -HeaderBar header_widget
        -QStackedWidget pages
        +_show_home()
        +_hide_to_tray() bool
        +_restore_from_tray()
        +_toggle_maximize()
        +_quit_application()
        +_launch_workflow(source, target, pair_id, check_only)
        +closeEvent(event)
    }

    class TrayController {
        +QSystemTrayIcon icon
        +hide_window() bool
        +restore_window()
        +show_first_hide_hint()
    }

    class WorkflowController {
        +ScanWorker worker
        +list check_queue
        +launch(source, target, pair_id, check_only)
        +cancel()
        +stop_for_shutdown() bool
    }

    class ScanWorker {
        -Path source
        -Path target
        -Database database
        -int pair_id
        -bool check_only
        -Condition _condition
        -bool _cancelled
        +choose(executable)
        +cancel()
        +run()
    }

    class Database {
        -Path path
        -ConnectionManager manager
        -PairRepository pair_repo
        -RunRepository run_repo
        -SettingsRepository settings_repo
        +get_or_create_pair(source, target)
        +list_pairs()
        +save_pair_item(pair_id, folder, exe, shortcut)
        +start_run(source, target)
        +save_result(run_id, result)
        +export_data()
        +import_data(payload)
    }

    class FolderPair {
        +int id
        +Path source
        +Path target
        +str created_at
        +str last_checked_at
    }

    class PairItem {
        +Path folder
        +Path executable
        +Path shortcut
        +str updated_at
    }

    class FolderResult {
        +Path folder
        +ResultStatus status
        +Path executable
        +Path shortcut
        +str error
    }

    MainWindow "1" o-- "1" Database : receives or creates for legacy callers
    MainWindow "1" *-- "1" TrayController : owns
    MainWindow "1" *-- "1" WorkflowController : owns
    WorkflowController "1" o-- "0..1" ScanWorker : runs
    MainWindow "1" *-- "many" FolderPair : navigates
    Database "1" ..> "many" FolderPair : persists
    Database "1" ..> "many" PairItem : persists
    Database "1" ..> "many" FolderResult : persists
    ScanWorker ..> Database : records progress
```

### Explanation
- [`MainWindow`](../ui/window.py) hosts the pages and Qt window events. [`WorkflowController`](../ui/workflow.py) manages the optional active [`ScanWorker`](../core/worker.py) thread; [`TrayController`](../ui/tray.py) owns the tray icon and hide/restore behavior. `_hide_to_tray()` delegates to the tray controller and returns false when Windows has no notification area; `closeEvent()` then quits.
- The worker executes asynchronously and reports progress via Qt signals without locking the GUI.
- Library editing, executable selection, settings/backups, and resize interaction
  are delegated to dedicated UI controllers; their state and call sequences are
  documented in the [UI workflow guide](../ui/doc/workflow_diagram.md).
- [`FolderPair`](../models.py), [`PairItem`](../models.py), and [`FolderResult`](../models.py) are immutable value dataclasses that flow between storage, execution, and presentation.

---

## 2. Scan & Synchronization Sequence Flow

The sequence diagram illustrates how a scanning run processes folder items, interacts with the Windows COM API, and resolves candidate disambiguation when multiple executables are present.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as MainWindow
    participant Flow as WorkflowController
    participant Worker as ScanWorker
    participant FS as File System
    participant COM as Windows Shell Link
    participant DB as SQLite Database

    User->>MW: Click "Scan folders" or "Check"
    MW->>Flow: start_from_fields() or launch()
    Flow->>DB: get_or_create_pair() or list_pairs()
    Flow->>Worker: start() [QThread]
    activate Worker

    Worker->>FS: source_folders(source)
    Worker->>DB: start_run(source, target)
    Worker-->>MW: folders_ready(list)

    loop For each folder in source
        Worker-->>MW: folder_started(folder)
        Worker->>FS: find_executables(folder)
        alt Multiple executables found
            Worker-->>MW: choice_required(folder, candidates)
            MW->>User: Display Choice Page (preview & test)
            User->>MW: Select preferred executable
            MW->>Worker: choose(selected_path)
        end
        Worker->>COM: install_launch_item(executable, destination)
        Worker->>DB: save_pair_item(pair_id, folder, exe, destination)
        Worker->>DB: save_result(run_id, FolderResult)
        Worker-->>MW: folder_finished(result)
    end

    Worker->>DB: complete_run(run_id)
    Worker->>DB: touch_pair(pair_id)
    Worker-->>Flow: workflow_finished(stats)
    deactivate Worker
    Flow->>MW: Display Done Page / summary
```

### Explanation
- Steps 1–5: The user triggers a run; the pair record is resolved, and the worker initiates directory discovery.
- Steps 8–12: When more than one executable candidate exists in a subfolder, [`ScanWorker`](../core/worker.py) suspends its thread via `Condition.wait_for()`, prompting the user via [`choice_page.py`](../ui/pages/choice_page.py). Upon user confirmation, `ScanWorker.choose()` wakes the worker.
- Steps 13–16: The shortcut is created via [`install_launch_item()`](../core/shell_link.py) and results are committed to [`Database`](../storage/database.py).
- Steps 17–20: Completion metrics are collected and summarized on [`done_page.py`](../ui/pages/done_page.py).

---

## 3. Entity-Relationship Diagram (ERD)

The persistence model is implemented in SQLite, adhering to normalized relational schemas with cascading deletions.

```mermaid
erDiagram
    FOLDER_PAIRS ||--o{ PAIR_ITEMS : "has"
    FOLDER_PAIRS {
        int id PK
        text source_folder
        text target_folder
        text source_key
        text target_key
        text created_at
        text last_checked_at
    }
    PAIR_ITEMS {
        int id PK
        int pair_id FK
        text folder_path
        text folder_key
        text executable_path
        text shortcut_path
        text updated_at
    }
    RUNS ||--o{ FOLDER_RESULTS : "records"
    RUNS {
        int id PK
        text source_folder
        text target_folder
        text started_at
        text completed_at
    }
    FOLDER_RESULTS {
        int id PK
        int run_id FK
        text folder_name
        text folder_path
        text executable_path
        text shortcut_path
        text status
        text error
        text created_at
    }
    SETTINGS {
        text key PK
        text value
    }
```

### Explanation
- `FOLDER_PAIRS` and `PAIR_ITEMS`: Durable records of configured library pairs and their chosen application launch configurations. Managed via [`PairRepository`](../storage/repository.py).
- `RUNS` and `FOLDER_RESULTS`: Audit trail logging every execution, duration, and per-folder status outcome. Managed via [`RunRepository`](../storage/repository.py).
- `SETTINGS`: Key-value application configuration store (e.g. `open_target_after_completion`, `confirm_pair_deletion`). Managed via [`SettingsRepository`](../storage/repository.py).
- Uniqueness is composite: `(source_key, target_key)` for folder pairs and
  `(pair_id, folder_key)` for pair items; individual key columns are not unique.

---

## 4. Folder Result Lifecycle State Machine

Each folder processed by the worker transitions through the following discrete status lifecycle:

```mermaid
stateDiagram-v2
    [*] --> Queued : Discovered in Source
    Queued --> Scanning : Worker starts folder
    Scanning --> UpToDate : Check mode & shortcut exists
    Scanning --> NeedsChoice : >1 Executables found
    Scanning --> Creating : Exactly 1 Executable found
    NeedsChoice --> Creating : User submits choice
    NeedsChoice --> Cancelled : User cancels choice
    Creating --> Created : Windows COM creates .lnk
    Creating --> Failed : I/O or COM error
    Scanning --> NoExecutable : 0 Executables found
    Scanning --> Removed : Source missing (Check mode)
    Created --> [*]
    UpToDate --> [*]
    Removed --> [*]
    NoExecutable --> [*]
    Failed --> [*]
    Cancelled --> [*]
```

### Explanation
- Discovered folders start as `Queued` and enter `Scanning` when picked up by the worker loop.
- If in check mode and the destination already points to the valid executable, it reaches `UpToDate`.
- Ambiguous targets branch to `NeedsChoice` until the user confirms or cancels.
- Terminal outcome labels correspond to [`ResultStatus`](../models.py) values.
  The diagram's queued/scanning/choice states are conceptual UI states, not enum
  members. Cancellation stops the worker loop; it does not persist a CANCELLED
  result for every unprocessed folder.

## 5. Application Assembly

```mermaid
sequenceDiagram
    participant Entry as __main__.py / GUI command / EXE
    participant Boot as bootstrap.main
    participant Paths as paths.py
    participant Qt as QApplication
    participant DB as Database
    participant Window as MainWindow
    Entry->>Boot: main()
    Boot->>Qt: configure application
    Boot->>Paths: app_icon_path(), default_database_path()
    Boot->>DB: Database(path)
    Boot->>Window: MainWindow(database=database)
    Window->>Window: build pages and controllers
    Boot->>Window: show()
    Boot->>Qt: exec()
    Qt-->>Entry: exit code through bootstrap
```

[`bootstrap.py`](../bootstrap.py) owns process startup. The window receives the
database and owns its UI controllers. Legacy UI entry points delegate to bootstrap.
