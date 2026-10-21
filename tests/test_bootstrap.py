"""Startup, dependency assembly, and backwards-compatible launch contracts."""

from __future__ import annotations

import os
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shortcut_studio import bootstrap
from shortcut_studio.paths import app_icon_path, default_database_path
from shortcut_studio.storage.database import Database


class PathTests(unittest.TestCase):
    def test_database_path_uses_local_app_data_without_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "user-data"
            with patch.dict(os.environ, {"LOCALAPPDATA": str(root)}):
                self.assertEqual(default_database_path(), root / "ShortcutStudio" / "shortcut_studio.db")
            self.assertFalse(root.exists())

    def test_database_path_falls_back_for_missing_or_empty_environment(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch("shortcut_studio.paths.Path.home", return_value=Path("C:/User")):
            expected = Path("C:/User/AppData/Local/ShortcutStudio/shortcut_studio.db")
            self.assertEqual(default_database_path(), expected)
            os.environ["LOCALAPPDATA"] = ""
            self.assertEqual(default_database_path(), expected)

    def test_icon_location_is_independent_of_working_directory(self) -> None:
        expected = app_icon_path()
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary)
                self.assertEqual(app_icon_path(), expected)
                self.assertTrue(expected.is_file())
            finally:
                os.chdir(original)


class BootstrapTests(unittest.TestCase):
    def test_startup_passes_database_to_window_and_returns_exit_code(self) -> None:
        with (
            patch.object(bootstrap, "QApplication") as application,
            patch.object(bootstrap, "QFont"),
            patch.object(bootstrap, "QIcon"),
            patch.object(bootstrap, "Database") as database,
            patch.object(bootstrap, "MainWindow") as window,
        ):
            application.return_value.exec.return_value = 7
            path = Path("isolated.db")
            self.assertEqual(bootstrap.main(["shortcut-studio"], database_path=path), 7)
            application.assert_called_once_with(["shortcut-studio"])
            application.return_value.setQuitOnLastWindowClosed.assert_called_once_with(False)
            database.assert_called_once_with(path)
            window.assert_called_once_with(database=database.return_value)
            window.return_value.show.assert_called_once_with()

    def test_startup_resolves_default_database_and_process_arguments(self) -> None:
        with (
            patch.object(bootstrap, "QApplication") as application,
            patch.object(bootstrap, "QFont"),
            patch.object(bootstrap, "QIcon"),
            patch.object(bootstrap, "Database") as database,
            patch.object(bootstrap, "MainWindow"),
            patch.object(bootstrap, "default_database_path", return_value=Path("default.db")),
            patch.object(sys, "argv", ["launcher", "-platform", "offscreen"]),
        ):
            bootstrap.main()
            application.assert_called_once_with(sys.argv)
            database.assert_called_once_with(Path("default.db"))

    def test_launchers_propagate_exit_code(self) -> None:
        launchers = [Path(bootstrap.__file__).with_name(name) for name in ("__main__.py", "app.py")]
        for launcher in launchers:
            with self.subTest(launcher=launcher), patch.object(bootstrap, "main", return_value=9) as main:
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(launcher), run_name="__main__")
                self.assertEqual(result.exception.code, 9)
                main.assert_called_once_with()

    def test_legacy_entry_points_remain_callable(self) -> None:
        from shortcut_studio.app import main
        from shortcut_studio.ui import main as ui_main
        from shortcut_studio.ui.window import main as window_main

        self.assertIs(main, bootstrap.main)
        for entry in (ui_main, window_main):
            with patch.object(bootstrap, "main", return_value=5):
                self.assertEqual(entry(), 5)


class WindowDependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from PyQt6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

    def test_injected_database_is_shared_with_workflow(self) -> None:
        from shortcut_studio.ui.window import MainWindow

        with tempfile.TemporaryDirectory() as temporary:
            database = Database(Path(temporary) / "injected.db")
            with patch("shortcut_studio.ui.window.Database") as constructor:
                window = MainWindow(database=database)
            try:
                constructor.assert_not_called()
                self.assertIs(window.database, database)
                self.assertIs(window.workflow.database, database)
            finally:
                window.tray.hide_icon()
                window.deleteLater()
                self.app.processEvents()

    def test_ambiguous_database_arguments_are_rejected(self) -> None:
        from shortcut_studio.ui.window import MainWindow

        with tempfile.TemporaryDirectory() as temporary:
            database = Database(Path(temporary) / "injected.db")
            with self.assertRaisesRegex(ValueError, "either database or database_path"):
                MainWindow(database.path, database=database)
