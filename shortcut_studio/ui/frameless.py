"""Frameless resize gestures and maximize-state presentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, Qt

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow

RESIZE_MARGIN = 6
EDGE_NONE = 0
EDGE_LEFT = 1
EDGE_TOP = 2
EDGE_RIGHT = 4
EDGE_BOTTOM = 8


class FramelessController(QObject):
    """Own resize gesture state and update the custom window chrome."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self._resize_edge = EDGE_NONE
        self._drag_start_geom: QRect | None = None
        self._drag_start_pos: QPoint | None = None

    def toggle_maximize(self) -> None:
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def change_event(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            is_max = self.window.isMaximized()
            if hasattr(self.window, "max_button"):
                if hasattr(self.window.max_button, "set_icon_type"):
                    self.window.max_button.set_icon_type("restore" if is_max else "maximize")
                self.window.max_button.setToolTip("Restore" if is_max else "Maximize")
            if hasattr(self.window, "shell"):
                self.window.shell.setProperty("maximized", is_max)
                self.window.shell.style().unpolish(self.window.shell)
                self.window.shell.style().polish(self.window.shell)
            if hasattr(self.window, "header_widget"):
                self.window.header_widget.setProperty("maximized", is_max)
                self.window.header_widget.style().unpolish(self.window.header_widget)
                self.window.header_widget.style().polish(self.window.header_widget)
            if hasattr(self.window, "pages"):
                self.window.pages.setProperty("maximized", is_max)
                self.window.pages.style().unpolish(self.window.pages)
                self.window.pages.style().polish(self.window.pages)

    def determine_edge(self, pos: QPoint) -> int:
        margin = RESIZE_MARGIN
        w, h = self.window.width(), self.window.height()
        edge = EDGE_NONE
        if pos.x() <= margin:
            edge |= EDGE_LEFT
        if pos.x() >= w - margin:
            edge |= EDGE_RIGHT
        if pos.y() <= margin:
            edge |= EDGE_TOP
        if pos.y() >= h - margin:
            edge |= EDGE_BOTTOM
        return edge

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is getattr(self.window, "shell", None):
            event_type = event.type()
            if event_type == QEvent.Type.MouseMove:
                if self._resize_edge != EDGE_NONE:
                    diff = event.globalPosition().toPoint() - self._drag_start_pos
                    geom = QRect(self._drag_start_geom)
                    min_w, min_h = self.window.minimumWidth(), self.window.minimumHeight()

                    if self._resize_edge & EDGE_LEFT:
                        new_left = geom.left() + diff.x()
                        if geom.right() - new_left >= min_w:
                            geom.setLeft(new_left)
                        else:
                            geom.setLeft(geom.right() - min_w)
                    if self._resize_edge & EDGE_RIGHT:
                        new_right = geom.right() + diff.x()
                        if new_right - geom.left() >= min_w:
                            geom.setRight(new_right)
                        else:
                            geom.setRight(geom.left() + min_w)
                    if self._resize_edge & EDGE_TOP:
                        new_top = geom.top() + diff.y()
                        if geom.bottom() - new_top >= min_h:
                            geom.setTop(new_top)
                        else:
                            geom.setTop(geom.bottom() - min_h)
                    if self._resize_edge & EDGE_BOTTOM:
                        new_bottom = geom.bottom() + diff.y()
                        if new_bottom - geom.top() >= min_h:
                            geom.setBottom(new_bottom)
                        else:
                            geom.setBottom(geom.top() + min_h)

                    self.window.setGeometry(geom)
                    return True
                elif not self.window.isMaximized():
                    edge = self.determine_edge(event.position().toPoint())
                    if edge in (EDGE_LEFT, EDGE_RIGHT):
                        self.window.setCursor(Qt.CursorShape.SizeHorCursor)
                    elif edge in (EDGE_TOP, EDGE_BOTTOM):
                        self.window.setCursor(Qt.CursorShape.SizeVerCursor)
                    elif edge in (EDGE_LEFT | EDGE_TOP, EDGE_RIGHT | EDGE_BOTTOM):
                        self.window.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif edge in (EDGE_RIGHT | EDGE_TOP, EDGE_LEFT | EDGE_BOTTOM):
                        self.window.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    else:
                        self.window.unsetCursor()
            elif event_type == QEvent.Type.MouseButtonPress:
                if not self.window.isMaximized() and event.button() == Qt.MouseButton.LeftButton:
                    edge = self.determine_edge(event.position().toPoint())
                    if edge != EDGE_NONE:
                        self._resize_edge = edge
                        self._drag_start_geom = self.window.geometry()
                        self._drag_start_pos = event.globalPosition().toPoint()
                        return True
            elif event_type == QEvent.Type.MouseButtonRelease:
                if self._resize_edge != EDGE_NONE:
                    self._resize_edge = EDGE_NONE
                    self.window.unsetCursor()
                    return True
            elif event_type == QEvent.Type.Leave:
                if self._resize_edge == EDGE_NONE:
                    self.window.unsetCursor()
        return super().eventFilter(obj, event)
