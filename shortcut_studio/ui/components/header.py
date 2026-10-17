from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_header(window: MainWindow) -> QWidget:
    header = QWidget()
    header.setObjectName("header")
    layout = QHBoxLayout(header)
    layout.setContentsMargins(28, 14, 28, 14)
    brand = QLabel("SHORTCUT / STUDIO")
    brand.setObjectName("brand")
    layout.addWidget(brand)
    layout.addStretch()
    for text, handler in (
        ("Start New", window._go_start),
        ("Check", window._show_check_page),
        ("Edit", window._show_edit_page),
        ("List", window._show_list_page),
        ("Settings", window._show_settings_page),
    ):
        button = QPushButton(text)
        button.setObjectName("navButton")
        button.clicked.connect(handler)
        window.nav_buttons.append(button)
        layout.addWidget(button)
    return header
