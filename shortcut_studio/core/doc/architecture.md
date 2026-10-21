# Core Execution Architecture

This package contains the Qt background worker and native Windows shortcut
adapter. It is an execution/platform layer, not a framework-free domain package.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Scan worker | [worker.py](../worker.py) | Discover folders, choose targets, synchronize shortcuts and persist results | `ScanWorker.run()`, `choose()`, `cancel()` |
| ShellLink adapter | [shell_link.py](../shell_link.py) | Sanitize names, copy existing links, create links through COM | `safe_shortcut_name()`, `shortcut_path()`, `install_launch_item()`, `create_shortcut()` |

## Ownership and Boundaries

`WorkflowController` in the UI owns worker lifetime; `ScanWorker` owns per-run
execution and its condition variable. The worker receives a `Database` facade;
storage owns SQLite connections and transactions. The worker reports via Qt
signals and does not import widgets, presentation modules, or bootstrap.
The ShellLink adapter owns COM interface acquisition and release.

## Runtime Flows

`run()` lists source folders, identifies stale saved items for check mode,
starts a run record, and processes folders. Multiple executable candidates cause
`choice_required` followed by a condition wait. `choose()` supplies the chosen
path; `cancel()` sets `_cancelled` and wakes the waiter. Results are recorded and
emitted; successful completion updates the run and pair timestamp.

## Invariants and Safeguards

Stale shortcut cleanup compares the saved path with the expected shortcut's
resolved path before unlinking. Name sanitation occurs in `shortcut_path()`.
Existing launch links are copied to preserve their embedded settings; real EXEs
use Windows COM. Cancellation is cooperative; UI shutdown waits at most 3000 ms
and refuses shutdown if the worker remains active. This migration leaves these
behaviors unchanged.

## Failure Handling and Verification

Setup and final-record errors emit `fatal_error`; per-folder failures become
`FolderResult` values. See [tests](../../../tests/test_core.py) for worker cleanup
and shortcut tests. Run `.venv\Scripts\python.exe -m unittest discover -s tests -v`.
