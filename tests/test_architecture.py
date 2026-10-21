"""Guard the intended dependency direction as modules evolve."""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

import shortcut_studio


class ArchitectureTests(unittest.TestCase):
    def test_lower_layers_do_not_import_presentation_or_startup(self) -> None:
        package = Path(shortcut_studio.__file__).resolve().parent
        files = [package / name for name in ("models.py", "scanner.py", "paths.py")]
        files += list((package / "storage").glob("*.py"))
        files += list((package / "core").glob("*.py"))
        for file in files:
            forbidden = ["shortcut_studio.ui", "shortcut_studio.app", "shortcut_studio.bootstrap"]
            if file.parent.name != "core":
                forbidden.append("PyQt6")
            for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
                imports = []
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:
                        parts = ["shortcut_studio"] + list(file.relative_to(package).parts[:-1])
                        module = ".".join(parts[:len(parts) - node.level + 1] + ([module] if module else []))
                    imports = [module, *(f"{module}.{alias.name}" for alias in node.names)]
                for imported in imports:
                    with self.subTest(file=file.name, imported=imported):
                        self.assertFalse(any(imported == prefix or imported.startswith(prefix + ".") for prefix in forbidden))

    def test_package_import_does_not_load_qt_or_storage(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "import sys; import shortcut_studio; assert not any(n.startswith(('PyQt6', 'shortcut_studio.storage')) for n in sys.modules)"],
            cwd=Path(shortcut_studio.__file__).resolve().parent.parent,
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
