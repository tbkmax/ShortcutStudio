from __future__ import annotations

import threading
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from shortcut_studio.database import Database
from shortcut_studio.models import FolderResult, ResultStatus
from shortcut_studio.scanner import find_executables, source_folders
from shortcut_studio.core.shell_link import install_launch_item, shortcut_path


class ScanWorker(QThread):
    folders_ready = pyqtSignal(list)
    folder_started = pyqtSignal(str)
    choice_required = pyqtSignal(str, list)
    folder_finished = pyqtSignal(object)
    workflow_finished = pyqtSignal(int, int, int, int, int)
    fatal_error = pyqtSignal(str)

    def __init__(
        self,
        source: Path,
        target: Path,
        database: Database,
        pair_id: int,
        check_only: bool = False,
    ) -> None:
        super().__init__()
        self.source = source
        self.target = target
        self.database = database
        self.pair_id = pair_id
        self.check_only = check_only
        self._condition = threading.Condition()
        self._choice: Path | None = None
        self._cancelled = False

    def choose(self, executable: Path) -> None:
        with self._condition:
            self._choice = executable
            self._condition.notify_all()

    def cancel(self) -> None:
        with self._condition:
            self._cancelled = True
            self._condition.notify_all()

    def run(self) -> None:
        try:
            folders = source_folders(self.source)
            stale_items = (
                [
                    item
                    for item in self.database.list_pair_items(self.pair_id)
                    if not item.folder.is_dir()
                ]
                if self.check_only
                else []
            )
            displayed_folders = folders + [item.folder for item in stale_items]
            self.folders_ready.emit([str(folder) for folder in displayed_folders])
            run_id = self.database.start_run(self.source, self.target)
        except Exception as exc:
            self.fatal_error.emit(str(exc))
            return

        created = skipped = failed = up_to_date = removed = 0
        for item in stale_items:
            if self._cancelled:
                break
            self.folder_started.emit(str(item.folder))
            try:
                expected_shortcut = shortcut_path(self.target, item.folder.name)
                if item.shortcut.resolve(strict=False) != expected_shortcut.resolve(
                    strict=False
                ):
                    raise OSError(
                        "Saved shortcut is outside its expected target location"
                    )
                if item.shortcut.exists() or item.shortcut.is_symlink():
                    item.shortcut.unlink()
                self.database.delete_pair_item(self.pair_id, item.folder)
                result = FolderResult(
                    item.folder,
                    ResultStatus.REMOVED,
                    item.executable,
                    item.shortcut,
                )
                removed += 1
            except Exception as exc:
                result = FolderResult(
                    item.folder,
                    ResultStatus.FAILED,
                    item.executable,
                    item.shortcut,
                    str(exc),
                )
                failed += 1
            self.database.save_result(run_id, result)
            self.folder_finished.emit(result)

        for folder in folders:
            if self._cancelled:
                break
            self.folder_started.emit(str(folder))
            try:
                destination = shortcut_path(self.target, folder.name)
                saved_executable = (
                    self.database.get_pair_executable(self.pair_id, folder)
                    if self.check_only
                    else None
                )
                if saved_executable and destination.exists():
                    result = FolderResult(
                        folder,
                        ResultStatus.UP_TO_DATE,
                        saved_executable,
                        destination,
                    )
                    up_to_date += 1
                else:
                    chosen = (
                        saved_executable
                        if saved_executable and saved_executable.is_file()
                        else self._choose_executable(folder)
                    )
                    if chosen is None:
                        if self._cancelled:
                            break
                        result = FolderResult(folder, ResultStatus.NO_EXECUTABLE)
                        skipped += 1
                    else:
                        install_launch_item(chosen, destination)
                        self.database.save_pair_item(
                            self.pair_id, folder, chosen, destination
                        )
                        result = FolderResult(
                            folder, ResultStatus.CREATED, chosen, destination
                        )
                        created += 1
            except Exception as exc:
                result = FolderResult(folder, ResultStatus.FAILED, error=str(exc))
                failed += 1
            self.database.save_result(run_id, result)
            self.folder_finished.emit(result)

        try:
            self.database.complete_run(run_id)
            self.database.touch_pair(self.pair_id)
        except Exception as exc:
            self.fatal_error.emit(f"Could not finish database record: {exc}")
            return
        self.workflow_finished.emit(created, skipped, failed, up_to_date, removed)

    def _choose_executable(self, folder: Path) -> Path | None:
        executables = find_executables(folder)
        if not executables:
            return None
        if len(executables) == 1:
            return executables[0]
        with self._condition:
            self._choice = None
            self.choice_required.emit(
                str(folder), [str(path) for path in executables]
            )
            self._condition.wait_for(
                lambda: self._choice is not None or self._cancelled
            )
            return None if self._cancelled else self._choice
