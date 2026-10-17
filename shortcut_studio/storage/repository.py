from __future__ import annotations

import sqlite3
from pathlib import Path

from shortcut_studio.models import FolderPair, FolderResult, PairItem
from shortcut_studio.storage.connection import _now, _path_key, _pair_from_row
from shortcut_studio.storage.schema import DEFAULT_SETTINGS


class PairRepository:
    """Data access repository for folder pairs and associated shortcut pair items."""

    def find_pair(self, connection: sqlite3.Connection, source: Path, target: Path) -> FolderPair | None:
        row = connection.execute(
            """
            SELECT id, source_folder, target_folder, created_at, last_checked_at
            FROM folder_pairs WHERE source_key = ? AND target_key = ?
            """,
            (_path_key(source), _path_key(target)),
        ).fetchone()
        return _pair_from_row(row) if row else None

    def get_or_create_pair(
        self, connection: sqlite3.Connection, source: Path, target: Path
    ) -> tuple[FolderPair, bool]:
        existing = self.find_pair(connection, source, target)
        if existing:
            return existing, False
        now = _now()
        try:
            cursor = connection.execute(
                """
                INSERT INTO folder_pairs(
                    source_folder, target_folder, source_key, target_key,
                    created_at, last_checked_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(source),
                    str(target),
                    _path_key(source),
                    _path_key(target),
                    now,
                    now,
                ),
            )
            pair_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            concurrent = self.find_pair(connection, source, target)
            if concurrent is None:
                raise
            return concurrent, False
        return FolderPair(pair_id, source, target, now, now), True

    def list_pairs(self, connection: sqlite3.Connection) -> list[FolderPair]:
        rows = connection.execute(
            """
            SELECT id, source_folder, target_folder, created_at, last_checked_at
            FROM folder_pairs ORDER BY last_checked_at DESC, id DESC
            """
        ).fetchall()
        return [_pair_from_row(row) for row in rows]

    def delete_pair(self, connection: sqlite3.Connection, pair_id: int) -> None:
        row = connection.execute(
            "SELECT source_folder, target_folder FROM folder_pairs WHERE id = ?",
            (pair_id,),
        ).fetchone()
        if not row:
            return
        connection.execute(
            "DELETE FROM runs WHERE source_folder = ? AND target_folder = ?", row
        )
        connection.execute("DELETE FROM folder_pairs WHERE id = ?", (pair_id,))

    def get_pair_executable(
        self, connection: sqlite3.Connection, pair_id: int, folder: Path
    ) -> Path | None:
        row = connection.execute(
            """
            SELECT executable_path FROM pair_items
            WHERE pair_id = ? AND folder_key = ?
            """,
            (pair_id, _path_key(folder)),
        ).fetchone()
        return Path(row[0]) if row else None

    def list_pair_items(
        self, connection: sqlite3.Connection, pair_id: int
    ) -> list[PairItem]:
        rows = connection.execute(
            """
            SELECT folder_path, executable_path, shortcut_path, updated_at
            FROM pair_items WHERE pair_id = ? ORDER BY folder_path COLLATE NOCASE
            """,
            (pair_id,),
        ).fetchall()
        return [
            PairItem(Path(row[0]), Path(row[1]), Path(row[2]), row[3])
            for row in rows
        ]

    def save_pair_item(
        self,
        connection: sqlite3.Connection,
        pair_id: int,
        folder: Path,
        executable: Path,
        shortcut: Path,
    ) -> None:
        connection.execute(
            """
            INSERT INTO pair_items(
                pair_id, folder_path, folder_key, executable_path,
                shortcut_path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(pair_id, folder_key) DO UPDATE SET
                folder_path = excluded.folder_path,
                executable_path = excluded.executable_path,
                shortcut_path = excluded.shortcut_path,
                updated_at = excluded.updated_at
            """,
            (
                pair_id,
                str(folder),
                _path_key(folder),
                str(executable),
                str(shortcut),
                _now(),
            ),
        )

    def delete_pair_item(
        self, connection: sqlite3.Connection, pair_id: int, folder: Path
    ) -> None:
        connection.execute(
            "DELETE FROM pair_items WHERE pair_id = ? AND folder_key = ?",
            (pair_id, _path_key(folder)),
        )

    def touch_pair(self, connection: sqlite3.Connection, pair_id: int) -> None:
        connection.execute(
            "UPDATE folder_pairs SET last_checked_at = ? WHERE id = ?",
            (_now(), pair_id),
        )


class RunRepository:
    """Data access repository for execution runs and folder results."""

    def start_run(
        self, connection: sqlite3.Connection, source: Path, target: Path
    ) -> int:
        cursor = connection.execute(
            "INSERT INTO runs(source_folder, target_folder, started_at) VALUES (?, ?, ?)",
            (str(source), str(target), _now()),
        )
        return int(cursor.lastrowid)

    def save_result(
        self, connection: sqlite3.Connection, run_id: int, result: FolderResult
    ) -> None:
        connection.execute(
            """
            INSERT INTO folder_results(
                run_id, folder_name, folder_path, executable_path,
                shortcut_path, status, error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                result.folder.name,
                str(result.folder),
                str(result.executable) if result.executable else None,
                str(result.shortcut) if result.shortcut else None,
                result.status.value,
                result.error,
                _now(),
            ),
        )

    def complete_run(self, connection: sqlite3.Connection, run_id: int) -> None:
        connection.execute(
            "UPDATE runs SET completed_at = ? WHERE id = ?", (_now(), run_id)
        )


class SettingsRepository:
    """Data access repository for key-value configuration settings."""

    def get_setting_bool(self, connection: sqlite3.Connection, key: str) -> bool:
        row = connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        value = row[0] if row else DEFAULT_SETTINGS.get(key, "false")
        return value.casefold() in {"1", "true", "yes", "on"}

    def set_settings(
        self, connection: sqlite3.Connection, values: dict[str, bool]
    ) -> None:
        connection.executemany(
            """
            INSERT INTO settings(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            [(key, "true" if value else "false") for key, value in values.items()],
        )

    def get_all_settings(self, connection: sqlite3.Connection) -> dict[str, str]:
        return dict(connection.execute("SELECT key, value FROM settings"))
