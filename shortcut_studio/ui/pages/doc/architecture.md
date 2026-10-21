# Page Architecture

Pages are functions that build Qt widget trees for a supplied MainWindow.
They currently share window attributes and callbacks; they are not independent
view-model objects.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Home | [home_page.py](../home_page.py) | New-library and check actions | `build_home_page()` |
| Setup | [setup_page.py](../setup_page.py) | Source/target inputs | `build_setup_page()` |
| Check | [check_page.py](../check_page.py) | Saved-library check selection | `build_check_page()` |
| List | [list_page.py](../list_page.py) | Saved library and run display containers | `build_list_page()` |
| Edit | [edit_page.py](../edit_page.py) | Library selection for editing | `build_edit_page()` |
| Edit detail | [edit_detail_page.py](../edit_detail_page.py) | Selected library item container | `build_edit_detail_page()` |
| Settings | [settings_page.py](../settings_page.py) | Preferences and import/export controls | `build_settings_page()` |
| Progress | [progress_page.py](../progress_page.py) | Worker progress widgets | `build_progress_page()` |
| Choice | [choice_page.py](../choice_page.py) | Executable candidates and confirmation | `build_choice_page()` |
| Done | [done_page.py](../done_page.py) | Completion summary and next actions | `build_done_page()` |

## Ownership and Boundaries

MainWindow builds all pages and owns the QStackedWidget navigation state. Builders
attach controls to the window so its handlers can refresh them. WorkflowController
owns worker/batch state. Pages connect signals; they do not start their own event
loop, create database connections, or own worker threads.

## Flows and Invariants

Setup connects Scan to `_start_workflow()`. Choice connects confirmation to
`_submit_choice()` and cancellation to `_cancel_choice()`. Settings displays the
injected database's path and connects actions to window handlers. Presentation
updates stay on the GUI thread; workers deliver progress through signals.
Keep existing attribute names and object names synchronized with window handlers
and theme styles when changing builders.

## Verification

Run `.venv\Scripts\python.exe -m unittest discover -s tests -v`. MainWindow tests
construct the page set and cover workflow completion and sequential batch checks.
