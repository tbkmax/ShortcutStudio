# Shortcut Studio

Shortcut Studio is a Windows desktop app that turns a folder of applications into a tidy folder of native `.lnk` shortcuts.

## What it does

- Treats each immediate subfolder in the source folder as one application.
- Searches recursively inside each application folder for `.exe` files.
- Also detects Windows shortcuts whose visible name ends in `.exe` (for example, an actual file named `game_start.exe.lnk`).
- Automatically uses the executable when exactly one is found.
- Shows native Windows icons and asks you to choose when multiple executables are found.
- Names each shortcut after its application folder and uses the executable's original icon.
- Records each run and folder result in a local SQLite database.
- Supports Simplified/Traditional Chinese, Japanese, and other Unicode names and paths.
- Saves each source/target folder pair for future checks.
- Checks one saved library or all saved libraries in a single run.
- Recreates missing shortcuts, detects newly added application folders, and removes saved shortcuts when their original source folders have been deleted.
- Provides a List page where saved pairs and their history can be removed without deleting files.
- Provides a Test button beside each executable candidate so it can be opened before selection.
- Preserves existing Windows shortcuts unchanged, including their arguments, working directory, icon, and special launcher behavior.
- Provides an Edit page showing every generated shortcut, its source subfolder, icon, and selected launch file; changing a selection updates the shortcut and icon together.
- Provides a Settings page for opening the database folder and importing or exporting saved pairs, executable choices, and preferences as Unicode JSON.
- Can optionally open the target folder after completion and make pair deletion confirmation optional.

The top menu contains **Start New**, **Check**, **Edit**, **List**, and **Settings**.

The home screen is a desktop-style dashboard showing the number of saved libraries, the most recent pair, and quick actions. Every menu destination includes a Back button to return to this dashboard.

Starting a new run with an already-saved source/target pair automatically performs a Check instead of rebuilding every shortcut.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer

## Run the app

Open PowerShell in this folder and run:

```powershell
py -m pip install .
py run.py
```

If your Python command is `python` instead of `py`, substitute `python` in both commands.
The installed package also provides a `shortcut-studio` GUI command.

The database is stored at `%LOCALAPPDATA%\ShortcutStudio\shortcut_studio.db`.

## Build the Windows EXE

The editable app icon is [`shortcut_studio/assets/icon.svg`](shortcut_studio/assets/icon.svg). Its multi-size Windows export is [`shortcut_studio/assets/icon.ico`](shortcut_studio/assets/icon.ico). Build through [`scripts/build.ps1`](scripts/build.ps1), which uses [`scripts/Shortcut Studio.spec`](scripts/Shortcut%20Studio.spec), bundles the icon for the window and tray, and prevents unrelated tools on `PATH` from supplying incompatible Qt libraries.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install '.[build]'
.\scripts\build.ps1
```

The resulting app is `dist\Shortcut Studio.exe`. Clicking its close button hides it in the Windows notification area; use the tray icon to reopen or quit.

## Run tests

```powershell
py -m unittest discover -s tests -v
```
