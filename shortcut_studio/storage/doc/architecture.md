# Storage Architecture

Storage persists library pairs, chosen launch items, scan history, and settings in
SQLite. It has no dependency on Qt, UI modules, or application startup.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Facade | [database.py](../database.py) | Initialize schema and expose transactional operations | `Database` |
| Connections | [connection.py](../connection.py) | Open, commit/rollback, and close connections; normalize paths | `ConnectionManager`, `_path_key()` |
| Schema | [schema.py](../schema.py) | Create tables, defaults, and import historical runs into pairs | `create_tables()`, `migrate_legacy_runs()` |
| Repositories | [repository.py](../repository.py) | Query and update pairs/items, runs/results, settings | `PairRepository`, `RunRepository`, `SettingsRepository` |
| Backups | [backup.py](../backup.py) | Validate and merge JSON payloads; serialize saved configuration | `export_data()`, `import_data()` |

## Ownership and Boundaries

`Database` owns its `ConnectionManager` and repositories. Each facade operation
opens a connection through a context manager; connections are not shared across
worker and UI threads. Repositories receive connections and execute SQL.
PairRepository owns pair/item queries, RunRepository owns run/result queries, and
SettingsRepository owns settings queries. Schema changes belong in schema.py.

## Data and Runtime Flows

The constructor creates the parent directory and initializes tables/defaults,
then migrates historical successful runs into newly inserted pairs. Library keys
are unique on `(source_key, target_key)`; item keys on `(pair_id, folder_key)`.
Backup format version 1 contains pairs, their items, and settings, not scan
history. Import upserts records inside the facade's transaction.

## Invariants and Safeguards

Every connection enables foreign keys. Transactions commit on success, roll back
on failure, and close in `finally`. Path keys use
`os.path.normcase(os.path.abspath(str(path)))`. Pair deletion cascades to items;
run deletion cascades to results. Stored paths are data, not permission to delete
files; the execution layer applies its cleanup guard.

## Operations and Verification

The caller supplies the database path. Default location policy belongs to
[paths.py](../../paths.py), not storage. No schema or data migration is introduced
by the startup refactor. Run `.venv\Scripts\python.exe -m unittest discover -s tests -v`
for CRUD, legacy migration, and export/import checks.
