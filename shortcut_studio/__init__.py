from __future__ import annotations

"""Shortcut Studio application package."""

__version__ = "1.0.0"

from shortcut_studio.models import FolderPair, FolderResult, PairItem, ResultStatus

__all__ = [
    "__version__",
    "FolderPair",
    "FolderResult",
    "PairItem",
    "ResultStatus",
]
