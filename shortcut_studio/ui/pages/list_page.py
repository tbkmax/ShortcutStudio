from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_list_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("Saved pairs"))
    layout.addWidget(window._title("Your shortcut libraries."))
    layout.addWidget(
        window._body(
            "Deleting a pair removes its saved configuration and history. Existing shortcuts and source files are left untouched."
        )
    )
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    window.list_container = QWidget()
    window.list_layout = QVBoxLayout(window.list_container)
    window.list_layout.setContentsMargins(0, 8, 0, 8)
    window.list_layout.setSpacing(10)
    window.list_layout.addStretch()
    scroll.setWidget(window.list_container)
    layout.addWidget(scroll, 1)
    layout.addLayout(window._back_row())
    return page
