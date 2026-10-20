from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


class WindowControlButton(QPushButton):
    """Custom title bar button with crisp, balanced vector window control icons."""

    def __init__(self, icon_type: str, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self.icon_type = icon_type  # 'minimize', 'maximize', 'restore', 'close'
        self.setFixedSize(38, 28)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_icon_type(self, icon_type: str) -> None:
        if self.icon_type != icon_type:
            self.icon_type = icon_type
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_close = self.objectName() == "windowCloseButton"
        if is_close and self.underMouse():
            color = QColor("#ffffff")
        elif self.underMouse():
            color = QColor("#ffffff")
        else:
            color = QColor("#cccccc")

        w, h = self.width(), self.height()
        cx, cy = int(w / 2), int(h / 2)

        if self.icon_type == "minimize":
            pen = QPen(color, 1.3)
            painter.setPen(pen)
            painter.drawLine(cx - 5, cy, cx + 5, cy)
        elif self.icon_type == "maximize":
            pen = QPen(color, 1.2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRect(cx - 5, cy - 5, 10, 10))
        elif self.icon_type == "restore":
            pen = QPen(color, 1.1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # Upper-right back square
            painter.drawRect(QRect(cx - 3, cy - 5, 8, 8))
            # Lower-left front square (fill to mask overlap)
            fill_color = QColor("#242424") if self.underMouse() else QColor("#0a0a0a")
            painter.fillRect(QRect(cx - 5, cy - 3, 8, 8), fill_color)
            painter.drawRect(QRect(cx - 5, cy - 3, 8, 8))
        elif self.icon_type == "close":
            pen = QPen(color, 1.3)
            painter.setPen(pen)
            painter.drawLine(cx - 5, cy - 5, cx + 5, cy + 5)
            painter.drawLine(cx + 5, cy - 5, cx - 5, cy + 5)


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

        min_btn = WindowControlButton("minimize", self)
        min_btn.setObjectName("windowMinButton")
        min_btn.setToolTip("Minimize")
        min_btn.clicked.connect(window.showMinimized)
        window.min_button = min_btn
        controls_layout.addWidget(min_btn)

        max_btn = WindowControlButton("maximize", self)
        max_btn.setObjectName("windowMaxButton")
        max_btn.setToolTip("Maximize")
        max_btn.clicked.connect(window._toggle_maximize)
        window.max_button = max_btn
        controls_layout.addWidget(max_btn)

        close_btn = WindowControlButton("close", self)
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

