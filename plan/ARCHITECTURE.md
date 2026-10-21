# Architecture review and implementation plan

Date: 2026-10-21

## Assessment

The original flat package layout was a valid modern Python application layout.
A thin root launcher is valid, but the owner's preferred structure keeps all
application code in the package. This migration therefore removes root `run.py`
and uses `shortcut_studio/__main__.py` for package and PyInstaller launches.
`pyproject.toml`, packaged assets, storage repositories, separate Qt pages,
and compatibility facades already provide a sound foundation. Folder names alone
do not establish production readiness.

The gaps found before migration concerned ownership and verification: `ui/window.py` owned process
startup, environment-dependent paths, database construction, and presentation;
there was no package `__main__` launcher; checkout tests could conceal missing wheel
contents; several existing code directories lacked the required documentation.
`core` is a Qt/Windows execution layer, not a framework-independent domain layer.
Page builders retain their window callback contract. A follow-up split on the
same date extracted library, selection, settings, and frameless controllers;
their architecture is maintained in the owning UI folder's guide.

## Authoritative architecture guides

Implementation architecture lives alongside the code, scoped to the owning folder:

- [Package and startup](../shortcut_studio/doc/architecture.md)
- [Core execution](../shortcut_studio/core/doc/architecture.md)
- [Storage](../shortcut_studio/storage/doc/architecture.md)
- [UI coordination](../shortcut_studio/ui/doc/architecture.md)
- [UI components](../shortcut_studio/ui/components/doc/architecture.md)
- [UI pages](../shortcut_studio/ui/pages/doc/architecture.md)
- [Tests](../tests/doc/architecture.md)
- [Build and distribution checks](../scripts/doc/architecture.md)

This file records assessment, migration work, and acceptance criteria; those
local documents are the architecture to follow when editing implementation.

Every code directory below the repository root has a four-file engineering `doc/`
suite for understanding the code before detailed changes. Root `doc/` is reserved
for user-facing documentation and does not use those templates. Startup owns assembly of the
database and passes it into `MainWindow`; the window owns its Qt controllers;
`WorkflowController` owns worker lifetime; storage owns transactions. Lower
layers must not import UI or bootstrap. Models and path policy do not import Qt.
The legacy `MainWindow(database_path=...)` constructor remains supported.

Retain the flat layout and public import names. A future `src/` migration can
enforce install-first development, but would require coordinated changes to
build paths and documentation. Verify the actual wheel from an unrelated working
directory now to address the immediate packaging risk without moving all files.
Do not add service interfaces, dependency-injection frameworks, or a new domain
package until another caller or genuinely independent use case requires them.

## Implementation checklist

- [x] Extract path policy and application bootstrap; add package launcher.
- [x] Inject the database into the normal startup path; preserve old constructors
  and facade imports, including `shortcut_studio.ui.window.main`.
- [x] Remove root run.py; route package launch, GUI command, and PyInstaller
  through the package bootstrap.
- [x] Add startup, constructor, import-boundary, and installed-wheel checks.
- [x] Update architecture, diagrams, changelogs, README, and missing module docs.
- [x] Run all tests, facade checks, wheel verification, and EXE archive build checks.

## Compatibility and acceptance

1. `python -m shortcut_studio`, `shortcut-studio`, and the PyInstaller executable
   invoke the same startup function and propagate its exit code. Root `run.py`
   is removed; existing scripts using it must switch to package execution.
2. Importing the package does not create a Qt application or database.
3. Source, wheel, and frozen runs resolve the existing packaged ICO independently
   of the current working directory.
4. Default data remains `%LOCALAPPDATA%/ShortcutStudio/shortcut_studio.db`; no
   schema migration or library relocation occurs.
5. An injected database is shared with the workflow controller. Supplying both a
   database instance and a database path raises a clear error.
6. Existing scan, choice, tray, cancellation, and persistence tests pass.

## Verification and rollback

Use `.venv\Scripts\python.exe -m unittest discover -s tests -v`, the facade import
check from AGENTS.md, and the installed-wheel verifier under `scripts/`. Build
the EXE using `.\scripts\build.ps1`. Use temporary databases for smoke tests.
Reverting the migration's code/configuration files restores the previous startup;
no data rollback is needed. Reinstall the package or rebuild the EXE to distribute
the new entry point.

Verified on 2026-10-21 using Windows 11 / Python 3.14.2: all 33 tests passed,
facade imports passed, the built wheel installed and ran its offscreen window
and event loop outside the checkout, and the EXE built from package __main__.py
passed archive verification. Other supported Python versions and interactive
testing of the rebuilt EXE remain release checks, not results claimed here.

## Remaining production work

This migration improves structure; it does not certify the entire application.
Separate work should cover release CI on supported Python/Windows versions and
startup error reporting for the windowed executable. Library-edit operations have
now moved to LibraryController. Track actionable follow-ups
in the package backlog instead of introducing unused layers now.

## References

- [PyPA: src layout versus flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Python: package __main__.py](https://docs.python.org/3/library/__main__.html)
