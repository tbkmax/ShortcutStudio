from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QHBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_setup_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("01 / Setup"))
    layout.addWidget(window._title("Choose your folders."))
    layout.addWidget(
        window._body(
            "Each immediate source subfolder becomes one shortcut in the target folder."
        )
    )
    source_card, window.source_field = window._path_field(
        "Source folder", "Folder containing one subfolder per app"
    )
    target_card, window.target_field = window._path_field(
        "Target folder", "Folder where shortcuts will be created"
    )
    layout.addWidget(source_card)
    layout.addWidget(target_card)
    actions = QHBoxLayout()
    back = window._outline_button("Back")
    back.clicked.connect(window._show_home)
    scan = window._primary_button("Scan folders")
    scan.clicked.connect(window._start_workflow)
    actions.addWidget(back)
    actions.addStretch()
    actions.addWidget(scan)
    layout.addLayout(actions)
    layout.addStretch()
    return page
