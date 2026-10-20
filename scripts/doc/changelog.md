# Build Script Changelog

## [Unreleased]

### Added

#### 2026-10-20 - Module Documentation Directory
- Created `scripts/doc/` with architecture, workflow, changelog, and backlog files following the repository templates.

#### 2026-10-20 - Verified Windows Build Command
- Filled in [`build.ps1`](../build.ps1) as the sole supported EXE build command. It isolates `PATH`, uses the checked-in spec, and checks the resulting archive for the runtime icon and conflicting ICU DLL.

### Removed

#### 2026-10-20 - Obsolete Text Build Command
- Removed `build.txt`, whose command regenerated the spec and could omit required runtime data.

### Fixed

#### 2026-10-20 - PowerShell Archive Verification
- Moved the Python archive check from an inline `-c` argument into [`verify_build.py`](../verify_build.py), preserving its checks while avoiding PowerShell quote and backslash mangling.

## Migration and Upgrade Notes

Run `.\scripts\build.ps1` to produce a new EXE. No database migration is required.
