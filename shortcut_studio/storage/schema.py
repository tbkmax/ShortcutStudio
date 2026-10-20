from __future__ import annotations

import sqlite3
from pathlib import Path

from shortcut_studio.storage.connection import _path_key


DEFAULT_SETTINGS: dict[str, str] = {
    "open_target_after_completion": "false",
    "confirm_pair_deletion": "true",
    "minimize_to_tray_on_close": "true",
}


def create_tables(connection: sqlite3.Connection) -> None:
    """Create all required tables and populate default application settings if missing."""
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


def migrate_legacy_runs(connection: sqlite3.Connection) -> None:
    """Migrate historical run data into structured folder pairs and items."""
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
