"""配置管理"""

import os
import site
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import yaml

# 随包数据在安装态落到的相对位置（与 pyproject.toml 的 [tool.setuptools.data-files] 对应）
SHARE_SUBDIR = Path("share") / "hws-formal-math"

# 判定"这是一份完整数据目录"的锚点文件
DATA_ANCHOR = Path("index") / "theorems.jsonl"


def is_frozen() -> bool:
    """是否运行在 PyInstaller 冻结态"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _share_roots() -> List[Path]:
    """安装态 share 基目录候选（venv / 系统 / 用户级三种安装位）

    data_files 的落地位置随安装方式变化：
      - venv / 普通安装 → sys.prefix/share
      - 装到系统解释器 → sys.base_prefix/share
      - `pip install --user` → site.USER_BASE/share
    返回的是 `<...>/share/hws-formal-math` 这一级，其下有 `data/` 与 `fixtures/`。
    """
    bases: List[Path] = []

    for prefix in (sys.prefix, sys.base_prefix):
        if prefix:
            bases.append(Path(prefix))

    user_base = getattr(site, "USER_BASE", None)
    if user_base:
        bases.append(Path(user_base))

    try:
        # <prefix>/Lib/site-packages → <prefix>
        for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
            site_path = Path(site_dir)
            bases.append(site_path.parent.parent)
            bases.append(site_path.parent)
    except Exception:  # pragma: no cover - 极端环境（无 site 支持）
        pass

    roots: List[Path] = []
    for base in bases:
        candidate = base / SHARE_SUBDIR
        if candidate not in roots:
            roots.append(candidate)
    # 相对路径兜底（工具把 share/ 平铺在当前工作目录旁的历史布局）
    if Path(SHARE_SUBDIR) not in roots:
        roots.append(Path(SHARE_SUBDIR))
    return roots


def _first_complete(candidates: List[Path], anchor: Path) -> Optional[Path]:
    for candidate in candidates:
        if (candidate / anchor).is_file():
            return candidate
    return None


def default_data_dir() -> Path:
    """随包数据目录

    冻结态：数据由 spec 的 datas 打进产物，落在 _MEIPASS（onefile）
    或 exe 同级（onedir）——冻结态自检据此断言"数据随包走"。
    源码态：CWD 相对的 data/（在仓根运行时命中，保持既有行为）。
    装态（pip 安装，D1）：回落到 <prefix>/share/hws-formal-math/data。
    """
    if is_frozen():
        return Path(sys._MEIPASS) / "data"

    cwd_data = Path("data")
    if (cwd_data / DATA_ANCHOR).is_file():
        return cwd_data

    installed = _first_complete(
        [root / "data" for root in _share_roots()], DATA_ANCHOR
    )
    if installed is not None:
        return installed

    return cwd_data


def default_fixtures_dir() -> Optional[Path]:
    """基准用例目录（D1：pip 装完 bench 找不到 tests/fixtures → exit 2）

    查找顺序：repo 内 tests/fixtures → 安装态 share/hws-formal-math/fixtures。
    """
    repo_fixtures = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
    if (repo_fixtures / "retrieval_cases.json").is_file():
        return repo_fixtures

    for root in _share_roots():
        candidate = root / "fixtures"
        if (candidate / "retrieval_cases.json").is_file():
            return candidate
    return None


@dataclass
class ModelConfig:
    """模型配置"""
    enabled: bool = False
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: str = "openpangu-2.0-flash"
    llama_cpp_path: Optional[str] = None
    omni_infer_url: Optional[str] = None


@dataclass
class LeanConfig:
    """Lean 配置"""
    lean_path: Optional[str] = None
    mathlib4_path: Optional[str] = None


@dataclass
class Config:
    """主配置"""
    model: ModelConfig = field(default_factory=ModelConfig)
    lean: LeanConfig = field(default_factory=LeanConfig)
    index_path: Path = field(default_factory=lambda: default_data_dir() / "index")
    data_dir: Path = field(default_factory=default_data_dir)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """从文件加载配置"""
        config = cls()

        if config_path and config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and "model" in data:
                model_data = data["model"]
                config.model.enabled = model_data.get("enabled", False)
                config.model.endpoint = model_data.get("endpoint")
                config.model.api_key = model_data.get("api_key") or os.environ.get("OPENAI_API_KEY")
                config.model.model = model_data.get("model", "openpangu-2.0-flash")
                config.model.llama_cpp_path = model_data.get("llama_cpp_path")
                config.model.omni_infer_url = model_data.get("omni_infer_url")

            if data and "lean" in data:
                lean_data = data["lean"]
                config.lean.lean_path = lean_data.get("lean_path")
                config.lean.mathlib4_path = lean_data.get("mathlib4_path")

        return config
