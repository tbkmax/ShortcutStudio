from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QHBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_done_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addStretch()
    layout.addWidget(window._eyebrow("Complete"))
    layout.addWidget(window._title("Your shortcuts are ready."))
    window.done_summary = window._body("")
    layout.addWidget(window.done_summary)
    done = window._primary_button("Done")
    done.clicked.connect(window._reset_to_home)
    actions = QHBoxLayout()
    actions.addWidget(done)
    actions.addStretch()
    layout.addLayout(actions)
    layout.addStretch(2)
    return page
