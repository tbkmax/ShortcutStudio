from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shortcut_studio.database import Database
from shortcut_studio.models import FolderResult, ResultStatus
from shortcut_studio.scanner import find_executables, source_folders
from shortcut_studio.shortcuts import install_launch_item, safe_shortcut_name, shortcut_path
from shortcut_studio.worker import ScanWorker


class ScannerTests(unittest.TestCase):
    def test_finds_unicode_executables_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / "应用程式_日本語"
            nested = app / "bin"
            nested.mkdir(parents=True)
            (nested / "啟動.exe").touch()
            (nested / "ignore.txt").touch()

            self.assertEqual(find_executables(app), [nested / "啟動.exe"])

    def test_lists_immediate_folders_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Beta" / "nested").mkdir(parents=True)
            (root / "alpha").mkdir()
            (root / "loose.exe").touch()

            self.assertEqual(
                [path.name for path in source_folders(root)], ["alpha", "Beta"]
            )

    def test_finds_shortcuts_whose_visible_name_ends_in_exe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            executable_link = folder / "game_start.exe.lnk"
            unrelated_link = folder / "documentation.lnk"
            executable_link.touch()
            unrelated_link.touch()

            self.assertEqual(find_executables(folder), [executable_link])


class ShortcutNameTests(unittest.TestCase):
    def test_preserves_unicode_and_replaces_windows_invalid_characters(self) -> None:
        self.assertEqual(safe_shortcut_name("遊戲：Game?"), "遊戲：Game_")
        self.assertEqual(safe_shortcut_name("A<B>"), "A_B_")

    def test_handles_reserved_and_empty_names(self) -> None:
        self.assertEqual(safe_shortcut_name("CON"), "CON_")
        self.assertEqual(safe_shortcut_name("..."), "Shortcut")
        self.assertEqual(shortcut_path(Path("C:/Target"), "工具").name, "工具.lnk")

    def test_preserves_existing_windows_shortcut(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "game_start.exe.lnk"
            destination = root / "output" / "Project123.lnk"
            original.write_bytes(b"original shortcut settings")

            install_launch_item(original, destination)

            self.assertEqual(destination.read_bytes(), original.read_bytes())


class DatabaseTests(unittest.TestCase):
    def test_records_unicode_run_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "history.db"
            database = Database(database_path)
            source = Path("C:/軟體來源")
            target = Path("C:/捷徑")
            folder = source / "日本語アプリ"
            executable = folder / "起動.exe"
            destination = target / "日本語アプリ.lnk"

            run_id = database.start_run(source, target)
            database.save_result(
                run_id,
                FolderResult(
                    folder,
                    ResultStatus.CREATED,
                    executable,
                    destination,
                ),
            )
            database.complete_run(run_id)

            connection = sqlite3.connect(database_path)
            try:
                row = connection.execute(
                    "SELECT folder_name, executable_path, shortcut_path, status "
                    "FROM folder_results WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                completed_at = connection.execute(
                    "SELECT completed_at FROM runs WHERE id = ?", (run_id,)
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(
                row,
                (
                    "日本語アプリ",
                    str(executable),
                    str(destination),
                    ResultStatus.CREATED.value,
                ),
            )
            self.assertIsNotNone(completed_at)

    def test_saves_lists_and_deletes_folder_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Database(Path(temporary) / "pairs.db")
            source = Path(temporary) / "来源"
            target = Path(temporary) / "捷徑"
            folder = source / "日本語"
            executable = folder / "起動.exe"
            shortcut = target / "日本語.lnk"

            pair, created = database.get_or_create_pair(source, target)
            duplicate, duplicate_created = database.get_or_create_pair(source, target)
            database.save_pair_item(pair.id, folder, executable, shortcut)

            self.assertTrue(created)
            self.assertFalse(duplicate_created)
            self.assertEqual(pair.id, duplicate.id)
            self.assertEqual(database.get_pair_executable(pair.id, folder), executable)
            self.assertEqual(database.list_pairs(), [pair])

            database.delete_pair(pair.id)
            self.assertEqual(database.list_pairs(), [])

    def test_deletes_saved_pair_item(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = Database(root / "pairs.db")
            source = root / "source"
            target = root / "target"
            folder = source / "Removed App"
            pair, _created = database.get_or_create_pair(source, target)
            database.save_pair_item(
                pair.id, folder, folder / "app.exe", target / "Removed App.lnk"
            )

            database.delete_pair_item(pair.id, folder)

            self.assertEqual(database.list_pair_items(pair.id), [])

    def test_migrates_previous_successful_run_to_saved_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "migration.db"
            source = Path(temporary) / "source"
            target = Path(temporary) / "target"
            folder = source / "App"
            executable = folder / "App.exe"
            shortcut = target / "App.lnk"
            database = Database(database_path)
            run_id = database.start_run(source, target)
            database.save_result(
                run_id,
                FolderResult(folder, ResultStatus.CREATED, executable, shortcut),
            )
            database.complete_run(run_id)

            migrated = Database(database_path)
            pairs = migrated.list_pairs()

            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0].source, source)
            self.assertEqual(
                migrated.get_pair_executable(pairs[0].id, folder), executable
            )

    def test_settings_and_export_import_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = Database(root / "original.db")
            source = root / "来源"
            target = root / "捷徑"
            folder = source / "ゲーム"
            executable = folder / "start.exe.lnk"
            shortcut = target / "ゲーム.lnk"
            pair, _created = original.get_or_create_pair(source, target)
            original.save_pair_item(pair.id, folder, executable, shortcut)
            original.set_settings(
                {
                    "open_target_after_completion": True,
                    "confirm_pair_deletion": False,
                }
            )

            exported = original.export_data()
            restored = Database(root / "restored.db")
            pair_count, item_count = restored.import_data(exported)
            restored_pair = restored.list_pairs()[0]

            self.assertEqual((pair_count, item_count), (1, 1))
            self.assertEqual(restored_pair.source, source)
            self.assertEqual(
                restored.get_pair_executable(restored_pair.id, folder), executable
            )
            self.assertTrue(restored.get_setting_bool("open_target_after_completion"))
            self.assertFalse(restored.get_setting_bool("confirm_pair_deletion"))
            self.assertTrue(restored.get_setting_bool("minimize_to_tray_on_close"))


class WorkerTests(unittest.TestCase):
    def test_check_removes_shortcut_when_saved_source_folder_is_gone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            removed_folder = source / "Removed App"
            saved_shortcut = target / "Removed App.lnk"
            saved_shortcut.write_bytes(b"shortcut")
            database = Database(root / "worker.db")
            pair, _created = database.get_or_create_pair(source, target)
            database.save_pair_item(
                pair.id,
                removed_folder,
                removed_folder / "app.exe",
                saved_shortcut,
            )
            historical_run = database.start_run(source, target)
            database.save_result(
                historical_run,
                FolderResult(
                    removed_folder,
                    ResultStatus.CREATED,
                    removed_folder / "app.exe",
                    saved_shortcut,
                ),
            )
            database.complete_run(historical_run)
            totals: list[tuple[int, int, int, int, int]] = []
            worker = ScanWorker(source, target, database, pair.id, check_only=True)
            worker.workflow_finished.connect(lambda *values: totals.append(values))

            worker.run()

            self.assertFalse(saved_shortcut.exists())
            self.assertEqual(database.list_pair_items(pair.id), [])
            self.assertEqual(totals, [(0, 0, 0, 0, 1)])
            reopened = Database(root / "worker.db")
            self.assertEqual(reopened.list_pair_items(pair.id), [])


class MainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_home_page_has_white_check_all_button(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from shortcut_studio.app import MainWindow
            db_path = Path(temporary) / "ui_test.db"
            window = MainWindow(database_path=db_path)
            self.assertTrue(hasattr(window, "home_check_all_button"))
            self.assertEqual(window.home_check_all_button.text(), "Check all")
            self.assertEqual(window.home_check_all_button.objectName(), "primaryButton")
            self.assertTrue(hasattr(window, "home_choose_check_button"))
            self.assertEqual(window.home_choose_check_button.text(), "Choose pair")

    def test_frameless_window_and_translucent_background(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from PyQt6.QtCore import Qt
            from shortcut_studio.app import MainWindow
            db_path = Path(temporary) / "ui_test.db"
            window = MainWindow(database_path=db_path)
            self.assertTrue(bool(window.windowFlags() & Qt.WindowType.FramelessWindowHint))
            self.assertTrue(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))

    def test_custom_window_buttons_and_maximize_toggle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from shortcut_studio.app import MainWindow
            db_path = Path(temporary) / "ui_test.db"
            window = MainWindow(database_path=db_path)
            self.assertTrue(hasattr(window, "min_button"))
            self.assertTrue(hasattr(window, "max_button"))
            self.assertTrue(hasattr(window, "close_button"))
            self.assertEqual(window.min_button.objectName(), "windowMinButton")
            self.assertEqual(window.max_button.objectName(), "windowMaxButton")
            self.assertEqual(window.close_button.objectName(), "windowCloseButton")
            self.assertEqual(window.max_button.icon_type, "maximize")

            # Test maximize toggle
            window._toggle_maximize()
            self.assertTrue(window.isMaximized())
            self.assertEqual(window.max_button.icon_type, "restore")
            window._toggle_maximize()
            self.assertFalse(window.isMaximized())
            self.assertEqual(window.max_button.icon_type, "maximize")

    @patch("shortcut_studio.ui.window.QSystemTrayIcon.isSystemTrayAvailable", return_value=True)
    def test_system_tray_icon_and_hide_restore(self, _tray_available) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from shortcut_studio.app import MainWindow
            db_path = Path(temporary) / "ui_test.db"
            window = MainWindow(database_path=db_path)
            self.assertTrue(hasattr(window, "tray_icon"))
            menu = window.tray_icon.contextMenu()
            self.assertIsNotNone(menu)
            action_texts = [act.text() for act in menu.actions() if act.text()]
            self.assertIn("Open Shortcut Studio", action_texts)
            self.assertIn("Hide to tool bar", action_texts)
            self.assertIn("Quit", action_texts)

            # Test normal minimization (reachable via Alt+Tab and visible in taskbar)
            window.show()
            self.assertFalse(window.isMinimized())
            self.assertFalse(window.isHidden())
            window.showMinimized()
            self.assertTrue(window.isMinimized())
            self.assertFalse(window.isHidden())
            self.assertTrue(window.isVisible())
            window._restore_from_tray()
            self.assertFalse(window.isMinimized())
            self.assertTrue(window.isVisible())

            # Test explicit hiding to tray and restoring
            window._hide_to_tray()
            self.assertTrue(window.isHidden())
            window._restore_from_tray()
            self.assertFalse(window.isHidden())

    @patch("shortcut_studio.ui.window.QSystemTrayIcon.isSystemTrayAvailable", return_value=True)
    def test_close_event_always_hides_to_tray(self, _tray_available) -> None:
        """Close button always hides to system tray (Discord-style); only Quit from tray menu exits."""
        with tempfile.TemporaryDirectory() as temporary:
            from shortcut_studio.app import MainWindow
            db_path = Path(temporary) / "ui_test.db"
            window = MainWindow(database_path=db_path)

            # Closing the window always hides to tray regardless of any setting
            window.show()
            self.assertFalse(window.isHidden())
            window.close()
            self.assertTrue(window.isHidden())

            # Restoring from tray makes the window visible again
            window._restore_from_tray()
            self.assertFalse(window.isHidden())

            # Closing again still hides (not quits)
            window.close()
            self.assertTrue(window.isHidden())

    @patch("shortcut_studio.ui.window.QSystemTrayIcon.isSystemTrayAvailable", return_value=False)
    def test_close_exits_without_system_tray(self, _tray_unavailable) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from shortcut_studio.app import MainWindow
            window = MainWindow(database_path=Path(temporary) / "ui_test.db")
            window.show()
            self.assertTrue(window.close())
            self.assertTrue(window.isHidden())
            self.assertFalse(window.tray_icon.isVisible())

    @patch("shortcut_studio.ui.window.QSystemTrayIcon.isSystemTrayAvailable", return_value=True)
    def test_close_recovers_hidden_or_missing_tray_icon(self, _tray_available) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            from PyQt6.QtGui import QIcon
            from shortcut_studio.app import MainWindow
            window = MainWindow(database_path=Path(temporary) / "ui_test.db")
            window.show()
            window.tray_icon.hide()
            window.tray_icon.setIcon(QIcon())
            self.assertFalse(window.close())
            self.assertTrue(window.isHidden())
            self.assertTrue(window.tray_icon.isVisible())
            self.assertFalse(window.tray_icon.icon().isNull())

    def test_packaged_icon_path_and_multisize_icon(self) -> None:
        from PyQt6.QtGui import QIcon
        from shortcut_studio.ui.window import _app_icon_path

        source_icon = _app_icon_path()
        self.assertTrue(source_icon.is_file())
        self.assertEqual(
            [size.width() for size in QIcon(str(source_icon)).availableSizes()],
            [16, 24, 32, 48, 64, 128, 256],
        )
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(sys, "_MEIPASS", temporary, create=True):
                self.assertEqual(
                    _app_icon_path(), Path(temporary) / "assest" / "icon.ico"
                )

if __name__ == "__main__":
    unittest.main()
