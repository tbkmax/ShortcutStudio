"""Scan worker and batch-check coordination for the desktop UI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox

from shortcut_studio.core.worker import ScanWorker
from shortcut_studio.models import FolderPair
from shortcut_studio.storage.database import Database

if TYPE_CHECKING:
    from shortcut_studio.ui.window import MainWindow


class WorkflowController(QObject):
    """Own worker lifetimes, check queues, and completed-run totals."""

    def __init__(self, window: MainWindow, database: Database) -> None:
        super().__init__(window)
        self.window = window
        self.database = database
        self.worker: ScanWorker | None = None
        self.check_queue: list[FolderPair] = []
        self.batch_check_total = 0
        self.batch_check_completed = 0
        self.batch_check_unavailable = 0
        self.batch_check_totals = [0, 0, 0, 0, 0]
        self.active_target: Path | None = None

    def is_active(self) -> bool:
        return bool(self.worker and self.worker.isRunning())

    def check_all_pairs(self) -> None:
        if self.is_active():
            return
        pairs = self.database.list_pairs()
        if not pairs:
            QMessageBox.information(
                self.window, "No saved libraries", "Start a new library before running a check."
            )
            return
        self.check_queue = [
            pair for pair in pairs if pair.source.is_dir() and pair.target.is_dir()
        ]
        self.batch_check_total = len(pairs)
        self.batch_check_completed = 0
        self.batch_check_unavailable = len(pairs) - len(self.check_queue)
        self.batch_check_totals = [0, 0, 0, 0, 0]
        if self.check_queue:
            self._launch_next_batch_check()
        else:
            self._finish_batch_check()

    def _launch_next_batch_check(self) -> None:
        pair = self.check_queue.pop(0)
        self.launch(pair.source, pair.target, pair.id, check_only=True)

    def start_from_fields(self) -> None:
        source = Path(self.window.source_field.text().strip()).expanduser()
        target = Path(self.window.target_field.text().strip()).expanduser()
        if not source.is_dir():
            QMessageBox.warning(self.window, "Source folder", "Choose an existing source folder.")
            return
        if not target.is_dir():
            QMessageBox.warning(self.window, "Target folder", "Choose an existing target folder.")
            return
        if source.resolve() == target.resolve():
            QMessageBox.warning(
                self.window, "Folder selection", "Source and target folders must be different."
            )
            return

        source = source.resolve()
        target = target.resolve()
        pair, created = self.database.get_or_create_pair(source, target)
        self.launch(source, target, pair.id, check_only=not created)

    def launch(self, source: Path, target: Path, pair_id: int, check_only: bool) -> None:
        self.window._clear_folder_rows()
        self.window.progress_caption.setText("Reading folders…")
        self.window.progress_bar.setRange(0, 0)
        self.window.pages.setCurrentWidget(self.window.progress_page)
        worker = ScanWorker(source, target, self.database, pair_id, check_only=check_only)
        self.worker = worker
        self.active_target = target
        for button in self.window.nav_buttons:
            button.setEnabled(False)
        worker.folders_ready.connect(self.window._folders_ready)
        worker.folder_started.connect(self.window._folder_started)
        worker.choice_required.connect(self.window._show_choice)
        worker.folder_finished.connect(self.window._folder_finished)
        worker.workflow_finished.connect(self._workflow_finished)
        worker.fatal_error.connect(self._fatal_error)
        worker.finished.connect(self._worker_stopped)
        worker.start()

    def _workflow_finished(
        self, created: int, skipped: int, failed: int, up_to_date: int, removed: int
    ) -> None:
        if self.batch_check_total:
            values = (created, skipped, failed, up_to_date, removed)
            self.batch_check_totals = [
                current + value for current, value in zip(self.batch_check_totals, values)
            ]
            self.batch_check_completed += 1
            return
        self.window.done_summary.setText(
            f"Created {created} shortcut{'s' if created != 1 else ''}. "
            f"{skipped} folder{'s' if skipped != 1 else ''} had no launch file. "
            f"{up_to_date} already up to date. "
            f"{removed} obsolete shortcut{'s' if removed != 1 else ''} removed. "
            f"{failed} failed."
        )
        self.window.pages.setCurrentWidget(self.window.done_page)
        if self.active_target and self.database.get_setting_bool(
            "open_target_after_completion"
        ):
            self.window._open_folder(self.active_target)

    def _fatal_error(self, message: str) -> None:
        if self.batch_check_total:
            self.batch_check_unavailable += 1
            return
        QMessageBox.critical(self.window, "Could not complete workflow", message)
        self.window.pages.setCurrentWidget(self.window.setup_page)

    def _worker_stopped(self) -> None:
        """Release the QThread only after its run method has fully returned."""
        if self.sender() is not self.worker:
            return
        self.worker = None
        if self.batch_check_total:
            if self.check_queue:
                self._launch_next_batch_check()
            else:
                self._finish_batch_check()
            return
        for button in self.window.nav_buttons:
            button.setEnabled(True)

    def _finish_batch_check(self) -> None:
        created, skipped, failed, up_to_date, removed = self.batch_check_totals
        unavailable = self.batch_check_unavailable
        self.window.done_summary.setText(
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
        for button in self.window.nav_buttons:
            button.setEnabled(True)
        self.window.pages.setCurrentWidget(self.window.done_page)

    def cancel(self) -> None:
        self.check_queue.clear()
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.window.progress_caption.setText("Cancelling…")
            self.window.pages.setCurrentWidget(self.window.progress_page)

    def stop_for_shutdown(self) -> bool:
        """Ask a running worker to stop, then wait at most three seconds."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            return bool(self.worker.wait(3000))
        return True
