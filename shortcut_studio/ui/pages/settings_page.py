from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_settings_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.addWidget(window._eyebrow("Settings"))
    layout.addWidget(window._title("Application settings."))
    layout.addWidget(
        window._body("Settings are stored in the Shortcut Studio database.")
    )
    preferences = QFrame()
    preferences.setObjectName("card")
    preferences_layout = QVBoxLayout(preferences)
    preferences_layout.setContentsMargins(24, 20, 24, 20)
    preferences_layout.setSpacing(14)
    window.open_target_setting = QCheckBox(
        "Open the target folder after completion"
    )
    window.confirm_delete_setting = QCheckBox(
        "Ask for confirmation before deleting a saved pair"
    )
    preferences_layout.addWidget(window.open_target_setting)
    preferences_layout.addWidget(window.confirm_delete_setting)
    layout.addWidget(preferences)
    data_card = QFrame()
    data_card.setObjectName("card")
    data_layout = QVBoxLayout(data_card)
    data_layout.setContentsMargins(24, 20, 24, 20)
    data_layout.setSpacing(12)
    data_layout.addWidget(window._eyebrow("Data"))
    database_path = QLabel(str(window.database.path))
    database_path.setObjectName("pairPathMuted")
    database_path.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
    )
    data_layout.addWidget(database_path)
    data_actions = QHBoxLayout()
    open_database = window._outline_button("Open database folder")
    open_database.clicked.connect(window._open_database_folder)
    export_button = window._outline_button("Export")
    export_button.clicked.connect(window._export_data)
    import_button = window._outline_button("Import")
    import_button.clicked.connect(window._import_data)
    data_actions.addWidget(open_database)
    data_actions.addWidget(export_button)
    data_actions.addWidget(import_button)
    data_actions.addStretch()
    data_layout.addLayout(data_actions)
    layout.addWidget(data_card)
    apply_button = window._primary_button("Apply")
    apply_button.clicked.connect(window._apply_settings)
    apply_row = window._back_row()
    apply_row.addWidget(apply_button)
    layout.addLayout(apply_row)
    layout.addStretch()
    return page
