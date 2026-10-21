# Test Suite Backlog

## High Priority

### - [x] Verify Extracted UI Controller Behavior

- **Title**: Protect window-controller extraction with behavior tests.
- **Problem or opportunity**: Existing window tests did not cover editing, settings dialogs, choice routing, or shell resize event filtering.
- **Desired outcome**: A module split preserves user-visible behavior and persistence semantics.
- **Scope**: tests/test_ui_controllers.py and shortcut_studio/ui/.
- **Acceptance criteria**: 1. Launcher edits update real temporary files and records. 2. Failed writes preserve the saved choice. 3. Edit and workflow cancellation route correctly. 4. Backups round-trip settings. 5. Shell mouse events resize the window and release the gesture.
- **Dependencies and risks**: Qt application and temporary filesystem fixtures; mock dialogs and worker callbacks to prevent external side effects.
- **Verification**: `.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- **Priority**: High; completed 2026-10-21 to protect the structural refactor.

### - [x] Guard startup and architectural boundaries

- **Title**: Guard startup and architectural boundaries.
- **Problem or opportunity**: Startup and import dependency direction lacked regression coverage.
- **Desired outcome**: Separate tests detect entry-point, path-policy, and injection regressions.
- **Scope**: test_bootstrap.py, test_architecture.py.
- **Acceptance criteria**: 1. Both launcher and legacy entry-point exit codes are covered. 2. Database injection is verified. 3. Lower-layer imports cannot depend on presentation/startup.
- **Dependencies and risks**: Static import checks do not detect dynamic imports; wheel smoke verification is separate.
- **Verification**: `.venv\Scripts\python.exe -m unittest discover -s tests -v`; `.venv\Scripts\python.exe scripts/verify_wheel.py dist/shortcut_studio-1.0.0-py3-none-any.whl`; `.\scripts\build.ps1`.
- **Priority**: High; completed 2026-10-21 to clarify ownership and guard releases.


No pending backlog items for this module.

## Medium Priority

No pending backlog items for this module.

## Low Priority

No pending backlog items for this module.
