# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

APP_NAME = 'FinLegal-Chat Ultimate'
VERSION = '5.0.0'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include any assets
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'flet',
        'flet.canvas',
        'flet.charts',
        'flet.core',
        'flet.io',
        'flet.runtime',
        'flet.audio',
        'flet.video',
        'flet.camera',
        'langchain',
        'langchain_openai',
        'langchain_community',
        'langchain_text_splitters',
        'langgraph',
        'pypdf',
        'docx',
        'docx2txt',
        'openpyxl',
        'faiss',
        'faiss.cpu',
        'tiktoken',
        'numpy',
        'yaml',
        'json',
        'sqlite3',
        'threading',
        'hashlib',
        'base64',
        'shutil',
        'src',
        'src.config',
        'src.database',
        'src.engine',
        'src.automation',
        'src.ui',
        'src.ui.theme',
        'src.ui.components',
        'src.ui.app',
        'src.ui.screens',
        'src.ui.screens.chat_screen',
        'src.ui.screens.settings_screen',
        'src.ui.screens.documents_screen',
        'src.ui.screens.history_screen',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'tkinter',
        'test',
        'unittest',
        'pydoc',
    ],
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
    name='FinLegal-Chat-Ultimate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version_file=None,
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FinLegal-Chat-Ultimate',
)
