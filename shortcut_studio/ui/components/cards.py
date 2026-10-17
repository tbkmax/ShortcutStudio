from __future__ import annotations

from pathlib import Path
from typing import Callable
from PyQt6.QtCore import QFileInfo
from PyQt6.QtWidgets import (
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from shortcut_studio.models import FolderPair, PairItem
from shortcut_studio.ui.components.widgets import outline_button, primary_button


def build_dashboard_action(
    title: str,
    description: str,
    button_text: str | None = None,
    handler: Callable[[], None] | None = None,
    primary: bool = False,
    buttons: list[QPushButton] | None = None,
) -> QFrame:
    card = QFrame()
    card.setObjectName("dashboardCard")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(22, 18, 22, 18)
    card_layout.setSpacing(9)
    title_label = QLabel(title)
    title_label.setObjectName("dashboardCardTitle")
    description_label = QLabel(description)
    description_label.setObjectName("dashboardCardBody")
    description_label.setWordWrap(True)
    button_row = QHBoxLayout()
    button_row.setSpacing(10)
    if buttons:
        for button in buttons:
            button_row.addWidget(button)
    elif button_text and handler:
        action = primary_button(button_text) if primary else outline_button(button_text)
        action.clicked.connect(handler)
        button_row.addWidget(action)
    button_row.addStretch()
    card_layout.addWidget(title_label)
    card_layout.addWidget(description_label)
    card_layout.addLayout(button_row)
    return card


def build_pair_card(
    pair: FolderPair,
    for_check: bool,
    for_edit: bool,
    on_check: Callable[[FolderPair], None],
    on_edit: Callable[[FolderPair], None],
    on_delete: Callable[[FolderPair], None],
) -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    layout = QHBoxLayout(card)
    layout.setContentsMargins(20, 16, 20, 16)
    details = QVBoxLayout()
    source = QLabel(f"SOURCE  {pair.source}")
    source.setObjectName("pairPath")
    source.setToolTip(str(pair.source))
    target = QLabel(f"TARGET  {pair.target}")
    target.setObjectName("pairPathMuted")
    target.setToolTip(str(pair.target))
    details.addWidget(source)
    details.addWidget(target)
    layout.addLayout(details, 1)
    if for_check:
        action = primary_button("Check")
        action.clicked.connect(lambda _checked=False, saved=pair: on_check(saved))
    elif for_edit:
        action = primary_button("Choose")
        action.clicked.connect(lambda _checked=False, saved=pair: on_edit(saved))
    else:
        action = outline_button("Delete")
        action.setObjectName("dangerButton")
        action.clicked.connect(lambda _checked=False, saved=pair: on_delete(saved))
    layout.addWidget(action)
    return card


def build_edit_item_card(
    pair_item: PairItem,
    icon_provider: QFileIconProvider,
    on_edit: Callable[[PairItem], None],
) -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    layout = QHBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(14)
    icon_source = (
        pair_item.shortcut if pair_item.shortcut.exists() else pair_item.executable
    )
    icon = icon_provider.icon(QFileInfo(str(icon_source)))
    icon_label = QLabel()
    icon_label.setFixedSize(42, 42)
    icon_label.setPixmap(icon.pixmap(40, 40))
    layout.addWidget(icon_label)
    details = QVBoxLayout()
    name = QLabel(pair_item.shortcut.stem)
    name.setObjectName("itemTitle")
    source_folder = QLabel(f"SOURCE FOLDER  {pair_item.folder}")
    source_folder.setObjectName("pairPathMuted")
    launch_file = QLabel(f"LAUNCH FILE  {pair_item.executable.name}")
    launch_file.setObjectName("pairPathMuted")
    details.addWidget(name)
    details.addWidget(source_folder)
    details.addWidget(launch_file)
    layout.addLayout(details, 1)
    edit_button = outline_button("Edit")
    edit_button.clicked.connect(
        lambda _checked=False, saved=pair_item: on_edit(saved)
    )
    layout.addWidget(edit_button)
    return card
