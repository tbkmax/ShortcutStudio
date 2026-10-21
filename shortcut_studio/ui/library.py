"""Saved-library display, editing, and persistence actions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFrame, QMessageBox, QVBoxLayout

from shortcut_studio.core.shell_link import install_launch_item, shortcut_path
from shortcut_studio.models import FolderPair, PairItem
from shortcut_studio.scanner import find_executables
from shortcut_studio.storage.database import Database
from shortcut_studio.ui.components import build_pair_card, build_edit_item_card

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


class LibraryController(QObject):
    """Saved-library display, editing, and persistence actions."""

    def __init__(self, window: MainWindow, database: Database) -> None:
        super().__init__(window)
        self.window = window
        self.database = database
        self.current_pair: FolderPair | None = None

    def refresh_dashboard(self) -> None:
        if not hasattr(self.window, "home_pair_count"):
            return
        pairs = self.database.list_pairs()
        self.window.home_pair_count.setText(str(len(pairs)))
        if pairs:
            recent = pairs[0]
            self.window.home_recent_pair.setText(
                f"{recent.source.name or recent.source}  →  {recent.target.name or recent.target}"
            )
            self.window.home_recent_pair.setToolTip(
                f"Source: {recent.source}\nTarget: {recent.target}"
            )
        else:
            self.window.home_recent_pair.setText("No saved pairs yet")
            self.window.home_recent_pair.setToolTip("")

    def refresh_pairs(
        self, layout: QVBoxLayout, for_check: bool, for_edit: bool = False
    ) -> None:
        self.window._clear_dynamic_layout(layout)
        pairs = self.database.list_pairs()
        if for_check and hasattr(self.window, "check_all_button"):
            self.window.check_all_button.setEnabled(bool(pairs))
        if not pairs:
            empty = QFrame()
            empty.setObjectName("card")
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(24, 24, 24, 24)
            empty_layout.addWidget(self.window._body("No saved folder pairs yet. Start a new run first."))
            layout.insertWidget(0, empty)
            return
        for pair in pairs:
            layout.insertWidget(
                layout.count() - 1, self.pair_card(pair, for_check, for_edit)
            )

    def pair_card(self, pair: FolderPair, for_check: bool, for_edit: bool) -> QFrame:
        return build_pair_card(
            pair,
            for_check,
            for_edit,
            on_check=self.check_pair,
            on_edit=self.edit_pair,
            on_delete=self.delete_pair,
        )

    def check_pair(self, pair: FolderPair) -> None:
        if not pair.source.is_dir() or not pair.target.is_dir():
            QMessageBox.warning(
                self.window,
                "Folder unavailable",
                "The source or target folder no longer exists. Update the folders or delete this saved pair.",
            )
            return
        self.window._launch_workflow(pair.source, pair.target, pair.id, check_only=True)

    def delete_pair(self, pair: FolderPair) -> None:
        confirmed = True
        if self.database.get_setting_bool("confirm_pair_deletion"):
            answer = QMessageBox.question(
                self.window,
                "Delete saved pair",
                "Delete this saved pair and its run history? Existing shortcuts and application files will not be deleted.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            confirmed = answer == QMessageBox.StandardButton.Yes
        if confirmed:
            self.database.delete_pair(pair.id)
            self.refresh_pairs(self.window.list_layout, for_check=False)

    def edit_pair(self, pair: FolderPair) -> None:
        self.current_pair = pair
        self.window.edit_detail_title.setText(pair.target.name or str(pair.target))
        self.window.edit_detail_caption.setText(
            f"Source: {pair.source}\nTarget: {pair.target}"
        )
        self.refresh_items()
        self.window.pages.setCurrentWidget(self.window.edit_detail_page)

    def refresh_items(self) -> None:
        self.window._clear_dynamic_layout(self.window.edit_items_layout)
        if not self.current_pair:
            return
        items = self.database.list_pair_items(self.current_pair.id)
        if not items:
            empty = QFrame()
            empty.setObjectName("card")
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(24, 24, 24, 24)
            empty_layout.addWidget(
                self.window._body("No saved shortcut selections are available for this pair.")
            )
            self.window.edit_items_layout.insertWidget(0, empty)
            return
        for pair_item in items:
            self.window.edit_items_layout.insertWidget(
                self.window.edit_items_layout.count() - 1,
                self.item_card(pair_item),
            )

    def item_card(self, pair_item: PairItem) -> QFrame:
        return build_edit_item_card(
            pair_item, self.window.icon_provider, self.edit_item
        )

    def edit_item(self, pair_item: PairItem) -> None:
        if not pair_item.folder.is_dir():
            QMessageBox.warning(
                self.window, "Source folder unavailable", "This source subfolder no longer exists."
            )
            return
        candidates = find_executables(pair_item.folder)
        if not candidates:
            QMessageBox.warning(
                self.window, "No launch files", "No executable or executable-named shortcut was found."
            )
            return
        self.window._show_choice(
            str(pair_item.folder), [str(path) for path in candidates], context="edit"
        )

    def open_target(self) -> None:
        if self.current_pair:
            self.window._open_folder(self.current_pair.target)

    def save_choice(self, folder: Path | None, chosen: Path) -> None:
        if not self.current_pair or not folder:
            QMessageBox.warning(self.window, "Edit unavailable", "The saved pair is no longer available.")
            return
        destination = shortcut_path(
            self.current_pair.target, folder.name
        )
        try:
            install_launch_item(chosen, destination)
            self.database.save_pair_item(
                self.current_pair.id,
                folder,
                chosen,
                destination,
            )
            self.database.touch_pair(self.current_pair.id)
        except OSError as exc:
            QMessageBox.critical(self.window, "Could not update shortcut", str(exc))
            return
        self.refresh_items()
        self.window.pages.setCurrentWidget(self.window.edit_detail_page)
