# UI Component Architecture

Components build reusable Qt widgets and layouts. They do not own process
startup, database connections, or worker lifetime.

## Component Inventory

| Component | File Link | Responsibility | Key Interfaces |
| :--- | :--- | :--- | :--- |
| Header | [header.py](../header.py) | Navigation and frameless window controls | `HeaderBar`, `WindowControlButton`, `build_header()` |
| Folder row | [folder_row.py](../folder_row.py) | Display a folder name and status | `FolderRow.set_status()` |
| Cards | [cards.py](../cards.py) | Build dashboard actions, pair and item cards | `build_dashboard_action()`, `build_pair_card()`, `build_edit_item_card()` |
| Widget helpers | [widgets.py](../widgets.py) | Labels, buttons, page and path layouts | `page_container()`, `path_field_card()`, `back_row_layout()` |
| Exports | [__init__.py](../__init__.py) | Stable component factory exports | Widget factories and `FolderRow` |

## Ownership, Runtime Flows, and Safeguards

Qt widget parenting/layouts own widget lifetime. The header retains its window
reference and connects signals to window callbacks. It sets the window's
navigation/control attributes; these are part of the current UI contract.
`FolderRow` owns its labels and uppercases status display text. Factories receive
handlers rather than creating workers or databases. Widgets must be created and
updated on the GUI thread.

Object names used by [theme.py](../../theme.py) are styling contracts. Window
control painting and interaction live in header.py; page routing remains in
MainWindow. No installed resource paths should be derived from the working
directory.

## Verification

Run `.venv\Scripts\python.exe -m unittest discover -s tests -v`. Window tests
exercise header controls, maximize/restore, and tray behavior.
