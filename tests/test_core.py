from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from shortcut_studio.database import Database
from shortcut_studio.models import FolderResult, ResultStatus
from shortcut_studio.scanner import find_executables, source_folders
from shortcut_studio.shortcuts import install_launch_item, safe_shortcut_name, shortcut_path


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


if __name__ == "__main__":
    unittest.main()
