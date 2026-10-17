from __future__ import annotations

import sqlite3
from pathlib import Path

from shortcut_studio.models import FolderPair, FolderResult, PairItem
from shortcut_studio.storage.backup import export_data, import_data
from shortcut_studio.storage.connection import ConnectionManager
from shortcut_studio.storage.repository import PairRepository, RunRepository, SettingsRepository
from shortcut_studio.storage.schema import DEFAULT_SETTINGS, create_tables, migrate_legacy_runs


class Database:
    """Unified storage facade for Shortcut Studio persistence."""

    def __init__(self, path: Path) -> None:
        self.manager = ConnectionManager(path)
        self.path = path
        self.pair_repo = PairRepository()
        self.run_repo = RunRepository()
        self.settings_repo = SettingsRepository()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return self.manager.connect()

    def _connection(self):
        return self.manager.connection()

    def _initialize(self) -> None:
        with self._connection() as connection:
            create_tables(connection)
            migrate_legacy_runs(connection)

    def _migrate_existing_runs(self, connection: sqlite3.Connection) -> None:
        migrate_legacy_runs(connection)

    def find_pair(self, source: Path, target: Path) -> FolderPair | None:
        with self._connection() as connection:
            return self.pair_repo.find_pair(connection, source, target)

    def get_or_create_pair(self, source: Path, target: Path) -> tuple[FolderPair, bool]:
        with self._connection() as connection:
            return self.pair_repo.get_or_create_pair(connection, source, target)

    def list_pairs(self) -> list[FolderPair]:
        with self._connection() as connection:
            return self.pair_repo.list_pairs(connection)

    def delete_pair(self, pair_id: int) -> None:
        with self._connection() as connection:
            self.pair_repo.delete_pair(connection, pair_id)

    def get_pair_executable(self, pair_id: int, folder: Path) -> Path | None:
        with self._connection() as connection:
            return self.pair_repo.get_pair_executable(connection, pair_id, folder)

    def list_pair_items(self, pair_id: int) -> list[PairItem]:
        with self._connection() as connection:
            return self.pair_repo.list_pair_items(connection, pair_id)

    def save_pair_item(
        self, pair_id: int, folder: Path, executable: Path, shortcut: Path
    ) -> None:
        with self._connection() as connection:
            self.pair_repo.save_pair_item(connection, pair_id, folder, executable, shortcut)

    def delete_pair_item(self, pair_id: int, folder: Path) -> None:
        with self._connection() as connection:
            self.pair_repo.delete_pair_item(connection, pair_id, folder)

    def touch_pair(self, pair_id: int) -> None:
        with self._connection() as connection:
            self.pair_repo.touch_pair(connection, pair_id)

    def get_setting_bool(self, key: str) -> bool:
        with self._connection() as connection:
            return self.settings_repo.get_setting_bool(connection, key)

    def set_settings(self, values: dict[str, bool]) -> None:
        with self._connection() as connection:
            self.settings_repo.set_settings(connection, values)

    def export_data(self) -> dict:
        with self._connection() as connection:
            return export_data(connection, self.pair_repo, self.settings_repo)

    def import_data(self, payload: dict) -> tuple[int, int]:
        with self._connection() as connection:
            return import_data(connection, payload)

    def start_run(self, source: Path, target: Path) -> int:
        with self._connection() as connection:
            return self.run_repo.start_run(connection, source, target)

    def save_result(self, run_id: int, result: FolderResult) -> None:
        with self._connection() as connection:
            self.run_repo.save_result(connection, run_id, result)

    def complete_run(self, run_id: int) -> None:
        with self._connection() as connection:
            self.run_repo.complete_run(connection, run_id)
