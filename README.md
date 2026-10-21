![Shortcut Studio banner](assest/readme-banner.svg)

<h1 align="center">Shortcut Studio</h1>

<p align="center">Clean shortcuts for every app in your library.</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#build-the-exe">Build the EXE</a> ·
  <a href="#run-tests">Run tests</a>
</p>

Shortcut Studio turns a folder of applications into a tidy library of native Windows `.lnk` shortcuts. It runs locally and keeps your library settings in SQLite.

## What you can do

- **Create shortcuts quickly.** Scan application folders for `.exe` files and executable-named `.lnk` files. Choose a launcher when there is more than one.
- **Keep libraries current.** Check one saved folder pair or all of them to add new shortcuts, repair missing ones, and clean up shortcuts for removed source folders.
- **Manage your choices.** Edit launch targets, inspect run history, and import or export your saved setup as JSON.
- **Stay in control.** Existing Windows shortcuts retain their arguments, working directories, and icons. Closing the window hides the app in the system tray.

## Quick start

Requires **Windows 10/11** and **Python 3.11+**. In PowerShell, from the repository root:

```powershell
py -m pip install .
py run.py
```

The installed package also provides a `shortcut-studio` GUI command. Your database is stored at `%LOCALAPPDATA%\ShortcutStudio\shortcut_studio.db`.

## Build the EXE

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install '.[build]'
.\scripts\build.ps1
```

The build produces `dist\Shortcut Studio.exe`. The icon source is [`shortcut_studio/assets/icon.svg`](shortcut_studio/assets/icon.svg); the build configuration lives in [`scripts/Shortcut Studio.spec`](scripts/Shortcut%20Studio.spec).

## Run tests

```powershell
py -m unittest discover -s tests -v
```
