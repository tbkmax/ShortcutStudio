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
        -ScanWorker worker
        -QSystemTrayIcon tray_icon
        -HeaderBar header_widget
        -QStackedWidget pages
        -list check_queue
        +show_home()
        +_hide_to_tray() bool
        +_restore_from_tray()
        +_toggle_maximize()
        +_quit_application()
        +_launch_workflow(source, target, pair_id, check_only)
        +closeEvent(event)
    }

    class ScanWorker {
        -Path source
        -Path target
        -Database database
        -int pair_id
        -bool check_only
        -Condition condition
        -bool cancelled
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

    MainWindow "1" *-- "1" Database : manages
    MainWindow "1" o-- "0..1" ScanWorker : runs
    MainWindow "1" *-- "many" FolderPair : navigates
    Database "1" ..> "many" FolderPair : persists
    Database "1" ..> "many" PairItem : persists
    Database "1" ..> "many" FolderResult : persists
    ScanWorker ..> Database : records progress
```

### Explanation
- [`MainWindow`](../ui/window.py) acts as the coordinator holding references to the [`Database`](../storage/database.py) facade and managing the optional active [`ScanWorker`](../core/worker.py) thread. `_hide_to_tray()` repairs a missing tray icon and returns false when Windows has no notification area; `closeEvent()` then quits.
- The worker executes asynchronously and reports progress via Qt signals without locking the GUI.
- [`FolderPair`](../models.py), [`PairItem`](../models.py), and [`FolderResult`](../models.py) are immutable value dataclasses that flow between storage, execution, and presentation.

---

## 2. Scan & Synchronization Sequence Flow

The sequence diagram illustrates how a scanning run processes folder items, interacts with the Windows COM API, and resolves candidate disambiguation when multiple executables are present.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as MainWindow
    participant Worker as ScanWorker
    participant FS as File System
    participant COM as Windows Shell Link
    participant DB as SQLite Database

    User->>MW: Click "Scan folders" or "Check"
    MW->>DB: get_or_create_pair(source, target)
    MW->>Worker: start() [QThread]
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
    Worker-->>MW: workflow_finished(stats)
    deactivate Worker
    MW->>User: Display Done Page / summary
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
        text source_key UK
        text target_key UK
        text created_at
        text last_checked_at
    }
    PAIR_ITEMS {
        int id PK
        int pair_id FK
        text folder_path
        text folder_key UK
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
- Terminal states (`Created`, `UpToDate`, `Removed`, `NoExecutable`, `Failed`, `Cancelled`) map directly to [`ResultStatus`](../models.py) enum values.
