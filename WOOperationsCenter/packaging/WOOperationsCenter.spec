# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification for WO Operations Center.
Bundles Python 3.12, PySide6 with QtWebEngine, openpyxl, python-docx,
and the pre-built React production bundle into a standalone executable.
"""

import sys
import os
from pathlib import Path

block_cipher = None

project_dir = os.path.abspath(os.path.join(SPECPATH, ".."))
frontend_dist = os.path.join(project_dir, "frontend", "dist")
icon_file = os.path.join(project_dir, "packaging", "icon.ico")

datas = [
    (frontend_dist, os.path.join("frontend", "dist")),
    (icon_file, "packaging"),
]

binaries = []

hiddenimports = [
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebChannel",
    "openpyxl",
    "docx",
    "sqlite3",
    "hashlib",
    "json",
    "logging"
]

a = Analysis(
    [os.path.join(project_dir, "main.py")],
    pathex=[project_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WOOperationsCenter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WOOperationsCenter",
)
