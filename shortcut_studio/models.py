from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ResultStatus(str, Enum):
    CREATED = "created"
    UP_TO_DATE = "up_to_date"
    REMOVED = "removed"
    NO_EXECUTABLE = "no_executable"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class FolderResult:
    folder: Path
    status: ResultStatus
    executable: Path | None = None
    shortcut: Path | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class FolderPair:
    id: int
    source: Path
    target: Path
    created_at: str
    last_checked_at: str


@dataclass(frozen=True, slots=True)
class PairItem:
    folder: Path
    executable: Path
    shortcut: Path
    updated_at: str
