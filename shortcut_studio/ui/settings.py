"""Settings and JSON backup dialogs for the desktop UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from shortcut_studio.storage.database import Database

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow

class SettingsController(QObject):
    """Settings and JSON backup dialogs for the desktop UI."""

    def __init__(self, window: MainWindow, database: Database) -> None:
        super().__init__(window)
        self.window = window
        self.database = database

    def show(self) -> None:
        if self.window._workflow_active():
            return
        self.window.open_target_setting.setChecked(
            self.database.get_setting_bool("open_target_after_completion")
        )
        self.window.confirm_delete_setting.setChecked(
            self.database.get_setting_bool("confirm_pair_deletion")
        )
        self.window.pages.setCurrentWidget(self.window.settings_page)

    def apply(self) -> None:
        self.database.set_settings(
            {
                "open_target_after_completion": self.window.open_target_setting.isChecked(),
                "confirm_pair_deletion": self.window.confirm_delete_setting.isChecked(),
            }
        )
        QMessageBox.information(self.window, "Settings applied", "Your settings were saved.")

    def export_data(self) -> None:
        default_path = str(Path.home() / "shortcut-studio-export.json")
        selected, _filter = QFileDialog.getSaveFileName(
            self.window, "Export Shortcut Studio data", default_path, "JSON files (*.json)"
        )
        if not selected:
            return
        try:
            Path(selected).write_text(
                json.dumps(self.database.export_data(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self.window, "Export failed", str(exc))
            return
        QMessageBox.information(self.window, "Export complete", "Pairs and settings were exported.")

    def import_data(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self.window, "Import Shortcut Studio data", str(Path.home()), "JSON files (*.json)"
        )
        if not selected:
            return
        try:
            payload = json.loads(Path(selected).read_text(encoding="utf-8"))
            pair_count, item_count = self.database.import_data(payload)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self.window, "Import failed", str(exc))
            return
        self.show()
        QMessageBox.information(
            self.window,
            "Import complete",
            f"Imported {pair_count} pair(s) and {item_count} shortcut selection(s).",
        )
