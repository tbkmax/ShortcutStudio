from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .models import FolderPair, FolderResult, PairItem


DEFAULT_SETTINGS = {
    "open_target_after_completion": "false",
    "confirm_pair_deletion": "true",
}


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY,
                    source_folder TEXT NOT NULL,
                    target_folder TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS folder_results (
                    id INTEGER PRIMARY KEY,
                    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    folder_name TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    executable_path TEXT,
                    shortcut_path TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS folder_pairs (
                    id INTEGER PRIMARY KEY,
                    source_folder TEXT NOT NULL,
                    target_folder TEXT NOT NULL,
                    source_key TEXT NOT NULL,
                    target_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_checked_at TEXT NOT NULL,
                    UNIQUE(source_key, target_key)
                );
                CREATE TABLE IF NOT EXISTS pair_items (
                    id INTEGER PRIMARY KEY,
                    pair_id INTEGER NOT NULL REFERENCES folder_pairs(id) ON DELETE CASCADE,
                    folder_path TEXT NOT NULL,
                    folder_key TEXT NOT NULL,
                    executable_path TEXT NOT NULL,
                    shortcut_path TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(pair_id, folder_key)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            connection.executemany(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                DEFAULT_SETTINGS.items(),
            )
            self._migrate_existing_runs(connection)

    def _migrate_existing_runs(self, connection: sqlite3.Connection) -> None:
        legacy_pairs = connection.execute(
            """
            SELECT source_folder, target_folder, MIN(started_at),
                   MAX(COALESCE(completed_at, started_at))
            FROM runs GROUP BY source_folder, target_folder
            """
        ).fetchall()
        for source_text, target_text, created_at, checked_at in legacy_pairs:
            source = Path(source_text)
            target = Path(target_text)
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO folder_pairs(
                    source_folder, target_folder, source_key, target_key,
                    created_at, last_checked_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_text,
                    target_text,
                    _path_key(source),
                    _path_key(target),
                    created_at,
                    checked_at,
                ),
            )
            if inserted.rowcount == 0:
                continue
            pair_row = connection.execute(
                "SELECT id FROM folder_pairs WHERE source_key = ? AND target_key = ?",
                (_path_key(source), _path_key(target)),
            ).fetchone()
            if not pair_row:
                continue
            successful_items = connection.execute(
                """
                SELECT fr.folder_path, fr.executable_path, fr.shortcut_path,
                       fr.created_at
                FROM folder_results fr
                JOIN runs r ON r.id = fr.run_id
                WHERE r.source_folder = ? AND r.target_folder = ?
                  AND fr.status = 'created'
                  AND fr.executable_path IS NOT NULL
                  AND fr.shortcut_path IS NOT NULL
                ORDER BY fr.id
                """,
                (source_text, target_text),
            ).fetchall()
            for folder_path, executable_path, shortcut_file, updated_at in successful_items:
                connection.execute(
                    """
                    INSERT INTO pair_items(
                        pair_id, folder_path, folder_key, executable_path,
                        shortcut_path, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pair_id, folder_key) DO UPDATE SET
                        executable_path = excluded.executable_path,
                        shortcut_path = excluded.shortcut_path,
                        updated_at = excluded.updated_at
                    """,
                    (
                        int(pair_row[0]),
                        folder_path,
                        _path_key(Path(folder_path)),
                        executable_path,
                        shortcut_file,
                        updated_at,
                    ),
                )

    def find_pair(self, source: Path, target: Path) -> FolderPair | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id, source_folder, target_folder, created_at, last_checked_at
                FROM folder_pairs WHERE source_key = ? AND target_key = ?
                """,
                (_path_key(source), _path_key(target)),
            ).fetchone()
        return _pair_from_row(row) if row else None

    def get_or_create_pair(self, source: Path, target: Path) -> tuple[FolderPair, bool]:
        existing = self.find_pair(source, target)
        if existing:
            return existing, False
        now = _now()
        try:
            with self._connection() as connection:
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
            concurrent = self.find_pair(source, target)
            if concurrent is None:
                raise
            return concurrent, False
        return FolderPair(pair_id, source, target, now, now), True

    def list_pairs(self) -> list[FolderPair]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, source_folder, target_folder, created_at, last_checked_at
                FROM folder_pairs ORDER BY last_checked_at DESC, id DESC
                """
            ).fetchall()
        return [_pair_from_row(row) for row in rows]

    def delete_pair(self, pair_id: int) -> None:
        with self._connection() as connection:
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

    def get_pair_executable(self, pair_id: int, folder: Path) -> Path | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT executable_path FROM pair_items
                WHERE pair_id = ? AND folder_key = ?
                """,
                (pair_id, _path_key(folder)),
            ).fetchone()
        return Path(row[0]) if row else None

    def list_pair_items(self, pair_id: int) -> list[PairItem]:
        with self._connection() as connection:
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
        self, pair_id: int, folder: Path, executable: Path, shortcut: Path
    ) -> None:
        with self._connection() as connection:
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

    def delete_pair_item(self, pair_id: int, folder: Path) -> None:
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM pair_items WHERE pair_id = ? AND folder_key = ?",
                (pair_id, _path_key(folder)),
            )

    def touch_pair(self, pair_id: int) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE folder_pairs SET last_checked_at = ? WHERE id = ?",
                (_now(), pair_id),
            )

    def get_setting_bool(self, key: str) -> bool:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        value = row[0] if row else DEFAULT_SETTINGS.get(key, "false")
        return value.casefold() in {"1", "true", "yes", "on"}

    def set_settings(self, values: dict[str, bool]) -> None:
        with self._connection() as connection:
            connection.executemany(
                """
                INSERT INTO settings(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                [(key, "true" if value else "false") for key, value in values.items()],
            )

    def export_data(self) -> dict:
        pairs = []
        for pair in self.list_pairs():
            pairs.append(
                {
                    "source_folder": str(pair.source),
                    "target_folder": str(pair.target),
                    "created_at": pair.created_at,
                    "last_checked_at": pair.last_checked_at,
                    "items": [
                        {
                            "folder_path": str(item.folder),
                            "executable_path": str(item.executable),
                            "shortcut_path": str(item.shortcut),
                            "updated_at": item.updated_at,
                        }
                        for item in self.list_pair_items(pair.id)
                    ],
                }
            )
        with self._connection() as connection:
            settings = dict(connection.execute("SELECT key, value FROM settings"))
        return {"format": "shortcut-studio", "version": 1, "pairs": pairs, "settings": settings}

    def import_data(self, payload: dict) -> tuple[int, int]:
        if payload.get("format") != "shortcut-studio" or payload.get("version") != 1:
            raise ValueError("This is not a supported Shortcut Studio export file")
        pairs = payload.get("pairs")
        if not isinstance(pairs, list):
            raise ValueError("The export file does not contain a valid pair list")
        imported_pairs = imported_items = 0
        with self._connection() as connection:
            for entry in pairs:
                if not isinstance(entry, dict):
                    raise ValueError("A folder pair entry is invalid")
                source_text = entry.get("source_folder")
                target_text = entry.get("target_folder")
                if not isinstance(source_text, str) or not isinstance(target_text, str):
                    raise ValueError("A folder pair is missing its source or target path")
                source = Path(source_text)
                target = Path(target_text)
                created_at = str(entry.get("created_at") or _now())
                checked_at = str(entry.get("last_checked_at") or created_at)
                connection.execute(
                    """
                    INSERT INTO folder_pairs(
                        source_folder, target_folder, source_key, target_key,
                        created_at, last_checked_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_key, target_key) DO UPDATE SET
                        source_folder = excluded.source_folder,
                        target_folder = excluded.target_folder,
                        last_checked_at = excluded.last_checked_at
                    """,
                    (
                        source_text,
                        target_text,
                        _path_key(source),
                        _path_key(target),
                        created_at,
                        checked_at,
                    ),
                )
                pair_id = int(
                    connection.execute(
                        "SELECT id FROM folder_pairs WHERE source_key = ? AND target_key = ?",
                        (_path_key(source), _path_key(target)),
                    ).fetchone()[0]
                )
                imported_pairs += 1
                items = entry.get("items", [])
                if not isinstance(items, list):
                    raise ValueError("A folder pair contains an invalid item list")
                for item in items:
                    if not isinstance(item, dict):
                        raise ValueError("A shortcut item is invalid")
                    required = ("folder_path", "executable_path", "shortcut_path")
                    if not all(isinstance(item.get(key), str) for key in required):
                        raise ValueError("A shortcut item is missing path information")
                    folder_path = item["folder_path"]
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
                            folder_path,
                            _path_key(Path(folder_path)),
                            item["executable_path"],
                            item["shortcut_path"],
                            str(item.get("updated_at") or _now()),
                        ),
                    )
                    imported_items += 1
            settings = payload.get("settings", {})
            if isinstance(settings, dict):
                for key in DEFAULT_SETTINGS:
                    if key in settings:
                        raw_value = str(settings[key]).casefold()
                        value = "true" if raw_value in {"1", "true", "yes", "on"} else "false"
                        connection.execute(
                            """
                            INSERT INTO settings(key, value) VALUES (?, ?)
                            ON CONFLICT(key) DO UPDATE SET value = excluded.value
                            """,
                            (key, value),
                        )
        return imported_pairs, imported_items

    def start_run(self, source: Path, target: Path) -> int:
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO runs(source_folder, target_folder, started_at) VALUES (?, ?, ?)",
                (str(source), str(target), _now()),
            )
            return int(cursor.lastrowid)

    def save_result(self, run_id: int, result: FolderResult) -> None:
        with self._connection() as connection:
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

    def complete_run(self, run_id: int) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE runs SET completed_at = ? WHERE id = ?", (_now(), run_id)
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _pair_from_row(row) -> FolderPair:
    return FolderPair(int(row[0]), Path(row[1]), Path(row[2]), row[3], row[4])
