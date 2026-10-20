from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


class HeaderBar(QWidget):
    """Custom frameless window header bar with brand, navigation, and window controls."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("header")
        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 10, 16, 10)
        layout.setSpacing(10)

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

        divider = QFrame()
        divider.setObjectName("verticalDivider")
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setFixedHeight(18)
        layout.addWidget(divider)

        # Window controls: Minimize, Resize (Maximize/Restore), Close
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(4, 0, 0, 0)
        controls_layout.setSpacing(4)

        min_btn = QPushButton("—")
        min_btn.setObjectName("windowMinButton")
        min_btn.setToolTip("Minimize to tool bar")
        min_btn.clicked.connect(window._hide_to_tray)
        window.min_button = min_btn
        controls_layout.addWidget(min_btn)

        max_btn = QPushButton("□")
        max_btn.setObjectName("windowMaxButton")
        max_btn.setToolTip("Maximize")
        max_btn.clicked.connect(window._toggle_maximize)
        window.max_button = max_btn
        controls_layout.addWidget(max_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("windowCloseButton")
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(window.close)
        window.close_button = close_btn
        controls_layout.addWidget(close_btn)

        layout.addLayout(controls_layout)
        window.header_widget = self

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if not self.window.isMaximized():
                self.window.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.window._toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


def build_header(window: MainWindow) -> QWidget:
    return HeaderBar(window)

