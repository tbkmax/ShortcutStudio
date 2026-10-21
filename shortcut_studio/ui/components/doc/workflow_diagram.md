# Component Workflows

## Class Diagram

```mermaid
classDiagram
    QWidget <|-- HeaderBar
    QPushButton <|-- WindowControlButton
    QFrame <|-- FolderRow
    class HeaderBar {
        +MainWindow window
        +mousePressEvent(event)
        +mouseMoveEvent(event)
        +mouseReleaseEvent(event)
        +mouseDoubleClickEvent(event)
    }
    class WindowControlButton {
        +str icon_type
        +set_icon_type(icon_type)
        +paintEvent(event)
    }
    class FolderRow {
        +QLabel name_label
        +QLabel status_label
        +set_status(text, color)
    }
    HeaderBar *-- WindowControlButton : contains controls
    HeaderBar --> MainWindow : invokes callbacks
```

[HeaderBar](../header.py) owns its control widgets and forwards actions to the
window. [FolderRow](../folder_row.py) only renders folder status. Card and widget
modules expose factory functions rather than extra application classes.
