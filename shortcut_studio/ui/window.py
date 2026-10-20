from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PyQt6.QtCore import QEvent, QFileInfo, QPoint, QRect, QSize, Qt
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
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from shortcut_studio.core.worker import ScanWorker
from shortcut_studio.core.shell_link import install_launch_item, shortcut_path
from shortcut_studio.models import FolderPair, FolderResult, PairItem, ResultStatus
from shortcut_studio.scanner import find_executables
from shortcut_studio.storage.database import Database
from shortcut_studio.ui.components import (
    FolderRow,
    back_row_layout,
    body_label,
    build_dashboard_action,
    build_edit_item_card,
    build_header,
    build_pair_card,
    eyebrow_label,
    outline_button,
    page_container,
    path_field_card,
    primary_button,
    title_label,
)
from shortcut_studio.ui.pages import (
    build_check_page,
    build_choice_page,
    build_done_page,
    build_edit_detail_page,
    build_edit_page,
    build_home_page,
    build_list_page,
    build_progress_page,
    build_settings_page,
    build_setup_page,
)
from shortcut_studio.ui.theme import (
    APP_NAME,
    BODY,
    GREEN,
    MUTED,
    ORANGE,
    RED,
    STYLESHEET,
)


RESIZE_MARGIN = 6
EDGE_NONE = 0
EDGE_LEFT = 1
EDGE_TOP = 2
EDGE_RIGHT = 4
EDGE_BOTTOM = 8


def _app_icon_path() -> Path:
    """Locate the runtime icon in source and PyInstaller one-file builds."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / "assest" / "icon.ico"


class MainWindow(QMainWindow):
    """Main desktop application window for Shortcut Studio."""

    def __init__(self, database_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(820, 620)
        self.resize(980, 720)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        icon_path = _app_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._resize_edge = EDGE_NONE
        self._drag_start_geom: QRect | None = None
        self._drag_start_pos: QPoint | None = None
        self._is_quitting = False

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
        shell.setObjectName("shell")
        shell.setMouseTracking(True)
        shell.installEventFilter(self)
        self.shell = shell

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._build_header())
        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
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
        self._setup_tray_icon()

    def _build_header(self) -> QWidget:
        return build_header(self)

    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        return page_container()

    def _eyebrow(self, text: str) -> QLabel:
        return eyebrow_label(text)

    def _title(self, text: str) -> QLabel:
        return title_label(text)

    def _body(self, text: str) -> QLabel:
        return body_label(text)

    def _outline_button(self, text: str) -> QPushButton:
        return outline_button(text)

    def _primary_button(self, text: str) -> QPushButton:
        return primary_button(text)

    def _path_field(self, label_text: str, hint: str) -> tuple[QWidget, QLineEdit]:
        return path_field_card(
            label_text, hint, lambda: self._browse_for_folder(field, label_text)
        ) if False else self._create_path_field(label_text, hint)

    def _create_path_field(self, label_text: str, hint: str) -> tuple[QWidget, QLineEdit]:
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

    def _back_row(self) -> QHBoxLayout:
        return back_row_layout(self._show_home)

    def _dashboard_action(
        self,
        title: str,
        description: str,
        button_text: str | None = None,
        handler=None,
        primary: bool = False,
        buttons: list[QPushButton] | None = None,
    ) -> QFrame:
        return build_dashboard_action(
            title, description, button_text, handler, primary, buttons
        )

    def _build_home_page(self) -> QWidget:
        return build_home_page(self)

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
        return build_check_page(self)

    def _build_list_page(self) -> QWidget:
        return build_list_page(self)

    def _build_edit_page(self) -> QWidget:
        return build_edit_page(self)

    def _build_edit_detail_page(self) -> QWidget:
        return build_edit_detail_page(self)

    def _build_settings_page(self) -> QWidget:
        return build_settings_page(self)

    def _build_setup_page(self) -> QWidget:
        return build_setup_page(self)

    def _build_progress_page(self) -> QWidget:
        return build_progress_page(self)

    def _build_choice_page(self) -> QWidget:
        return build_choice_page(self)

    def _build_done_page(self) -> QWidget:
        return build_done_page(self)

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
        return build_pair_card(
            pair,
            for_check,
            for_edit,
            on_check=self._check_pair,
            on_edit=self._edit_pair,
            on_delete=self._delete_pair,
        )

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
        return build_edit_item_card(
            pair_item, self.icon_provider, self._edit_pair_item
        )

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

    def _setup_tray_icon(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = _app_icon_path()
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = self.windowIcon()
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(APP_NAME)

        tray_menu = QMenu(self)
        self.tray_open_action = tray_menu.addAction(f"Open {APP_NAME}")
        open_font = self.tray_open_action.font()
        open_font.setBold(True)
        self.tray_open_action.setFont(open_font)
        self.tray_open_action.triggered.connect(self._restore_from_tray)

        self.tray_toggle_action = tray_menu.addAction("Hide to tool bar")
        self.tray_toggle_action.triggered.connect(self._toggle_hide_to_tray)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self._quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        if self.isHidden():
            self.show()
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        if hasattr(self, "tray_toggle_action"):
            self.tray_toggle_action.setText("Hide to tool bar")

    def _toggle_hide_to_tray(self) -> None:
        if self.isHidden():
            self._restore_from_tray()
        else:
            self._hide_to_tray()

    def _hide_to_tray(self) -> bool:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False
        if self.tray_icon.icon().isNull():
            self.tray_icon.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )
        if not self.tray_icon.isVisible():
            self.tray_icon.show()
        self.hide()
        if hasattr(self, "tray_toggle_action"):
            self.tray_toggle_action.setText(f"Show {APP_NAME}")
        return True

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _quit_application(self) -> None:
        self._is_quitting = True
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
        QApplication.instance().quit()

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            is_max = self.isMaximized()
            if hasattr(self, "max_button"):
                if hasattr(self.max_button, "set_icon_type"):
                    self.max_button.set_icon_type("restore" if is_max else "maximize")
                self.max_button.setToolTip("Restore" if is_max else "Maximize")
            if hasattr(self, "shell"):
                self.shell.setProperty("maximized", is_max)
                self.shell.style().unpolish(self.shell)
                self.shell.style().polish(self.shell)
            if hasattr(self, "header_widget"):
                self.header_widget.setProperty("maximized", is_max)
                self.header_widget.style().unpolish(self.header_widget)
                self.header_widget.style().polish(self.header_widget)
            if hasattr(self, "pages"):
                self.pages.setProperty("maximized", is_max)
                self.pages.style().unpolish(self.pages)
                self.pages.style().polish(self.pages)
        super().changeEvent(event)

    def _determine_edge(self, pos: QPoint) -> int:
        margin = RESIZE_MARGIN
        w, h = self.width(), self.height()
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
        if obj is getattr(self, "shell", None):
            event_type = event.type()
            if event_type == QEvent.Type.MouseMove:
                if self._resize_edge != EDGE_NONE:
                    diff = event.globalPosition().toPoint() - self._drag_start_pos
                    geom = QRect(self._drag_start_geom)
                    min_w, min_h = self.minimumWidth(), self.minimumHeight()

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

                    self.setGeometry(geom)
                    return True
                elif not self.isMaximized():
                    edge = self._determine_edge(event.position().toPoint())
                    if edge in (EDGE_LEFT, EDGE_RIGHT):
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    elif edge in (EDGE_TOP, EDGE_BOTTOM):
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    elif edge in (EDGE_LEFT | EDGE_TOP, EDGE_RIGHT | EDGE_BOTTOM):
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif edge in (EDGE_RIGHT | EDGE_TOP, EDGE_LEFT | EDGE_BOTTOM):
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    else:
                        self.unsetCursor()
            elif event_type == QEvent.Type.MouseButtonPress:
                if not self.isMaximized() and event.button() == Qt.MouseButton.LeftButton:
                    edge = self._determine_edge(event.position().toPoint())
                    if edge != EDGE_NONE:
                        self._resize_edge = edge
                        self._drag_start_geom = self.geometry()
                        self._drag_start_pos = event.globalPosition().toPoint()
                        return True
            elif event_type == QEvent.Type.MouseButtonRelease:
                if self._resize_edge != EDGE_NONE:
                    self._resize_edge = EDGE_NONE
                    self.unsetCursor()
                    return True
            elif event_type == QEvent.Type.Leave:
                if self._resize_edge == EDGE_NONE:
                    self.unsetCursor()
        return super().eventFilter(obj, event)

    def closeEvent(self, event: QCloseEvent) -> None:
        # Hide with a usable tray; otherwise close so the button never becomes a no-op.
        if not getattr(self, "_is_quitting", False):
            if self._hide_to_tray():
                event.ignore()
                # Show a one-time balloon hint so the user knows where to find the app.
                if not getattr(self, "_tray_hint_shown", False):
                    self._tray_hint_shown = True
                    self.tray_icon.showMessage(
                        APP_NAME,
                        "Shortcut Studio is still running. Click the tray icon to reopen it, "
                        "or right-click for options.",
                        QSystemTrayIcon.MessageIcon.Information,
                        4000,
                    )
                return
            self._is_quitting = True
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            if not self.worker.wait(3000):
                self._is_quitting = False
                event.ignore()
                return
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
        event.accept()
        QApplication.instance().quit()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    font = QFont("Segoe UI")
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    icon_path = _app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()
