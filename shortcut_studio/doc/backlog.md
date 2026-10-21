# Engineering Backlog: Shortcut Studio

This backlog records prioritized engineering tasks, architectural milestones, and functional improvements planned for Shortcut Studio.

---

## How to Use This Backlog

- Each item is self-contained with explicit scope, acceptance criteria, and verification steps.
- Checkboxes denote actionable implementation items.
- Workstreams are grouped by priority based on system reliability, modularity, and user impact.

---

## High Priority

### - [x] Separate startup and verify installed distributions

- **Title**: Separate startup and verify installed distributions.
- **Problem or opportunity**: Window presentation also owned process startup and path policy; source tests alone could hide distribution errors.
- **Desired outcome**: Package-owned launch, explicit startup assembly, preserved imports, and verified installed resources.
- **Scope**: bootstrap.py, paths.py, __main__.py, app.py, ui/window.py, pyproject.toml, scripts, tests, local docs.
- **Acceptance criteria**: 1. Package and GUI entry points converge on bootstrap. 2. Database injection preserves legacy callers. 3. Full tests, installed-wheel smoke test, and EXE archive checks pass.
- **Dependencies and risks**: Reinstall or rebuild to distribute changes; scripts using run.py must switch to package launch.
- **Verification**: `.venv\Scripts\python.exe -m unittest discover -s tests -v`; `.venv\Scripts\python.exe scripts/verify_wheel.py dist/shortcut_studio-1.0.0-py3-none-any.whl`; `.\scripts\build.ps1`.
- **Priority**: High; completed 2026-10-21 to clarify ownership and guard releases.


### - [x] FIX-3: Modern Python Packaging and Resource Layout

- **Problem or opportunity**: Dependency installation relied on `requirements.txt`, while application icons and the build spec were scattered at the repository root.
- **Desired outcome**: Installable `pyproject.toml` project with icons inside the package and build files together in `scripts/`.
- **Scope**: `pyproject.toml`, `shortcut_studio/assets/`, `shortcut_studio/ui/window.py`, `scripts/`, `README.md`, `tests/test_core.py`.
- **Acceptance criteria**: (1) `pip install .` installs PyQt6 and the CLI entry point. (2) Built package includes the icon. (3) PyInstaller bundles the same icon. (4) Public facades and tests pass.
- **Dependencies and risks**: Existing development environments should reinstall the project; deployed EXEs need rebuilding to receive the new resource layout.
- **Verification**: `.venv\Scripts\python.exe -m unittest discover -s tests -v`; `.\scripts\build.ps1`; inspect built wheel.
- **Priority**: High (completed 2026-10-21; packaging consistency and reliable icon lookup).

### - [x] Restore Packaged Tray Visibility
- **Problem or opportunity**: The packaged EXE did not include a runtime copy of the tray icon, so closing could leave the app unreachable.
- **Desired outcome**: A new scalable icon appears on the EXE and in the tray; Close repairs a missing icon or quits when no tray exists.
- **Scope**: `shortcut_studio/assets/icon.svg`, `shortcut_studio/assets/icon.ico`, `scripts/Shortcut Studio.spec`, `scripts/build.ps1`, `shortcut_studio/ui/window.py`, `tests/test_core.py`.
- **Acceptance criteria**: (1) Seven ICO sizes are readable by Qt. (2) The spec bundles the ICO for runtime. (3) Close recovers a missing tray icon and hides with a usable tray. (4) Close quits when no tray exists.
- **Dependencies and risks**: Existing packaged builds need to be rebuilt.
- **Verification**: `.venv\Scripts\python.exe -m unittest discover -s tests -v`; `.\scripts\build.ps1`; console startup probe.
- **Priority**: High (app reachability; low effort). Completed 2026-10-20.

### - [x] FIX-2: Custom Frameless Window Behavior & System Tray Integration
- **Problem or opportunity**: Window used default OS chrome without system tray support or theme alignment.
- **Desired outcome**: Frameless window with custom minimize, resize, and close buttons, 12px rounded corners on all 4 sides adhering to `DESIGN.md`, and system tray hiding with left-click restore and right-click quit.
- **Scope**: `shortcut_studio/ui/window.py`, `shortcut_studio/ui/theme.py`, `shortcut_studio/ui/components/header.py`, `tests/test_core.py`.
- **Acceptance criteria**:
  1. Window has `FramelessWindowHint` and translucent background.
  2. All 4 sides render 12px rounded borders.
  3. Custom minimize button hides window to system tray; left-click on tray icon restores window; right-click displays "Quit".
  4. Custom resize button toggles maximize/restore; header bar is draggable and double-click maximizes.
  5. Automated unit tests validate frameless hints, buttons, tray actions, and restore.
- **Verification**: `python -m unittest discover -s tests -v` (16/16 tests pass).
- **Priority**: High (Completed on 2026-10-19).

### - [x] Implement Submodule Documentation Suites (`storage/doc/`, `core/doc/`)
- **Completed**: 2026-10-21. Added all four documents for core, storage, UI components, and UI pages. Each architecture guide owns its folder's details and links to related guides.
- **Problem or opportunity**: Core, storage, components, and pages lacked local engineering guides for locating and understanding implementation before edits.
- **Desired outcome**: Dedicated `doc/` directories inside `shortcut_studio/storage/doc/` and `shortcut_studio/core/doc/`.
- **Scope**:
  - `shortcut_studio/storage/doc/` (all four engineering documents)
  - `shortcut_studio/core/doc/` (all four engineering documents)
  - `shortcut_studio/ui/components/doc/` and `shortcut_studio/ui/pages/doc/` (all four engineering documents)
  - Note: `shortcut_studio/ui/doc/` completed.
- **Acceptance criteria**:
  1. Each subpackage contains a targeted `doc/` folder adhering to engineering templates.
  2. Storage documentation details SQLite schema, migration history, and repository queries.
  3. Core documentation details COM interface methods, threading condition variables, and error recovery.
  4. UI documentation details page transitions, widget hierarchies, and QSS style contracts.
- **Dependencies and risks**: Low risk; pure documentation addition.
- **Verification**: Review markdown links across all subpackage documents and verify correctness against source files.
- **Priority**: High (Urgency: High, Effort: Low, Value: Maintains modular architectural clarity across teams).

---

## Medium Priority

### - [ ] Automate Windows Release Verification

- **Title**: Run source, wheel, and EXE checks in release CI.
- **Problem or opportunity**: Local verification does not establish coverage across the declared Python 3.11+ support range.
- **Desired outcome**: A Windows CI job runs tests and distribution checks for supported release interpreters.
- **Scope**: CI configuration, pyproject.toml, scripts/verify_wheel.py, scripts/build.ps1.
- **Acceptance criteria**: 1. Python 3.11 and the current release interpreter run the test suite. 2. The built wheel is tested outside the checkout. 3. An EXE build runs archive verification and is retained as an artifact.
- **Dependencies and risks**: Requires a CI provider decision; pin release tooling without changing runtime compatibility.
- **Verification**: Successful Windows CI runs of the unittest, wheel verifier, and EXE build commands.
- **Priority**: Medium; release confidence across versions, moderate setup effort.

### - [ ] Present Startup Failures in the Windowed Application

- **Title**: Add actionable startup error reporting.
- **Problem or opportunity**: Bootstrap database initialization errors currently propagate; the GUI entry point may have no console for users to inspect.
- **Desired outcome**: Users see a useful error and diagnostic location when startup cannot initialize storage.
- **Scope**: bootstrap.py and tests/test_bootstrap.py.
- **Acceptance criteria**: 1. An unwritable database path gives a clear error. 2. Startup exits nonzero. 3. Failed startup does not launch workers or overwrite user data.
- **Dependencies and risks**: Choose a fallback diagnostic location that also works when LOCALAPPDATA is unavailable; avoid recursive error reporting.
- **Verification**: Add subprocess tests for an unavailable database location and normal startup.
- **Priority**: Medium; operational usability beyond the completed structural migration.

### - [ ] Add Custom Arguments and Working Directory Overrides to Shortcut Items
- **Problem or opportunity**: Certain complex Windows executables (e.g. launchers or portable games) require specific command-line arguments or custom working directories rather than defaulting to the executable's parent folder.
- **Desired outcome**: Users can optionally specify command-line arguments and custom working directories when configuring or editing a shortcut pair item.
- **Scope**:
  - `shortcut_studio/models.py` (`PairItem` dataclass field additions)
  - `shortcut_studio/storage/schema.py` (column migration for `pair_items`)
  - `shortcut_studio/core/shell_link.py` (support for `IShellLinkW::SetArguments`)
  - `shortcut_studio/ui/pages/edit_detail_page.py` (argument input field)
- **Acceptance criteria**:
  1. Schema migration adds optional `arguments` and `working_dir` text columns to `pair_items`.
  2. COM creation sets arguments on `IShellLinkW` if provided.
  3. Backward compatibility: Existing `pair_items` with null arguments load and execute without error.
  4. Unit test validates that arguments survive round-trip export/import and are passed to COM link creation.
- **Dependencies and risks**: Requires schema migration; existing databases must cleanly upgrade.
- **Verification**: Run `unittest discover -s tests -v` with new test cases asserting argument persistence.
- **Priority**: Medium (Urgency: Medium, Effort: Medium, Value: Expands app compatibility for complex launchers).

### - [ ] Automated Batch Check Progress and Cancellation Tests
- **Problem or opportunity**: Current unit test suite covers single worker runs, scanner utilities, and database CRUD, but does not simulate multi-pair batch check queuing and cancellation under load.
- **Desired outcome**: Comprehensive automated integration tests simulating batch check processing across multiple mock libraries with edge cases (missing paths, canceled intermediate runs).
- **Scope**:
  - `tests/test_batch_check.py`
  - `tests/test_core.py`
- **Acceptance criteria**:
  1. Test verifies that `batch_check_totals` accumulates statistics correctly across 3+ simulated folder pairs.
  2. Test verifies that cancelling a batch check immediately clears `check_queue` and restores navigation button states.
  3. Tests execute headless in CI environment without displaying GUI popups.
- **Dependencies and risks**: None; test suite addition only.
- **Verification**: `python -m unittest discover -s tests -v` passes cleanly in sub-second execution.
- **Priority**: Medium (Urgency: Medium, Effort: Low, Value: Prevents regression in complex queue state machine).

---

## Low Priority

### - [ ] Export / Import Encryption and Password Protection
- **Problem or opportunity**: Saved pairs export files are currently plain-text JSON. Users storing sensitive paths across drives may desire password-encrypted backups.
- **Desired outcome**: Optional AES-GCM encrypted backup format with passphrase prompt.
- **Scope**: `shortcut_studio/storage/backup.py`, `shortcut_studio/ui/pages/settings_page.py`.
- **Acceptance criteria**: Users can select either plain JSON or encrypted archive; corrupt passphrases trigger friendly error dialogs.
- **Dependencies and risks**: May require standard library or minimal crypto dependency.
- **Verification**: Round-trip encryption and invalid password rejection tests.
- **Priority**: Low (Urgency: Low, Effort: Medium, Value: Enhanced privacy for sensitive folder structures).
