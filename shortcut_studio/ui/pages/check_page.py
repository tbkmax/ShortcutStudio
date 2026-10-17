from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_check_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("Check"))
    layout.addWidget(window._title("Check a saved folder pair."))
    layout.addWidget(
        window._body(
            "Recreate missing shortcuts, process new application folders, and remove shortcuts whose source folders are gone."
        )
    )
    check_all_row = QHBoxLayout()
    window.check_all_button = window._primary_button("Check all saved libraries")
    window.check_all_button.clicked.connect(window._check_all_pairs)
    check_all_row.addWidget(window.check_all_button)
    check_all_row.addStretch()
    layout.addLayout(check_all_row)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    window.check_container = QWidget()
    window.check_layout = QVBoxLayout(window.check_container)
    window.check_layout.setContentsMargins(0, 8, 0, 8)
    window.check_layout.setSpacing(10)
    window.check_layout.addStretch()
    scroll.setWidget(window.check_container)
    layout.addWidget(scroll, 1)
    layout.addLayout(window._back_row())
    return page
