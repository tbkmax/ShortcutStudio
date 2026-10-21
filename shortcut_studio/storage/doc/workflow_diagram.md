# Storage Workflows

## Class Relationships

```mermaid
classDiagram
    class Database {
        +Path path
        +ConnectionManager manager
        +PairRepository pair_repo
        +RunRepository run_repo
        +SettingsRepository settings_repo
        +export_data()
        +import_data(payload)
    }
    class ConnectionManager {
        +Path path
        +connect()
        +connection()
    }
    class PairRepository {
        +list_pairs(connection)
        +list_pair_items(connection, pair_id)
    }
    class RunRepository {
        +complete_run(connection, run_id)
    }
    class SettingsRepository {
        +get_all_settings(connection)
    }
    Database *-- ConnectionManager
    Database *-- PairRepository
    Database *-- RunRepository
    Database *-- SettingsRepository
```

The [Database facade](../database.py) owns repository objects. Connections are
short-lived resources managed by [ConnectionManager](../connection.py).

## Transaction Sequence

```mermaid
sequenceDiagram
    participant Caller
    participant DB as Database
    participant Manager as ConnectionManager
    participant Repo as PairRepository
    Caller->>DB: list_pairs()
    DB->>Manager: connection()
    Manager->>Manager: connect(), PRAGMA foreign_keys = ON
    DB->>Repo: list_pairs(connection)
    Repo-->>DB: list[FolderPair]
    alt Success
        Manager->>Manager: commit
    else Exception
        Manager->>Manager: rollback
    end
    Manager->>Manager: close
    DB-->>Caller: result or exception
```

The context manager scopes commit/rollback and closure. Other facade operations
follow the same pattern; schema initialization also uses this connection manager.
