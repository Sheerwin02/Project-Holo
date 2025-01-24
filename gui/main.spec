# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    module_collection_mode={
        'gradio': 'py', 
    },
    ['C:\\Users\\Sheerwin\\Desktop\\Project Holo\\gui\\main.py'],
    pathex=[
        'C:\\Users\\Sheerwin\\Desktop\\Project Holo',
        'C:\\Users\\Sheerwin\\Desktop\\Project Holo\\gui',
        'C:\\Users\\Sheerwin\\Desktop\\Project Holo\\server'
    ],
    binaries=[],
    datas=[
        ('C:\\Users\\Sheerwin\\Desktop\\Project Holo\\.env', '.'),
        ('C:\\Users\\Sheerwin\\Desktop\\Project Holo\\server\\assistant.json', 'server'),
        ('C:\\Users\\Sheerwin\\Desktop\\Project Holo\\server', 'server')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide2', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='your_application_name',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='your_application_name'
)
