# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：CLI + 桌面查看器双产物
#
# 纪律（crash-loop-rescue / ai-tool-project-sprint / preflight ㉕）：
#   - 入口是**绝对导入的薄模块**（相对导入会让 exe 一启动就 ImportError，而构建仍 exit 0）
#   - pathex 用 SPECPATH 相对推导，**不写死本机绝对路径**（否则 CI 构建失败 + 脱敏扫描命中）
#   - datas 收随包数据（索引/命题/快照/基准用例），冻结态自检断言数据目录落在 exe 同级
#   - **查看器是独立产物**：`hws-formal-math-viewer`，与 CLI 同目录（onedir 双 exe），
#     随 Release zip 一起分发——只在源码里存在不算交付（preflight ㉓/㉕）
#
# 依赖缺失语义：查看器在无 PySide6 时仍可 `--selftest`（零 Qt 路径），窗口模式 exit 3。
# 因此 spec 不强依赖 PySide6；构建机装了 gui extra 时自动收 Qt，没装则只产 CLI。

from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()          # tools/
REPO_ROOT = SPEC_DIR.parent                  # 仓库根
SRC_DIR = REPO_ROOT / "src"

DATAS = [
    (str(REPO_ROOT / "data" / "index"), "data/index"),
    (str(REPO_ROOT / "data" / "proposals"), "data/proposals"),
    (str(REPO_ROOT / "data" / "snapshots"), "data/snapshots"),
    (str(REPO_ROOT / "tests" / "fixtures"), "tests/fixtures"),
]

HIDDEN = [
    "hws_formal_math",
    "hws_formal_math.cli",
    "hws_formal_math.core",
    "hws_formal_math.engine",
    "hws_formal_math.parser",
    "hws_formal_math.benchmark",
    "hws_formal_math.config",
    "hws_formal_math.logging",
    "hws_formal_math.exceptions",
    "hws_formal_math.viewer",
    "hws_formal_math.viewer.controller",
]


def _has_pyside():
    try:
        import PySide6  # noqa: F401
        return True
    except ImportError:
        return False


# 只用到 QtCore/QtGui/QtWidgets。PySide6 的 hook 会把 Quick/Qml/Pdf/OpenGL 的 DLL
# 与插件一并收进来（产物 100MB+），而 excludes 对 binaries 不生效——
# 因此在 Analysis 之后**按文件名再滤一遍**（2026-10-18：zip 由 112MB 降到 ~35MB）。
DROP_QT = (
    "qt6quick", "qt6qml", "qt6pdf", "qt6opengl", "qt6network", "qt6sql",
    "qt6designer", "qt6svg", "qt6charts", "qt6datavisualization", "qt6multimedia",
    "qt6test", "opengl32sw", "qml", "qtquick", "qtvirtualkeyboard",
)


def _trim_qt(analysis):
    """从 binaries/datas 中剔除未使用的 Qt 组件（大小与启动时间双收益）"""
    def keep(entry):
        name = entry[0].replace("\\", "/").lower()
        if "/pyside6/" not in name and not name.startswith("pyside6/"):
            return True
        base = name.rsplit("/", 1)[-1]
        return not any(token in base or token in name for token in DROP_QT)

    analysis.binaries = [b for b in analysis.binaries if keep(b)]
    analysis.datas = [d for d in analysis.datas if keep(d)]
    return analysis


def _analysis(entry):
    return Analysis(
        [str(entry)],
        pathex=[str(SRC_DIR)],
        binaries=[],
        datas=DATAS,
        hiddenimports=HIDDEN,
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        # 只用到 QtCore/QtGui/QtWidgets：Quick/Qml/Pdf/OpenGL 等模块会把产物撑到 100MB+，
        # 且对纯窗口应用无用（排除后 zip 从 ~112MB 降到 ~30MB 量级）
        excludes=[
            "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickWidgets",
            "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtWebEngineCore",
            "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
            "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
            "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets", "PySide6.QtSql",
            "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtUiTools",
            "PySide6.QtNetwork", "PySide6.QtSvg", "PySide6.QtPrintSupport",
            "tkinter", "unittest", "pydoc", "doctest", "numpy", "scipy", "matplotlib",
        ],
        noarchive=False,
        optimize=0,
    )


def _exe(analysis, name, console):
    pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=None)
    return EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=console,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )


# ---- CLI 产物（console=True） ----
cli_analysis = _analysis(SRC_DIR / "hws_formal_math" / "__main__.py")
cli_exe = _exe(cli_analysis, "hws-formal-math", console=True)

collect_args = [cli_exe, cli_analysis.binaries, cli_analysis.datas]

# ---- 查看器产物（console=False；无 PySide6 时仍产出一个可 --selftest 的 exe） ----
viewer_analysis = _trim_qt(_analysis(SRC_DIR / "hws_formal_math" / "viewer" / "__main__.py"))
viewer_exe = _exe(viewer_analysis, "hws-formal-math-viewer", console=False)
collect_args += [viewer_exe, viewer_analysis.binaries]

coll = COLLECT(
    *collect_args,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="hws-formal-math",
)
