from __future__ import annotations

from typing import Callable
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def page_container(
    margins: tuple[int, int, int, int] = (64, 50, 64, 50), spacing: int = 18
) -> tuple[QWidget, QVBoxLayout]:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return page, layout


def eyebrow_label(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setObjectName("eyebrow")
    return label


def title_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("title")
    label.setWordWrap(True)
    return label


def body_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("body")
    label.setWordWrap(True)
    return label


def outline_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def primary_button(text: str) -> QPushButton:
    button = outline_button(text)
    button.setObjectName("primaryButton")
    return button


def path_field_card(
    label_text: str, hint: str, browse_handler: Callable[[], None]
) -> tuple[QFrame, QLineEdit]:
    card = QFrame()
    card.setObjectName("card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(10)
    label = eyebrow_label(label_text)
    row = QHBoxLayout()
    field = QLineEdit()
    field.setPlaceholderText(hint)
    browse = outline_button("Browse")
    browse.clicked.connect(browse_handler)
    row.addWidget(field, 1)
    row.addWidget(browse)
    layout.addWidget(label)
    layout.addLayout(row)
    return card, field


def back_row_layout(back_handler: Callable[[], None]) -> QHBoxLayout:
    row = QHBoxLayout()
    back = outline_button("Back")
    back.clicked.connect(back_handler)
    row.addWidget(back)
    row.addStretch()
    return row
