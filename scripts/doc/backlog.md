# Build Script Backlog

## High Priority

### - [x] Verify installed wheels and package launcher builds

- **Title**: Verify installed wheels and package launcher builds.
- **Problem or opportunity**: Checkout imports can mask missing distribution content.
- **Desired outcome**: Installed wheel runs outside the checkout and EXE uses the package-owned launcher.
- **Scope**: verify_wheel.py, Shortcut Studio.spec.
- **Acceptance criteria**: 1. Wheel probe asserts import origin. 2. Icon and GUI entry point work. 3. Qt creates a visible offscreen window and exits cleanly. 4. EXE archive verification passes.
- **Dependencies and risks**: Requires installed PyQt6 and pip; temporary install does not replace the developer environment.
- **Verification**: `.venv\Scripts\python.exe -m unittest discover -s tests -v`; `.venv\Scripts\python.exe scripts/verify_wheel.py dist/shortcut_studio-1.0.0-py3-none-any.whl`; `.\scripts\build.ps1`.
- **Priority**: High; completed 2026-10-21 to clarify ownership and guard releases.


No pending backlog items for this module.

## Medium Priority

No pending backlog items for this module.

## Low Priority

No pending backlog items for this module.
