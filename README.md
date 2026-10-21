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
py -m shortcut_studio
```

The installed package also provides a `shortcut-studio` GUI command. Both launch methods use the same application bootstrap. Your database is stored at `%LOCALAPPDATA%\ShortcutStudio\shortcut_studio.db`.

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

## Development and architecture

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[build]'
.\.venv\Scripts\python.exe -m shortcut_studio
```

The flat package layout keeps application code inside `shortcut_studio/`.
`__main__.py` is the package and PyInstaller launcher. `bootstrap.py` assembles
Qt and the database; `paths.py` owns filesystem locations; `ui/`, `core/`, and
`storage/` own presentation, scan/platform execution, and persistence. See the
[architecture review and plan](plan/ARCHITECTURE.md) and
[package architecture](shortcut_studio/doc/architecture.md).

Verify a wheel outside the checkout as well as running source tests:

```powershell
.\.venv\Scripts\python.exe -m pip wheel --no-deps --no-build-isolation . --wheel-dir dist
.\.venv\Scripts\python.exe scripts/verify_wheel.py dist/shortcut_studio-1.0.0-py3-none-any.whl
```

The verifier uses the environment's installed PyQt6, installs the local wheel in
a disposable directory without network access, and starts an offscreen window
and event loop. Reinstall the package or rebuild the EXE after code changes.
