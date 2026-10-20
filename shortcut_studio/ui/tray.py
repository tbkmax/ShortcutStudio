"""Windows notification-area lifecycle for the main window."""

from pathlib import Path
from typing import Callable

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QMenu, QStyle, QSystemTrayIcon

from shortcut_studio.ui.theme import APP_NAME


class TrayController:
    """Own the tray icon, menu, and hide/restore behavior."""

    def __init__(
        self, window: QMainWindow, icon_path: Path, quit_application: Callable[[], None]
    ) -> None:
        self.window = window
        self.icon = QSystemTrayIcon(window)
        icon = QIcon(str(icon_path)) if icon_path.exists() else window.windowIcon()
        if icon.isNull():
            icon = window.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.icon.setIcon(icon)
        self.icon.setToolTip(APP_NAME)

        menu = QMenu(window)
        self.open_action = menu.addAction(f"Open {APP_NAME}")
        open_font = self.open_action.font()
        open_font.setBold(True)
        self.open_action.setFont(open_font)
        self.open_action.triggered.connect(self.restore_window)

        self.toggle_action = menu.addAction("Hide to tool bar")
        self.toggle_action.triggered.connect(self.toggle_window)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(quit_application)

        self.icon.setContextMenu(menu)
        self.icon.activated.connect(self._activated)
        self.icon.show()
        self._hint_shown = False

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.restore_window()

    def restore_window(self) -> None:
        if self.window.isHidden():
            self.window.show()
        if self.window.isMinimized():
            self.window.showNormal()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.toggle_action.setText("Hide to tool bar")

    def toggle_window(self) -> None:
        if self.window.isHidden():
            self.restore_window()
        else:
            self.hide_window()

    def hide_window(self) -> bool:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False
        if self.icon.icon().isNull():
            self.icon.setIcon(
                self.window.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )
        if not self.icon.isVisible():
            self.icon.show()
        self.window.hide()
        self.toggle_action.setText(f"Show {APP_NAME}")
        return True

    def show_first_hide_hint(self) -> None:
        if self._hint_shown:
            return
        self._hint_shown = True
        self.icon.showMessage(
            APP_NAME,
            "Shortcut Studio is still running. Click the tray icon to reopen it, "
            "or right-click for options.",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    def hide_icon(self) -> None:
        self.icon.hide()
