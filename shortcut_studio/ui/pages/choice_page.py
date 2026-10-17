from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QHBoxLayout, QTreeWidget, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_choice_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("Executable selection"))
    window.choice_title = window._title("Choose an executable.")
    layout.addWidget(window.choice_title)
    layout.addWidget(
        window._body(
            "This folder contains more than one launch option. Select the executable or Windows shortcut you want to use."
        )
    )
    window.candidate_list = QTreeWidget()
    window.candidate_list.setHeaderLabels(["Launch file", ""])
    window.candidate_list.setIconSize(QSize(40, 40))
    window.candidate_list.setRootIsDecorated(False)
    window.candidate_list.setUniformRowHeights(True)
    window.candidate_list.setColumnWidth(0, 610)
    window.candidate_list.itemDoubleClicked.connect(
        lambda _item, _column: window._submit_choice()
    )
    layout.addWidget(window.candidate_list, 1)
    actions = QHBoxLayout()
    cancel = window._outline_button("Cancel")
    cancel.clicked.connect(window._cancel_choice)
    open_source = window._outline_button("Open source folder")
    open_source.clicked.connect(window._open_choice_folder)
    window.choose_button = window._primary_button("Use selected")
    window.choose_button.clicked.connect(window._submit_choice)
    actions.addWidget(cancel)
    actions.addWidget(open_source)
    actions.addStretch()
    actions.addWidget(window.choose_button)
    layout.addLayout(actions)
    return page
