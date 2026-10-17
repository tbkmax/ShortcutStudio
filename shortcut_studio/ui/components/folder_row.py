from __future__ import annotations

from pathlib import Path
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy


class FolderRow(QFrame):
    """Visual row representation for a scanned folder item with status indicator."""

    def __init__(self, folder: Path) -> None:
        super().__init__()
        self.setObjectName("folderRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        self.name_label = QLabel(folder.name)
        self.name_label.setToolTip(str(folder))
        self.name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.status_label = QLabel("QUEUED")
        self.status_label.setObjectName("monoMuted")
        layout.addWidget(self.name_label)
        layout.addWidget(self.status_label)

    def set_status(self, text: str, color: str) -> None:
        self.status_label.setText(text.upper())
        self.status_label.setStyleSheet(
            f"font-family: Consolas; font-size: 12px; letter-spacing: 1px; color: {color};"
        )
