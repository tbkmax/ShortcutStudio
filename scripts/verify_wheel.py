"""Install a local wheel into a temporary target and smoke-test it outside the repo.

Usage: python scripts/verify_wheel.py dist/shortcut_studio-1.0.0-py3-none-any.whl
Run with the project's environment so its PyQt6 dependency is available.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


PROBE = r'''
import sys
from importlib.metadata import distribution
from pathlib import Path
from unittest.mock import patch

site = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(site))
import shortcut_studio
assert Path(shortcut_studio.__file__).resolve().is_relative_to(site)
assert not any(name.startswith("PyQt6") for name in sys.modules)
from shortcut_studio.app import main, MainWindow
from shortcut_studio.bootstrap import main as bootstrap_main
from shortcut_studio.database import Database
from shortcut_studio.shortcuts import create_shortcut
from shortcut_studio.worker import ScanWorker
from shortcut_studio.paths import app_icon_path
assert main is bootstrap_main
assert app_icon_path().is_file()
assert app_icon_path().is_relative_to(site)
entry = next(e for e in distribution("shortcut-studio").entry_points
             if e.group == "gui_scripts" and e.name == "shortcut-studio")
assert entry.load() is main
assert Path(shortcut_studio.__file__).with_name("__main__.py").is_file()
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
original_exec = QApplication.exec
def short_event_loop(app):
    assert not app.windowIcon().isNull()
    assert len(QIcon(str(app_icon_path())).availableSizes()) == 7
    assert any(isinstance(w, MainWindow) and w.isVisible() for w in app.topLevelWidgets())
    QTimer.singleShot(0, app.quit)
    return original_exec()
with patch.object(QApplication, "exec", short_event_loop):
    assert main(["shortcut-studio"], database_path=Path.cwd() / "smoke.db") == 0
assert (Path.cwd() / "smoke.db").is_file()
print("Installed wheel: imports, GUI entry point, icon, window, and event loop verified")
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="shortcut-wheel-") as temporary:
        root = Path(temporary)
        site = root / "installed"
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-index", "--no-deps",
             "--no-compile", "--target", str(site), str(wheel)],
            check=True, cwd=root, timeout=120,
        )
        environment = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        subprocess.run(
            [sys.executable, "-I", "-c", PROBE, str(site)],
            check=True, cwd=root, env=environment, timeout=30,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
