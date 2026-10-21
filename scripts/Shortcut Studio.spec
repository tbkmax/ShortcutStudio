# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).resolve().parent
icon = project_root / 'shortcut_studio' / 'assets' / 'icon.ico'

a = Analysis(
    [str(project_root / 'run.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(icon), 'shortcut_studio/assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Shortcut Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(icon)],
)
