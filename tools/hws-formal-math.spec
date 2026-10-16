# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['src/hws_formal_math/__main__.py'],
    pathex=['D:\\ProgramData\\zcode\\HWS-formal-math-navigator\\src'],
    binaries=[],
    datas=[('data/index', 'data/index'), ('data/proposals', 'data/proposals'), ('data/snapshots', 'data/snapshots')],
    hiddenimports=['hws_formal_math', 'hws_formal_math.cli', 'hws_formal_math.core', 'hws_formal_math.engine', 'hws_formal_math.parser', 'hws_formal_math.config', 'hws_formal_math.logging', 'hws_formal_math.exceptions'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hws-formal-math',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
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
    name='hws-formal-math',
)
