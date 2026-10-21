"""Executable selection state shared by scan and library-edit flows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QFileInfo, QObject, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox, QTreeWidgetItem

from shortcut_studio.ui.theme import BODY, ORANGE

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow

class SelectionController(QObject):
    """Executable selection state shared by scan and library-edit flows."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.folder: Path | None = None
        self.candidates: list[Path] = []
        self.context = "workflow"

    def show(
        self, raw_folder: str, raw_candidates: list[str], context: str = "workflow"
    ) -> None:
        folder = Path(raw_folder)
        self.context = context
        self.folder = folder
        self.candidates = [Path(path) for path in raw_candidates]
        self.window.choice_title.setText(f"Choose an executable for {folder.name}.")
        self.window.candidate_list.clear()
        for candidate in self.candidates:
            icon = self.window.icon_provider.icon(QFileInfo(str(candidate)))
            if icon.isNull():
                icon = QIcon.fromTheme("application-x-executable")
            display_name = (
                candidate.stem
                if candidate.suffix.casefold() == ".lnk"
                else candidate.name
            )
            item = QTreeWidgetItem([display_name, ""])
            item.setIcon(0, icon)
            item.setSizeHint(0, QSize(0, 64))
            item.setToolTip(0, str(candidate))
            self.window.candidate_list.addTopLevelItem(item)
            test_button = self.window._outline_button("Test")
            test_button.clicked.connect(
                lambda _checked=False, path=candidate: self.test_executable(path)
            )
            self.window.candidate_list.setItemWidget(item, 1, test_button)
        if self.window.candidate_list.topLevelItemCount():
            self.window.candidate_list.setCurrentItem(self.window.candidate_list.topLevelItem(0))
        row = self.window.folder_rows.get(folder)
        if row:
            row.set_status("Needs choice", ORANGE)
        self.window.pages.setCurrentWidget(self.window.choice_page)

    def submit(self) -> None:
        index = self.window.candidate_list.indexOfTopLevelItem(
            self.window.candidate_list.currentItem()
        )
        if index < 0 or index >= len(self.candidates):
            QMessageBox.information(self.window, "Choose an executable", "Select an executable first.")
            return
        chosen = self.candidates[index]
        if self.context == "edit":
            self.window._save_edited_choice(chosen)
            return
        self.window.pages.setCurrentWidget(self.window.progress_page)
        if self.folder:
            row = self.window.folder_rows.get(self.folder)
            if row:
                row.set_status("Creating", BODY)
        if self.window.workflow.worker:
            self.window.workflow.worker.choose(chosen)

    def cancel(self) -> None:
        if self.context == "edit":
            self.window.pages.setCurrentWidget(self.window.edit_detail_page)
        else:
            self.window._cancel_workflow()

    def open_folder(self) -> None:
        if self.folder:
            self.window._open_folder(self.folder)

    def test_executable(self, executable: Path) -> None:
        if not executable.is_file():
            QMessageBox.warning(
                self.window, "Executable unavailable", "This executable no longer exists."
            )
            return
        try:
            os.startfile(str(executable))
        except OSError:
            QMessageBox.warning(
                self.window, "Could not open executable", f"Windows could not open {executable.name}."
            )
