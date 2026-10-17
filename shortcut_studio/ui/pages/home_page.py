from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


def build_home_page(window: MainWindow) -> QWidget:
    page, layout = window._page()
    layout.setContentsMargins(48, 36, 48, 36)
    layout.addWidget(window._eyebrow("Overview"))
    heading = QLabel("Shortcut Studio")
    heading.setObjectName("dashboardTitle")
    layout.addWidget(heading)
    layout.addWidget(
        window._body(
            "Create, check, and maintain Windows shortcut libraries from one workspace."
        )
    )

    status_card = QFrame()
    status_card.setObjectName("card")
    status_layout = QHBoxLayout(status_card)
    status_layout.setContentsMargins(24, 18, 24, 18)
    saved_block = QVBoxLayout()
    saved_label = window._eyebrow("Saved libraries")
    window.home_pair_count = QLabel("0")
    window.home_pair_count.setObjectName("metric")
    saved_block.addWidget(saved_label)
    saved_block.addWidget(window.home_pair_count)
    status_layout.addLayout(saved_block)
    divider = QFrame()
    divider.setObjectName("verticalDivider")
    divider.setFixedWidth(1)
    status_layout.addWidget(divider)
    recent_block = QVBoxLayout()
    recent_block.addWidget(window._eyebrow("Most recent pair"))
    window.home_recent_pair = QLabel("No saved pairs yet")
    window.home_recent_pair.setObjectName("homeRecent")
    window.home_recent_pair.setWordWrap(True)
    recent_block.addWidget(window.home_recent_pair)
    status_layout.addLayout(recent_block, 1)
    layout.addWidget(status_card)

    layout.addWidget(window._eyebrow("Quick actions"))
    first_row = QHBoxLayout()
    first_row.setSpacing(12)
    first_row.addWidget(
        window._dashboard_action(
            "Start New",
            "Choose source and target folders and build a new shortcut library.",
            "Start",
            window._go_start,
            primary=True,
        )
    )
    window.home_check_all_button = window._primary_button("Check all")
    window.home_check_all_button.clicked.connect(window._check_all_pairs)
    window.home_choose_check_button = window._outline_button("Choose pair")
    window.home_choose_check_button.clicked.connect(window._show_check_page)
    first_row.addWidget(
        window._dashboard_action(
            "Check",
            "Restore missing shortcuts and discover newly added application folders.",
            buttons=[window.home_check_all_button, window.home_choose_check_button],
        )
    )
    layout.addLayout(first_row)
    second_row = QHBoxLayout()
    second_row.setSpacing(12)
    second_row.addWidget(
        window._dashboard_action(
            "Edit",
            "Review saved shortcuts and change their executable or launcher.",
            "Choose pair",
            window._show_edit_page,
        )
    )
    second_row.addWidget(
        window._dashboard_action(
            "Saved Pairs",
            "View or remove the source and target pairs stored by the app.",
            "Open list",
            window._show_list_page,
        )
    )
    layout.addLayout(second_row)
    layout.addStretch()
    window._refresh_home_dashboard()
    return page
