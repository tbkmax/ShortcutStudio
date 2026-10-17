from __future__ import annotations

import os
import json
import sys
from pathlib import Path

from PyQt6.QtCore import QFileInfo, QSize, Qt
from PyQt6.QtGui import QCloseEvent, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .models import FolderPair, FolderResult, PairItem, ResultStatus
from .scanner import find_executables
from .shortcuts import install_launch_item, shortcut_path
from .worker import ScanWorker


APP_NAME = "Shortcut Studio"
CANVAS = "#0a0a0a"
CARD = "#191919"
SOFT = "#1a1c20"
HAIRLINE = "#2c2f34"
WHITE = "#ffffff"
BODY = "#dadbdf"
MUTED = "#7d8187"
GREEN = "#48d597"
ORANGE = "#ff7a17"
RED = "#ff6b6b"


class FolderRow(QFrame):
    def __init__(self, folder: Path) -> None:
        super().__init__()
        self.setObjectName("folderRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        self.name_label = QLabel(folder.name)
        self.name_label.setToolTip(str(folder))
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_label = QLabel("QUEUED")
        self.status_label.setObjectName("monoMuted")
        layout.addWidget(self.name_label)
        layout.addWidget(self.status_label)

    def set_status(self, text: str, color: str) -> None:
        self.status_label.setText(text.upper())
        self.status_label.setStyleSheet(
            f"font-family: Consolas; font-size: 12px; letter-spacing: 1px; color: {color};"
        )


class MainWindow(QMainWindow):
    def __init__(self, database_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(820, 620)
        self.resize(980, 720)

        local_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.database = Database(
            database_path or local_data / "ShortcutStudio" / "shortcut_studio.db"
        )
        self.worker: ScanWorker | None = None
        self.check_queue: list[FolderPair] = []
        self.batch_check_total = 0
        self.batch_check_completed = 0
        self.batch_check_unavailable = 0
        self.batch_check_totals = [0, 0, 0, 0, 0]
        self.folder_rows: dict[Path, FolderRow] = {}
        self.current_choice_folder: Path | None = None
        self.current_candidates: list[Path] = []
        self.choice_context = "workflow"
        self.current_edit_pair: FolderPair | None = None
        self.active_target: Path | None = None
        self.icon_provider = QFileIconProvider()
        self.nav_buttons: list[QPushButton] = []

        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._build_header())
        self.pages = QStackedWidget()
        self.home_page = self._build_home_page()
        self.setup_page = self._build_setup_page()
        self.check_page = self._build_check_page()
        self.list_page = self._build_list_page()
        self.edit_page = self._build_edit_page()
        self.edit_detail_page = self._build_edit_detail_page()
        self.settings_page = self._build_settings_page()
        self.progress_page = self._build_progress_page()
        self.choice_page = self._build_choice_page()
        self.done_page = self._build_done_page()
        for page in (
            self.home_page,
            self.setup_page,
            self.check_page,
            self.list_page,
            self.edit_page,
            self.edit_detail_page,
            self.settings_page,
            self.progress_page,
            self.choice_page,
            self.done_page,
        ):
            self.pages.addWidget(page)
        shell_layout.addWidget(self.pages)
        self.setCentralWidget(shell)
        self.setStyleSheet(STYLESHEET)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 14, 28, 14)
        brand = QLabel("SHORTCUT / STUDIO")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        layout.addStretch()
        for text, handler in (
            ("Start New", self._go_start),
            ("Check", self._show_check_page),
            ("Edit", self._show_edit_page),
            ("List", self._show_list_page),
            ("Settings", self._show_settings_page),
        ):
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.clicked.connect(handler)
            self.nav_buttons.append(button)
            layout.addWidget(button)
        return header

    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(64, 50, 64, 50)
        layout.setSpacing(18)
        return page, layout

    def _eyebrow(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("eyebrow")
        return label

    def _title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("title")
        label.setWordWrap(True)
        return label

    def _body(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("body")
        label.setWordWrap(True)
        return label

    def _outline_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _primary_button(self, text: str) -> QPushButton:
        button = self._outline_button(text)
        button.setObjectName("primaryButton")
        return button

    def _build_home_page(self) -> QWidget:
        page, layout = self._page()
        layout.setContentsMargins(48, 36, 48, 36)
        layout.addWidget(self._eyebrow("Overview"))
        heading = QLabel("Shortcut Studio")
        heading.setObjectName("dashboardTitle")
        layout.addWidget(heading)
        layout.addWidget(
            self._body(
                "Create, check, and maintain Windows shortcut libraries from one workspace."
            )
        )

        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(24, 18, 24, 18)
        saved_block = QVBoxLayout()
        saved_label = self._eyebrow("Saved libraries")
        self.home_pair_count = QLabel("0")
        self.home_pair_count.setObjectName("metric")
        saved_block.addWidget(saved_label)
        saved_block.addWidget(self.home_pair_count)
        status_layout.addLayout(saved_block)
        divider = QFrame()
        divider.setObjectName("verticalDivider")
        divider.setFixedWidth(1)
        status_layout.addWidget(divider)
        recent_block = QVBoxLayout()
        recent_block.addWidget(self._eyebrow("Most recent pair"))
        self.home_recent_pair = QLabel("No saved pairs yet")
        self.home_recent_pair.setObjectName("homeRecent")
        self.home_recent_pair.setWordWrap(True)
        recent_block.addWidget(self.home_recent_pair)
        status_layout.addLayout(recent_block, 1)
        layout.addWidget(status_card)

        layout.addWidget(self._eyebrow("Quick actions"))
        first_row = QHBoxLayout()
        first_row.setSpacing(12)
        first_row.addWidget(
            self._dashboard_action(
                "Start New",
                "Choose source and target folders and build a new shortcut library.",
                "Start",
                self._go_start,
                primary=True,
            )
        )
        self.home_check_all_button = self._primary_button("Check all")
        self.home_check_all_button.clicked.connect(self._check_all_pairs)
        self.home_choose_check_button = self._outline_button("Choose pair")
        self.home_choose_check_button.clicked.connect(self._show_check_page)
        first_row.addWidget(
            self._dashboard_action(
                "Check",
                "Restore missing shortcuts and discover newly added application folders.",
                buttons=[self.home_check_all_button, self.home_choose_check_button],
            )
        )
        layout.addLayout(first_row)
        second_row = QHBoxLayout()
        second_row.setSpacing(12)
        second_row.addWidget(
            self._dashboard_action(
                "Edit",
                "Review saved shortcuts and change their executable or launcher.",
                "Choose pair",
                self._show_edit_page,
            )
        )
        second_row.addWidget(
            self._dashboard_action(
                "Saved Pairs",
                "View or remove the source and target pairs stored by the app.",
                "Open list",
                self._show_list_page,
            )
        )
        layout.addLayout(second_row)
        layout.addStretch()
        self._refresh_home_dashboard()
        return page

    def _dashboard_action(
        self,
        title: str,
        description: str,
        button_text: str | None = None,
        handler=None,
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
            action = (
                self._primary_button(button_text)
                if primary
                else self._outline_button(button_text)
            )
            action.clicked.connect(handler)
            button_row.addWidget(action)
        button_row.addStretch()
        card_layout.addWidget(title_label)
        card_layout.addWidget(description_label)
        card_layout.addLayout(button_row)
        return card

    def _refresh_home_dashboard(self) -> None:
        if not hasattr(self, "home_pair_count"):
            return
        pairs = self.database.list_pairs()
        self.home_pair_count.setText(str(len(pairs)))
        if pairs:
            recent = pairs[0]
            self.home_recent_pair.setText(
                f"{recent.source.name or recent.source}  →  {recent.target.name or recent.target}"
            )
            self.home_recent_pair.setToolTip(
                f"Source: {recent.source}\nTarget: {recent.target}"
            )
        else:
            self.home_recent_pair.setText("No saved pairs yet")
            self.home_recent_pair.setToolTip("")

    def _build_check_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("Check"))
        layout.addWidget(self._title("Check a saved folder pair."))
        layout.addWidget(
            self._body(
                "Recreate missing shortcuts, process new application folders, and remove shortcuts whose source folders are gone."
            )
        )
        check_all_row = QHBoxLayout()
        self.check_all_button = self._primary_button("Check all saved libraries")
        self.check_all_button.clicked.connect(self._check_all_pairs)
        check_all_row.addWidget(self.check_all_button)
        check_all_row.addStretch()
        layout.addLayout(check_all_row)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.check_container = QWidget()
        self.check_layout = QVBoxLayout(self.check_container)
        self.check_layout.setContentsMargins(0, 8, 0, 8)
        self.check_layout.setSpacing(10)
        self.check_layout.addStretch()
        scroll.setWidget(self.check_container)
        layout.addWidget(scroll, 1)
        layout.addLayout(self._back_row())
        return page

    def _build_list_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("Saved pairs"))
        layout.addWidget(self._title("Your shortcut libraries."))
        layout.addWidget(
            self._body(
                "Deleting a pair removes its saved configuration and history. Existing shortcuts and source files are left untouched."
            )
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 8, 0, 8)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)
        layout.addLayout(self._back_row())
        return page

    def _build_edit_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("Edit"))
        layout.addWidget(self._title("Choose a shortcut library."))
        layout.addWidget(
            self._body("Select a saved source and target pair to change its executable choices.")
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.edit_pairs_container = QWidget()
        self.edit_pairs_layout = QVBoxLayout(self.edit_pairs_container)
        self.edit_pairs_layout.setContentsMargins(0, 8, 0, 8)
        self.edit_pairs_layout.setSpacing(10)
        self.edit_pairs_layout.addStretch()
        scroll.setWidget(self.edit_pairs_container)
        layout.addWidget(scroll, 1)
        layout.addLayout(self._back_row())
        return page

    def _build_edit_detail_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("Edit shortcuts"))
        self.edit_detail_title = self._title("Shortcut library")
        layout.addWidget(self.edit_detail_title)
        self.edit_detail_caption = self._body("")
        layout.addWidget(self.edit_detail_caption)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.edit_items_container = QWidget()
        self.edit_items_layout = QVBoxLayout(self.edit_items_container)
        self.edit_items_layout.setContentsMargins(0, 8, 0, 8)
        self.edit_items_layout.setSpacing(10)
        self.edit_items_layout.addStretch()
        scroll.setWidget(self.edit_items_container)
        layout.addWidget(scroll, 1)
        actions = QHBoxLayout()
        back = self._outline_button("Back")
        back.clicked.connect(self._show_edit_page)
        open_target = self._outline_button("Open target folder")
        open_target.clicked.connect(self._open_current_target)
        actions.addWidget(back)
        actions.addStretch()
        actions.addWidget(open_target)
        layout.addLayout(actions)
        return page

    def _build_settings_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("Settings"))
        layout.addWidget(self._title("Application settings."))
        layout.addWidget(self._body("Settings are stored in the Shortcut Studio database."))
        preferences = QFrame()
        preferences.setObjectName("card")
        preferences_layout = QVBoxLayout(preferences)
        preferences_layout.setContentsMargins(24, 20, 24, 20)
        preferences_layout.setSpacing(14)
        self.open_target_setting = QCheckBox("Open the target folder after completion")
        self.confirm_delete_setting = QCheckBox("Ask for confirmation before deleting a saved pair")
        preferences_layout.addWidget(self.open_target_setting)
        preferences_layout.addWidget(self.confirm_delete_setting)
        layout.addWidget(preferences)
        data_card = QFrame()
        data_card.setObjectName("card")
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(24, 20, 24, 20)
        data_layout.setSpacing(12)
        data_layout.addWidget(self._eyebrow("Data"))
        database_path = QLabel(str(self.database.path))
        database_path.setObjectName("pairPathMuted")
        database_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_layout.addWidget(database_path)
        data_actions = QHBoxLayout()
        open_database = self._outline_button("Open database folder")
        open_database.clicked.connect(self._open_database_folder)
        export_button = self._outline_button("Export")
        export_button.clicked.connect(self._export_data)
        import_button = self._outline_button("Import")
        import_button.clicked.connect(self._import_data)
        data_actions.addWidget(open_database)
        data_actions.addWidget(export_button)
        data_actions.addWidget(import_button)
        data_actions.addStretch()
        data_layout.addLayout(data_actions)
        layout.addWidget(data_card)
        apply_button = self._primary_button("Apply")
        apply_button.clicked.connect(self._apply_settings)
        apply_row = self._back_row()
        apply_row.addWidget(apply_button)
        layout.addLayout(apply_row)
        layout.addStretch()
        return page

    def _back_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        back = self._outline_button("Back")
        back.clicked.connect(self._show_home)
        row.addWidget(back)
        row.addStretch()
        return row

    def _path_field(self, label_text: str, hint: str) -> tuple[QWidget, QLineEdit]:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)
        label = self._eyebrow(label_text)
        row = QHBoxLayout()
        field = QLineEdit()
        field.setPlaceholderText(hint)
        browse = self._outline_button("Browse")
        browse.clicked.connect(lambda: self._browse_for_folder(field, label_text))
        row.addWidget(field, 1)
        row.addWidget(browse)
        layout.addWidget(label)
        layout.addLayout(row)
        return card, field

    def _build_setup_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("01 / Setup"))
        layout.addWidget(self._title("Choose your folders."))
        layout.addWidget(self._body("Each immediate source subfolder becomes one shortcut in the target folder."))
        source_card, self.source_field = self._path_field(
            "Source folder", "Folder containing one subfolder per app"
        )
        target_card, self.target_field = self._path_field(
            "Target folder", "Folder where shortcuts will be created"
        )
        layout.addWidget(source_card)
        layout.addWidget(target_card)
        actions = QHBoxLayout()
        back = self._outline_button("Back")
        back.clicked.connect(self._show_home)
        scan = self._primary_button("Scan folders")
        scan.clicked.connect(self._start_workflow)
        actions.addWidget(back)
        actions.addStretch()
        actions.addWidget(scan)
        layout.addLayout(actions)
        layout.addStretch()
        return page

    def _build_progress_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("02 / Processing"))
        layout.addWidget(self._title("Building your shortcut library."))
        self.progress_caption = self._body("Reading folders…")
        layout.addWidget(self.progress_caption)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 8, 0, 8)
        self.rows_layout.setSpacing(8)
        self.rows_layout.addStretch()
        scroll.setWidget(self.rows_container)
        layout.addWidget(scroll, 1)
        cancel = self._outline_button("Cancel")
        cancel.clicked.connect(self._cancel_workflow)
        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(cancel)
        layout.addLayout(controls)
        return page

    def _build_choice_page(self) -> QWidget:
        page, layout = self._page()
        layout.addWidget(self._eyebrow("Executable selection"))
        self.choice_title = self._title("Choose an executable.")
        layout.addWidget(self.choice_title)
        layout.addWidget(self._body("This folder contains more than one launch option. Select the executable or Windows shortcut you want to use."))
        self.candidate_list = QTreeWidget()
        self.candidate_list.setHeaderLabels(["Launch file", ""])
        self.candidate_list.setIconSize(QSize(40, 40))
        self.candidate_list.setRootIsDecorated(False)
        self.candidate_list.setUniformRowHeights(True)
        self.candidate_list.setColumnWidth(0, 610)
        self.candidate_list.itemDoubleClicked.connect(
            lambda _item, _column: self._submit_choice()
        )
        layout.addWidget(self.candidate_list, 1)
        actions = QHBoxLayout()
        cancel = self._outline_button("Cancel")
        cancel.clicked.connect(self._cancel_choice)
        open_source = self._outline_button("Open source folder")
        open_source.clicked.connect(self._open_choice_folder)
        self.choose_button = self._primary_button("Use selected")
        self.choose_button.clicked.connect(self._submit_choice)
        actions.addWidget(cancel)
        actions.addWidget(open_source)
        actions.addStretch()
        actions.addWidget(self.choose_button)
        layout.addLayout(actions)
        return page

    def _build_done_page(self) -> QWidget:
        page, layout = self._page()
        layout.addStretch()
        layout.addWidget(self._eyebrow("Complete"))
        layout.addWidget(self._title("Your shortcuts are ready."))
        self.done_summary = self._body("")
        layout.addWidget(self.done_summary)
        done = self._primary_button("Done")
        done.clicked.connect(self._reset_to_home)
        actions = QHBoxLayout()
        actions.addWidget(done)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch(2)
        return page

    def _browse_for_folder(self, field: QLineEdit, caption: str) -> None:
        initial = field.text().strip() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, f"Choose {caption}", initial)
        if selected:
            field.setText(selected)

    def _go_start(self) -> None:
        if self._workflow_active():
            return
        self.pages.setCurrentWidget(self.setup_page)

    def _show_home(self) -> None:
        if self._workflow_active():
            return
        self._refresh_home_dashboard()
        self.pages.setCurrentWidget(self.home_page)

    def _show_check_page(self) -> None:
        if self._workflow_active():
            return
        self._refresh_pair_cards(self.check_layout, for_check=True)
        self.pages.setCurrentWidget(self.check_page)

    def _show_list_page(self) -> None:
        if self._workflow_active():
            return
        self._refresh_pair_cards(self.list_layout, for_check=False)
        self.pages.setCurrentWidget(self.list_page)

    def _show_edit_page(self) -> None:
        if self._workflow_active():
            return
        self.current_edit_pair = None
        self._refresh_pair_cards(self.edit_pairs_layout, for_check=False, for_edit=True)
        self.pages.setCurrentWidget(self.edit_page)

    def _show_settings_page(self) -> None:
        if self._workflow_active():
            return
        self.open_target_setting.setChecked(
            self.database.get_setting_bool("open_target_after_completion")
        )
        self.confirm_delete_setting.setChecked(
            self.database.get_setting_bool("confirm_pair_deletion")
        )
        self.pages.setCurrentWidget(self.settings_page)

    def _workflow_active(self) -> bool:
        return bool(self.worker and self.worker.isRunning())

    def _refresh_pair_cards(
        self, layout: QVBoxLayout, for_check: bool, for_edit: bool = False
    ) -> None:
        self._clear_dynamic_layout(layout)
        pairs = self.database.list_pairs()
        if for_check and hasattr(self, "check_all_button"):
            self.check_all_button.setEnabled(bool(pairs))
        if not pairs:
            empty = QFrame()
            empty.setObjectName("card")
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(24, 24, 24, 24)
            empty_layout.addWidget(self._body("No saved folder pairs yet. Start a new run first."))
            layout.insertWidget(0, empty)
            return
        for pair in pairs:
            layout.insertWidget(
                layout.count() - 1, self._pair_card(pair, for_check, for_edit)
            )

    def _pair_card(self, pair: FolderPair, for_check: bool, for_edit: bool) -> QFrame:
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
            action = self._primary_button("Check")
            action.clicked.connect(lambda _checked=False, saved=pair: self._check_pair(saved))
        elif for_edit:
            action = self._primary_button("Choose")
            action.clicked.connect(lambda _checked=False, saved=pair: self._edit_pair(saved))
        else:
            action = self._outline_button("Delete")
            action.setObjectName("dangerButton")
            action.clicked.connect(lambda _checked=False, saved=pair: self._delete_pair(saved))
        layout.addWidget(action)
        return card

    def _check_pair(self, pair: FolderPair) -> None:
        if not pair.source.is_dir() or not pair.target.is_dir():
            QMessageBox.warning(
                self,
                "Folder unavailable",
                "The source or target folder no longer exists. Update the folders or delete this saved pair.",
            )
            return
        self._launch_workflow(pair.source, pair.target, pair.id, check_only=True)

    def _check_all_pairs(self) -> None:
        if self._workflow_active():
            return
        pairs = self.database.list_pairs()
        if not pairs:
            QMessageBox.information(
                self, "No saved libraries", "Start a new library before running a check."
            )
            return
        self.check_queue = [
            pair for pair in pairs if pair.source.is_dir() and pair.target.is_dir()
        ]
        self.batch_check_total = len(pairs)
        self.batch_check_completed = 0
        self.batch_check_unavailable = len(pairs) - len(self.check_queue)
        self.batch_check_totals = [0, 0, 0, 0, 0]
        if not self.check_queue:
            self._finish_batch_check()
            return
        self._launch_next_batch_check()

    def _launch_next_batch_check(self) -> None:
        pair = self.check_queue.pop(0)
        self._launch_workflow(pair.source, pair.target, pair.id, check_only=True)

    def _delete_pair(self, pair: FolderPair) -> None:
        confirmed = True
        if self.database.get_setting_bool("confirm_pair_deletion"):
            answer = QMessageBox.question(
                self,
                "Delete saved pair",
                "Delete this saved pair and its run history? Existing shortcuts and application files will not be deleted.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            confirmed = answer == QMessageBox.StandardButton.Yes
        if confirmed:
            self.database.delete_pair(pair.id)
            self._refresh_pair_cards(self.list_layout, for_check=False)

    def _edit_pair(self, pair: FolderPair) -> None:
        self.current_edit_pair = pair
        self.active_target = pair.target
        self.edit_detail_title.setText(pair.target.name or str(pair.target))
        self.edit_detail_caption.setText(
            f"Source: {pair.source}\nTarget: {pair.target}"
        )
        self._refresh_edit_items()
        self.pages.setCurrentWidget(self.edit_detail_page)

    def _refresh_edit_items(self) -> None:
        self._clear_dynamic_layout(self.edit_items_layout)
        if not self.current_edit_pair:
            return
        items = self.database.list_pair_items(self.current_edit_pair.id)
        if not items:
            empty = QFrame()
            empty.setObjectName("card")
            empty_layout = QVBoxLayout(empty)
            empty_layout.setContentsMargins(24, 24, 24, 24)
            empty_layout.addWidget(
                self._body("No saved shortcut selections are available for this pair.")
            )
            self.edit_items_layout.insertWidget(0, empty)
            return
        for pair_item in items:
            self.edit_items_layout.insertWidget(
                self.edit_items_layout.count() - 1,
                self._edit_item_card(pair_item),
            )

    def _edit_item_card(self, pair_item: PairItem) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        icon_source = pair_item.shortcut if pair_item.shortcut.exists() else pair_item.executable
        icon = self.icon_provider.icon(QFileInfo(str(icon_source)))
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
        edit_button = self._outline_button("Edit")
        edit_button.clicked.connect(
            lambda _checked=False, saved=pair_item: self._edit_pair_item(saved)
        )
        layout.addWidget(edit_button)
        return card

    def _edit_pair_item(self, pair_item: PairItem) -> None:
        if not pair_item.folder.is_dir():
            QMessageBox.warning(
                self, "Source folder unavailable", "This source subfolder no longer exists."
            )
            return
        candidates = find_executables(pair_item.folder)
        if not candidates:
            QMessageBox.warning(
                self, "No launch files", "No executable or executable-named shortcut was found."
            )
            return
        self._show_choice(
            str(pair_item.folder), [str(path) for path in candidates], context="edit"
        )

    def _open_current_target(self) -> None:
        if self.current_edit_pair:
            self._open_folder(self.current_edit_pair.target)

    def _open_database_folder(self) -> None:
        self._open_folder(self.database.path.parent)

    def _open_folder(self, folder: Path) -> None:
        if not folder.is_dir():
            QMessageBox.warning(self, "Folder unavailable", "This folder no longer exists.")
            return
        try:
            os.startfile(str(folder))
        except OSError as exc:
            QMessageBox.warning(self, "Could not open folder", str(exc))

    def _apply_settings(self) -> None:
        self.database.set_settings(
            {
                "open_target_after_completion": self.open_target_setting.isChecked(),
                "confirm_pair_deletion": self.confirm_delete_setting.isChecked(),
            }
        )
        QMessageBox.information(self, "Settings applied", "Your settings were saved.")

    def _export_data(self) -> None:
        default_path = str(Path.home() / "shortcut-studio-export.json")
        selected, _filter = QFileDialog.getSaveFileName(
            self, "Export Shortcut Studio data", default_path, "JSON files (*.json)"
        )
        if not selected:
            return
        try:
            Path(selected).write_text(
                json.dumps(self.database.export_data(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(self, "Export complete", "Pairs and settings were exported.")

    def _import_data(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self, "Import Shortcut Studio data", str(Path.home()), "JSON files (*.json)"
        )
        if not selected:
            return
        try:
            payload = json.loads(Path(selected).read_text(encoding="utf-8"))
            pair_count, item_count = self.database.import_data(payload)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return
        self._show_settings_page()
        QMessageBox.information(
            self,
            "Import complete",
            f"Imported {pair_count} pair(s) and {item_count} shortcut selection(s).",
        )

    def _start_workflow(self) -> None:
        source = Path(self.source_field.text().strip()).expanduser()
        target = Path(self.target_field.text().strip()).expanduser()
        if not source.is_dir():
            QMessageBox.warning(self, "Source folder", "Choose an existing source folder.")
            return
        if not target.is_dir():
            QMessageBox.warning(self, "Target folder", "Choose an existing target folder.")
            return
        if source.resolve() == target.resolve():
            QMessageBox.warning(self, "Folder selection", "Source and target folders must be different.")
            return

        source = source.resolve()
        target = target.resolve()
        pair, created = self.database.get_or_create_pair(source, target)
        self._launch_workflow(
            source, target, pair.id, check_only=not created
        )

    def _launch_workflow(
        self, source: Path, target: Path, pair_id: int, check_only: bool
    ) -> None:
        self._clear_folder_rows()
        self.progress_caption.setText("Reading folders…")
        self.progress_bar.setRange(0, 0)
        self.pages.setCurrentWidget(self.progress_page)
        self.worker = ScanWorker(
            source, target, self.database, pair_id, check_only=check_only
        )
        self.active_target = target
        for button in self.nav_buttons:
            button.setEnabled(False)
        self.worker.folders_ready.connect(self._folders_ready)
        self.worker.folder_started.connect(self._folder_started)
        self.worker.choice_required.connect(self._show_choice)
        self.worker.folder_finished.connect(self._folder_finished)
        self.worker.workflow_finished.connect(self._workflow_finished)
        self.worker.fatal_error.connect(self._fatal_error)
        self.worker.finished.connect(self._worker_stopped)
        self.worker.start()

    def _clear_folder_rows(self) -> None:
        self.folder_rows.clear()
        self._clear_dynamic_layout(self.rows_layout)

    @staticmethod
    def _clear_dynamic_layout(layout: QVBoxLayout) -> None:
        """Remove all dynamic widgets while preserving the final stretch item."""
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _folders_ready(self, paths: list[str]) -> None:
        for raw_path in paths:
            folder = Path(raw_path)
            row = FolderRow(folder)
            self.folder_rows[folder] = row
            self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        total = len(paths)
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(0)
        prefix = (
            f"Library {self.batch_check_completed + 1} of {self.batch_check_total}: "
            if self.batch_check_total
            else ""
        )
        self.progress_caption.setText(
            f"{prefix}{total} folder{'s' if total != 1 else ''} found."
        )

    def _folder_started(self, raw_path: str) -> None:
        folder = Path(raw_path)
        row = self.folder_rows.get(folder)
        if row:
            row.set_status("Scanning", BODY)
        self.progress_caption.setText(f"Scanning {folder.name}…")

    def _show_choice(
        self, raw_folder: str, raw_candidates: list[str], context: str = "workflow"
    ) -> None:
        folder = Path(raw_folder)
        self.choice_context = context
        self.current_choice_folder = folder
        self.current_candidates = [Path(path) for path in raw_candidates]
        self.choice_title.setText(f"Choose an executable for {folder.name}.")
        self.candidate_list.clear()
        for candidate in self.current_candidates:
            icon = self.icon_provider.icon(QFileInfo(str(candidate)))
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
            self.candidate_list.addTopLevelItem(item)
            test_button = self._outline_button("Test")
            test_button.clicked.connect(
                lambda _checked=False, path=candidate: self._test_executable(path)
            )
            self.candidate_list.setItemWidget(item, 1, test_button)
        if self.candidate_list.topLevelItemCount():
            self.candidate_list.setCurrentItem(self.candidate_list.topLevelItem(0))
        row = self.folder_rows.get(folder)
        if row:
            row.set_status("Needs choice", ORANGE)
        self.pages.setCurrentWidget(self.choice_page)

    def _submit_choice(self) -> None:
        index = self.candidate_list.indexOfTopLevelItem(
            self.candidate_list.currentItem()
        )
        if index < 0 or index >= len(self.current_candidates):
            QMessageBox.information(self, "Choose an executable", "Select an executable first.")
            return
        chosen = self.current_candidates[index]
        if self.choice_context == "edit":
            self._save_edited_choice(chosen)
            return
        self.pages.setCurrentWidget(self.progress_page)
        if self.current_choice_folder:
            row = self.folder_rows.get(self.current_choice_folder)
            if row:
                row.set_status("Creating", BODY)
        if self.worker:
            self.worker.choose(chosen)

    def _save_edited_choice(self, chosen: Path) -> None:
        if not self.current_edit_pair or not self.current_choice_folder:
            QMessageBox.warning(self, "Edit unavailable", "The saved pair is no longer available.")
            return
        destination = shortcut_path(
            self.current_edit_pair.target, self.current_choice_folder.name
        )
        try:
            install_launch_item(chosen, destination)
            self.database.save_pair_item(
                self.current_edit_pair.id,
                self.current_choice_folder,
                chosen,
                destination,
            )
            self.database.touch_pair(self.current_edit_pair.id)
        except OSError as exc:
            QMessageBox.critical(self, "Could not update shortcut", str(exc))
            return
        self._refresh_edit_items()
        self.pages.setCurrentWidget(self.edit_detail_page)

    def _cancel_choice(self) -> None:
        if self.choice_context == "edit":
            self.pages.setCurrentWidget(self.edit_detail_page)
        else:
            self._cancel_workflow()

    def _open_choice_folder(self) -> None:
        if self.current_choice_folder:
            self._open_folder(self.current_choice_folder)

    def _test_executable(self, executable: Path) -> None:
        if not executable.is_file():
            QMessageBox.warning(
                self, "Executable unavailable", "This executable no longer exists."
            )
            return
        try:
            os.startfile(str(executable))
        except OSError:
            QMessageBox.warning(
                self, "Could not open executable", f"Windows could not open {executable.name}."
            )

    def _folder_finished(self, result: FolderResult) -> None:
        row = self.folder_rows.get(result.folder)
        if row:
            if result.status == ResultStatus.CREATED:
                row.set_status("Created", GREEN)
                row.setToolTip(str(result.shortcut))
            elif result.status == ResultStatus.NO_EXECUTABLE:
                row.set_status("No app found", MUTED)
            elif result.status == ResultStatus.UP_TO_DATE:
                row.set_status("Up to date", GREEN)
            elif result.status == ResultStatus.REMOVED:
                row.set_status("Removed", ORANGE)
            else:
                row.set_status("Failed", RED)
                row.setToolTip(result.error or "Unknown error")
        completed = sum(
            1
            for current_row in self.folder_rows.values()
            if current_row.status_label.text()
            in {"CREATED", "NO APP FOUND", "UP TO DATE", "REMOVED", "FAILED"}
        )
        self.progress_bar.setValue(completed)
        self.progress_caption.setText(f"Processed {completed} of {len(self.folder_rows)} folders.")

    def _workflow_finished(
        self, created: int, skipped: int, failed: int, up_to_date: int, removed: int
    ) -> None:
        if self.batch_check_total:
            values = (created, skipped, failed, up_to_date, removed)
            self.batch_check_totals = [
                current + value
                for current, value in zip(self.batch_check_totals, values)
            ]
            self.batch_check_completed += 1
            return
        self.done_summary.setText(
            f"Created {created} shortcut{'s' if created != 1 else ''}. "
            f"{skipped} folder{'s' if skipped != 1 else ''} had no launch file. "
            f"{up_to_date} already up to date. "
            f"{removed} obsolete shortcut{'s' if removed != 1 else ''} removed. "
            f"{failed} failed."
        )
        self.pages.setCurrentWidget(self.done_page)
        if (
            self.active_target
            and self.database.get_setting_bool("open_target_after_completion")
        ):
            self._open_folder(self.active_target)

    def _fatal_error(self, message: str) -> None:
        if self.batch_check_total:
            self.batch_check_unavailable += 1
            return
        QMessageBox.critical(self, "Could not complete workflow", message)
        self.pages.setCurrentWidget(self.setup_page)

    def _worker_stopped(self) -> None:
        """Release the QThread only after its run method has fully returned."""
        finished_worker = self.sender()
        if finished_worker is self.worker:
            self.worker = None
            if self.batch_check_total:
                if self.check_queue:
                    self._launch_next_batch_check()
                    return
                self._finish_batch_check()
                return
            for button in self.nav_buttons:
                button.setEnabled(True)

    def _finish_batch_check(self) -> None:
        created, skipped, failed, up_to_date, removed = self.batch_check_totals
        unavailable = self.batch_check_unavailable
        self.done_summary.setText(
            f"Checked {self.batch_check_completed} of {self.batch_check_total} saved libraries. "
            f"Created {created} shortcut{'s' if created != 1 else ''}. "
            f"{skipped} folder{'s' if skipped != 1 else ''} had no launch file. "
            f"{up_to_date} already up to date. "
            f"{removed} obsolete shortcut{'s' if removed != 1 else ''} removed. "
            f"{failed} failed. "
            f"{unavailable} librar{'ies were' if unavailable != 1 else 'y was'} unavailable."
        )
        self.batch_check_total = 0
        self.batch_check_unavailable = 0
        self.batch_check_completed = 0
        self.check_queue.clear()
        for button in self.nav_buttons:
            button.setEnabled(True)
        self.pages.setCurrentWidget(self.done_page)

    def _cancel_workflow(self) -> None:
        self.check_queue.clear()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.progress_caption.setText("Cancelling…")
            self.pages.setCurrentWidget(self.progress_page)

    def _reset_to_home(self) -> None:
        self.source_field.clear()
        self.target_field.clear()
        self._show_home()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            if not self.worker.wait(3000):
                event.ignore()
                return
        event.accept()


STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Microsoft YaHei UI", "Yu Gothic UI", sans-serif;
    font-size: 14px;
    font-weight: 400;
}}
QMainWindow, QWidget {{ background: {CANVAS}; color: {WHITE}; }}
#header {{ border-bottom: 1px solid {HAIRLINE}; }}
#brand, #eyebrow {{
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    letter-spacing: 2px;
    color: {WHITE};
}}
#monoMuted {{
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
    letter-spacing: 1px;
    color: {MUTED};
}}
#title {{ font-size: 42px; letter-spacing: -1px; color: {WHITE}; }}
#dashboardTitle {{ font-size: 30px; letter-spacing: -0.6px; color: {WHITE}; }}
#dashboardCardTitle {{ font-size: 18px; color: {WHITE}; }}
#dashboardCardBody {{ font-size: 13px; color: {BODY}; }}
#metric {{ font-size: 28px; color: {WHITE}; }}
#homeRecent {{ font-size: 15px; color: {BODY}; }}
#body {{ font-size: 16px; line-height: 24px; color: {BODY}; }}
QPushButton {{
    background: transparent;
    color: {WHITE};
    border: 1px solid #45484e;
    border-radius: 18px;
    padding: 8px 18px;
    min-height: 18px;
}}
QPushButton:hover {{ border-color: #8b8e94; background: {SOFT}; }}
QPushButton:pressed {{ background: #2a2c31; }}
QPushButton:disabled {{ color: #55585e; border-color: {HAIRLINE}; }}
QPushButton#primaryButton {{ background: {WHITE}; color: {CANVAS}; border-color: {WHITE}; }}
QPushButton#primaryButton:hover {{ background: #e8e8e5; }}
QPushButton#navButton {{
    border: none;
    padding: 6px 10px;
    min-height: 16px;
}}
QPushButton#navButton:hover {{ background: {SOFT}; }}
QPushButton#dangerButton {{ color: {RED}; }}
QFrame#card, QFrame#folderRow, QFrame#dashboardCard {{
    background: {CARD};
    border: 1px solid {HAIRLINE};
    border-radius: 8px;
}}
QFrame#card QLabel, QFrame#card QCheckBox, QFrame#folderRow QLabel,
QFrame#dashboardCard QLabel {{ background: transparent; }}
QFrame#verticalDivider {{ background: {HAIRLINE}; border: none; }}
QLineEdit {{
    background: {SOFT};
    color: {WHITE};
    border: 1px solid {HAIRLINE};
    border-radius: 8px;
    padding: 11px 14px;
    selection-background-color: #4c4f55;
}}
QLineEdit:focus {{ border-color: #777b82; }}
QProgressBar {{ background: {SOFT}; border: none; border-radius: 3px; height: 6px; }}
QProgressBar::chunk {{ background: {WHITE}; border-radius: 3px; }}
QScrollArea {{ background: transparent; }}
QTreeWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QTreeWidget::item {{
    background: {CARD};
    border: 1px solid {HAIRLINE};
    padding: 10px 14px;
    color: {BODY};
}}
QTreeWidget::item:hover {{ border-color: #5a5e64; }}
QTreeWidget::item:selected {{ background: {SOFT}; border: 1px solid {WHITE}; color: {WHITE}; }}
QHeaderView::section {{
    background: {CANVAS};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {HAIRLINE};
    padding: 8px 12px;
    font-family: Consolas, monospace;
    font-size: 11px;
}}
#pairPath, #pairPathMuted {{
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
}}
#pairPathMuted {{ color: {MUTED}; }}
#itemTitle {{ font-size: 16px; color: {WHITE}; }}
QMessageBox {{ background: {CANVAS}; }}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    font = QFont("Segoe UI")
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    window = MainWindow()
    window.show()
    return app.exec()
