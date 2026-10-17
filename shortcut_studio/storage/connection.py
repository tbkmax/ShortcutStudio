from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from shortcut_studio.models import FolderPair


def _now() -> str:
    """Return the current UTC timestamp formatted as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _path_key(path: Path) -> str:
    """Canonicalize a filesystem path for case-folded comparisons on Windows."""
    return os.path.normcase(os.path.abspath(str(path)))


def _pair_from_row(row: tuple | list) -> FolderPair:
    """Convert a database query row tuple into a FolderPair dataclass instance."""
    return FolderPair(int(row[0]), Path(row[1]), Path(row[2]), row[3], row[4])


class ConnectionManager:
    """Manages SQLite database file connections with foreign key constraints enabled."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled."""
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an active transactional connection."""
        conn = self.connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()
