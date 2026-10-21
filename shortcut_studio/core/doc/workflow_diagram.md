# Core Workflows

## Worker Types

```mermaid
classDiagram
    QThread <|-- ScanWorker
    class ScanWorker {
        +Path source
        +Path target
        +Database database
        -Condition _condition
        -Path _choice
        -bool _cancelled
        +run()
        +choose(executable)
        +cancel()
        -_choose_executable(folder)
    }
    class Database {
        +start_run(source, target)
        +save_result(run_id, result)
        +complete_run(run_id)
    }
    ScanWorker --> Database : records results
```

[ScanWorker](../worker.py) runs on a QThread and receives its database. Its
condition variable coordinates choice and cancellation without blocking Qt's UI.

## Executable Choice

```mermaid
sequenceDiagram
    participant Worker as ScanWorker
    participant UI as MainWindow
    Worker->>Worker: _choose_executable(folder)
    Worker-->>UI: choice_required(folder, candidates)
    Worker->>Worker: _condition.wait_for(...)
    alt User chooses
        UI->>Worker: choose(executable)
        Worker->>Worker: set _choice, notify_all()
    else User cancels
        UI->>Worker: cancel()
        Worker->>Worker: set _cancelled, notify_all()
    end
```

The condition's predicate checks choice or cancellation, so either user action
releases the wait. The remaining folder loop observes the cancellation flag.
