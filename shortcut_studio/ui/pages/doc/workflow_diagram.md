# Page Workflows

## Host Class Relationships

```mermaid
classDiagram
    class MainWindow {
        +QStackedWidget pages
        +QLineEdit source_field
        +QLineEdit target_field
        +QTreeWidget candidate_list
        +_start_workflow()
        +_submit_choice()
        +_cancel_choice()
    }
    class QStackedWidget {
        +addWidget(widget)
        +setCurrentWidget(widget)
    }
    MainWindow *-- QStackedWidget : owns page host
    QStackedWidget o-- QWidget : contains built pages
```

The package defines page-builder functions, not page classes. This diagram shows
the real Qt host types and MainWindow attributes assigned by the builders.

## Scan Action

```mermaid
sequenceDiagram
    participant User
    participant Setup as setup_page widgets
    participant Window as MainWindow
    participant Flow as WorkflowController
    User->>Setup: Click Scan folders
    Setup->>Window: _start_workflow()
    Window->>Flow: start_from_fields()
    Flow->>Flow: validate paths and launch worker
```

[setup_page.py](../setup_page.py) binds the action; the window and workflow
controller perform validation and launch. Page construction has no scan side effects.
