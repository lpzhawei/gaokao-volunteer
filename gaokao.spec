# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
运行：pyinstaller gaokao.spec
"""
import os
from pathlib import Path

BASE_DIR = Path('.').resolve()

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(BASE_DIR)],
    binaries=[
        # Win7兼容：api-ms-win-core-path-l1-1-0.dll
        ('resources/api-ms-win-core-path-l1-1-0.dll', '.'),
    ],
    datas=[
        # 包含数据目录
        ('data/db/gaokao.db', 'data/db'),
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'xlsxwriter',
        'reportlab',
        'reportlab.pdfbase.ttfonts',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'numpy',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.patches',
        'matplotlib.font_manager',
        'matplotlib.figure',
        'matplotlib.backends.backend_agg',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test'],
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
    name='河北高考志愿填报系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # 发布版隐藏控制台
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',   # 程序图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='河北高考志愿填报系统',
)
