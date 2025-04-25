import sys
import os
from PyInstaller.utils.hooks import collect_data_files

# Collect data files from tiktoken
tiktokenDatas = collect_data_files('tiktoken')

block_cipher = None

a = Analysis(
    ['..\\openAIClient\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('../openAIClient/assets', 'openAIClient/assets')],
    hiddenimports=['tiktoken_ext', 'tiktoken_ext.openai_public'],
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
    name='obeliscaDivergencia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='obeliscaDivergencia',
)
