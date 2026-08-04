# -*- mode: python ; coding: utf-8 -*-

import sys


windows_version = "packaging/windows-version.txt" if sys.platform == "win32" else None

analysis = Analysis(
    ["ui-tools/ui_studio.py"],
    pathex=[],
    binaries=[],
    datas=[("ui-tools/studio", "studio")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="plazmic-ui-studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    version=windows_version,
)
