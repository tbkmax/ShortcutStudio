"""Behavior checks for the window's composed UI controllers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton

from shortcut_studio.app import MainWindow
from shortcut_studio.database import Database
from shortcut_studio.ui.frameless import EDGE_BOTTOM, EDGE_NONE, EDGE_RIGHT


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.database = Database(self.root / "ui.db")
        self.window = MainWindow(database=self.database)
        self.addCleanup(self.dispose_window)
        self.source = self.root / "source"
        self.folder = self.source / "Game"
        self.folder.mkdir(parents=True)
        self.target = self.root / "shortcuts"
        self.target.mkdir()
        self.pair, _ = self.database.get_or_create_pair(self.source, self.target)
        self.original = self.folder / "old.exe.lnk"
        self.original.write_bytes(b"original launch settings")
        self.replacement = self.folder / "new.exe.lnk"
        self.replacement.write_bytes(b"replacement launch settings")
        self.destination = self.target / "Game.lnk"
        self.destination.write_bytes(self.original.read_bytes())
        self.database.save_pair_item(
            self.pair.id, self.folder, self.original, self.destination
        )

    def dispose_window(self) -> None:
        # Tests use only a mock worker; never leave it attached during Qt cleanup.
        self.window.workflow.worker = None
        self.window.tray.hide_icon()
        self.window.hide()
        self.window.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def select_replacement(self) -> None:
        self.window._edit_pair(self.pair)
        item = self.database.list_pair_items(self.pair.id)[0]
        self.window._edit_pair_item(item)
        index = self.window.selection.candidates.index(self.replacement)
        self.window.candidate_list.setCurrentItem(
            self.window.candidate_list.topLevelItem(index)
        )

    def test_edit_selection_updates_shortcut_and_saved_item(self) -> None:
        self.select_replacement()
        self.assertEqual(self.window.library.current_pair, self.pair)
        self.window.choose_button.click()
        saved = self.database.list_pair_items(self.pair.id)[0]
        self.assertEqual(saved.executable, self.replacement)
        self.assertEqual(saved.shortcut, self.destination)
        self.assertEqual(self.destination.read_bytes(), self.replacement.read_bytes())
        self.assertIs(self.window.pages.currentWidget(), self.window.edit_detail_page)

    def test_failed_edit_preserves_saved_choice_and_selection_page(self) -> None:
        self.select_replacement()
        with (
            patch("shortcut_studio.ui.library.install_launch_item", side_effect=OSError("denied")),
            patch("shortcut_studio.ui.library.QMessageBox.critical") as error,
        ):
            self.window.choose_button.click()
        error.assert_called_once()
        self.assertEqual(self.database.list_pair_items(self.pair.id)[0].executable, self.original)
        self.assertEqual(self.destination.read_bytes(), self.original.read_bytes())
        self.assertIs(self.window.pages.currentWidget(), self.window.choice_page)

    def test_delete_confirmation_preserves_files(self) -> None:
        with patch("shortcut_studio.ui.library.QMessageBox.question", return_value=QMessageBox.StandardButton.Cancel):
            self.window._delete_pair(self.pair)
        self.assertEqual(len(self.database.list_pairs()), 1)
        with patch("shortcut_studio.ui.library.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes):
            self.window._delete_pair(self.pair)
        self.assertEqual(self.database.list_pairs(), [])
        self.assertTrue(self.original.is_file())
        self.assertTrue(self.destination.is_file())

    def test_workflow_choice_resumes_worker_and_cancel_clears_queue(self) -> None:
        worker = Mock()
        worker.isRunning.return_value = True
        self.window.workflow.worker = worker
        self.window._show_choice(str(self.folder), [str(self.replacement)])
        self.window.choose_button.click()
        worker.choose.assert_called_once_with(self.replacement)
        self.assertIs(self.window.pages.currentWidget(), self.window.progress_page)
        self.window.workflow.check_queue = [self.pair]
        self.window._cancel_choice()
        worker.cancel.assert_called_once_with()
        self.assertEqual(self.window.workflow.check_queue, [])

    def test_cancel_edit_does_not_cancel_worker_or_change_saved_choice(self) -> None:
        self.select_replacement()
        with patch.object(self.window.workflow, "cancel") as cancel:
            self.window._cancel_choice()
        cancel.assert_not_called()
        self.assertEqual(self.database.list_pair_items(self.pair.id)[0].executable, self.original)
        self.assertIs(self.window.pages.currentWidget(), self.window.edit_detail_page)

    def test_settings_backup_round_trip_updates_controls(self) -> None:
        backup = self.root / "backup.json"
        self.window._show_settings_page()
        self.window.open_target_setting.setChecked(True)
        self.window.confirm_delete_setting.setChecked(False)
        with patch("shortcut_studio.ui.settings.QMessageBox.information"):
            self.window._apply_settings()
            with patch("shortcut_studio.ui.settings.QFileDialog.getSaveFileName", return_value=(str(backup), "")):
                self.window._export_data()
            self.assertEqual(json.loads(backup.read_text(encoding="utf-8"))["format"], "shortcut-studio")
            self.database.delete_pair(self.pair.id)
            self.database.set_settings({"open_target_after_completion": False})
            with patch("shortcut_studio.ui.settings.QFileDialog.getOpenFileName", return_value=(str(backup), "")):
                self.window._import_data()
        self.assertEqual(len(self.database.list_pairs()), 1)
        self.assertTrue(self.window.open_target_setting.isChecked())
        self.assertFalse(self.window.confirm_delete_setting.isChecked())
        self.assertIs(self.window.pages.currentWidget(), self.window.settings_page)

    def test_invalid_backup_reports_error_without_changing_data(self) -> None:
        backup = self.root / "invalid.json"
        backup.write_text("not json", encoding="utf-8")
        before = self.database.export_data()
        with (
            patch("shortcut_studio.ui.settings.QFileDialog.getOpenFileName", return_value=(str(backup), "")),
            patch("shortcut_studio.ui.settings.QMessageBox.critical") as error,
        ):
            self.window._import_data()
        error.assert_called_once()
        self.assertEqual(self.database.export_data(), before)

    def test_resize_filter_handles_drag_and_releases_gesture(self) -> None:
        self.window.show()
        self.app.processEvents()
        initial_width = self.window.width()
        local = QPoint(self.window.width() - 1, self.window.height() // 2)
        global_pos = self.window.shell.mapToGlobal(local)
        for kind, delta, button, buttons in (
            (QEvent.Type.MouseButtonPress, 0, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton),
            (QEvent.Type.MouseMove, 40, Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton),
            (QEvent.Type.MouseButtonRelease, 40, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton),
        ):
            event = QMouseEvent(
                kind, QPointF(local + QPoint(delta, 0)),
                QPointF(global_pos + QPoint(delta, 0)), button, buttons,
                Qt.KeyboardModifier.NoModifier,
            )
            QApplication.sendEvent(self.window.shell, event)
        self.assertEqual(self.window.width(), initial_width + 40)
        self.assertEqual(self.window.chrome._resize_edge, EDGE_NONE)
        self.assertEqual(
            self.window.chrome.determine_edge(QPoint(self.window.width() - 1, self.window.height() - 1)),
            EDGE_RIGHT | EDGE_BOTTOM,
        )

    def test_path_field_browse_updates_its_own_input(self) -> None:
        card, field = self.window._path_field("Source", "Choose folder")
        self.addCleanup(card.deleteLater)
        with patch("shortcut_studio.ui.window.QFileDialog.getExistingDirectory", return_value=str(self.source)):
            card.findChild(QPushButton).click()
        self.assertEqual(field.text(), str(self.source))
