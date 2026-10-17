from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_edit_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("Edit"))
    layout.addWidget(window._title("Choose a shortcut library."))
    layout.addWidget(
        window._body(
            "Select a saved source and target pair to change its executable choices."
        )
    )
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    window.edit_pairs_container = QWidget()
    window.edit_pairs_layout = QVBoxLayout(window.edit_pairs_container)
    window.edit_pairs_layout.setContentsMargins(0, 8, 0, 8)
    window.edit_pairs_layout.setSpacing(10)
    window.edit_pairs_layout.addStretch()
    scroll.setWidget(window.edit_pairs_container)
    layout.addWidget(scroll, 1)
    layout.addLayout(window._back_row())
    return page
