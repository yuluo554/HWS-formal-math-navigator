"""HWS-formal-math-navigator: 形式化数学库导航与证明骨架生成器

D11：版本号单源。以前 pyproject.toml=0.1.1 而这里写死 0.1.0，于是
发布出去的 wheel METADATA 是 0.1.1、`import hws_formal_math` 却得到 0.1.0。
现在以**安装元数据**为唯一真源（pyproject.toml → dist-info）；
源码态（未安装）回落到仓内 pyproject.toml，最后才是常量兜底。
"""

import re
from pathlib import Path
from typing import Optional

# 源码态兜底：仅在既未安装、也读不到 pyproject.toml 时使用。
# 它必须与 pyproject.toml 的 version 一致 —— tests/test_repo_gate.py 有对撞断言。
_FALLBACK_VERSION = "0.1.2"


def _read_version_from_pyproject() -> Optional[str]:
    """从仓库根 pyproject.toml 读版本（源码态的权威值）"""
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject.is_file():
        return None
    match = re.search(
        r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE
    )
    return match.group(1) if match else None


def _read_version_from_metadata() -> Optional[str]:
    """从已安装的 dist-info 读版本"""
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - 3.7 及以下无该模块
        return None

    try:
        return version("hws-formal-math-navigator")
    except PackageNotFoundError:
        return None


def _resolve_version() -> str:
    """安装元数据 → 仓内 pyproject → 兜底常量

    源码态优先用 pyproject：`pip install -e .` 之后 dist-info 也会存在，
    但改 pyproject 不会立刻反映到 editable 安装的元数据里，两者可能短暂不一致。
    """
    pyproject_version = _read_version_from_pyproject()
    if pyproject_version:
        return pyproject_version

    return _read_version_from_metadata() or _FALLBACK_VERSION


__version__ = _resolve_version()
