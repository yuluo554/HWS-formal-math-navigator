# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：CLI 冻结产物
#
# 纪律（crash-loop-rescue / ai-tool-project-sprint）：
#   - 入口是**绝对导入的薄模块**（相对导入会让 exe 一启动就 ImportError，而构建仍 exit 0）
#   - pathex 用 SPECPATH 相对推导，**不写死本机绝对路径**（否则 CI 构建失败 + 脱敏扫描命中）
#   - datas 收随包数据（索引/命题/快照/基准用例），冻结态自检断言数据目录落在 exe 同级

from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()          # tools/
REPO_ROOT = SPEC_DIR.parent                  # 仓库根
SRC_DIR = REPO_ROOT / "src"

a = Analysis(
    [str(SRC_DIR / "hws_formal_math" / "__main__.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=[
        (str(REPO_ROOT / "data" / "index"), "data/index"),
        (str(REPO_ROOT / "data" / "proposals"), "data/proposals"),
        (str(REPO_ROOT / "data" / "snapshots"), "data/snapshots"),
        (str(REPO_ROOT / "tests" / "fixtures"), "tests/fixtures"),
    ],
    hiddenimports=[
        "hws_formal_math",
        "hws_formal_math.cli",
        "hws_formal_math.core",
        "hws_formal_math.engine",
        "hws_formal_math.parser",
        "hws_formal_math.benchmark",
        "hws_formal_math.config",
        "hws_formal_math.logging",
        "hws_formal_math.exceptions",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="hws-formal-math",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="hws-formal-math",
)
