from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from shortcut_studio.storage.connection import _now, _path_key
from shortcut_studio.storage.schema import DEFAULT_SETTINGS

if TYPE_CHECKING:
    from shortcut_studio.storage.repository import PairRepository, SettingsRepository


def export_data(
    connection: sqlite3.Connection,
    pair_repo: PairRepository,
    settings_repo: SettingsRepository,
) -> dict:
    """Export all saved folder pairs, pair items, and settings into a JSON-serializable dictionary."""
    pairs = []
    for pair in pair_repo.list_pairs(connection):
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
                    for item in pair_repo.list_pair_items(connection, pair.id)
                ],
            }
        )
    settings = settings_repo.get_all_settings(connection)
    return {"format": "shortcut-studio", "version": 1, "pairs": pairs, "settings": settings}


def import_data(connection: sqlite3.Connection, payload: dict) -> tuple[int, int]:
    """Validate and restore folder pairs, pair items, and settings from an export payload."""
    if payload.get("format") != "shortcut-studio" or payload.get("version") != 1:
        raise ValueError("This is not a supported Shortcut Studio export file")
    pairs = payload.get("pairs")
    if not isinstance(pairs, list):
        raise ValueError("The export file does not contain a valid pair list")
    imported_pairs = imported_items = 0
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
