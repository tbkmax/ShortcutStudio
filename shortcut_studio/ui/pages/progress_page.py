from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_progress_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("02 / Processing"))
    layout.addWidget(window._title("Building your shortcut library."))
    window.progress_caption = window._body("Reading folders…")
    layout.addWidget(window.progress_caption)
    window.progress_bar = QProgressBar()
    window.progress_bar.setRange(0, 1)
    window.progress_bar.setValue(0)
    window.progress_bar.setTextVisible(False)
    layout.addWidget(window.progress_bar)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    window.rows_container = QWidget()
    window.rows_layout = QVBoxLayout(window.rows_container)
    window.rows_layout.setContentsMargins(0, 8, 0, 8)
    window.rows_layout.setSpacing(8)
    window.rows_layout.addStretch()
    scroll.setWidget(window.rows_container)
    layout.addWidget(scroll, 1)
    cancel = window._outline_button("Cancel")
    cancel.clicked.connect(window._cancel_workflow)
    controls = QHBoxLayout()
    controls.addStretch()
    controls.addWidget(cancel)
    layout.addLayout(controls)
    return page
