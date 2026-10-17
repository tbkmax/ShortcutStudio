from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_edit_detail_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("Edit shortcuts"))
    window.edit_detail_title = window._title("Shortcut library")
    layout.addWidget(window.edit_detail_title)
    window.edit_detail_caption = window._body("")
    layout.addWidget(window.edit_detail_caption)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    window.edit_items_container = QWidget()
    window.edit_items_layout = QVBoxLayout(window.edit_items_container)
    window.edit_items_layout.setContentsMargins(0, 8, 0, 8)
    window.edit_items_layout.setSpacing(10)
    window.edit_items_layout.addStretch()
    scroll.setWidget(window.edit_items_container)
    layout.addWidget(scroll, 1)
    actions = QHBoxLayout()
    back = window._outline_button("Back")
    back.clicked.connect(window._show_edit_page)
    open_target = window._outline_button("Open target folder")
    open_target.clicked.connect(window._open_current_target)
    actions.addWidget(back)
    actions.addStretch()
    actions.addWidget(open_target)
    layout.addLayout(actions)
    return page
