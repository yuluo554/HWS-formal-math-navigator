"""配置管理"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml


def is_frozen() -> bool:
    """是否运行在 PyInstaller 冻结态"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def default_data_dir() -> Path:
    """随包数据目录

    冻结态：数据由 spec 的 datas 打进产物，落在 _MEIPASS（onefile）
    或 exe 同级（onedir）——冻结态自检据此断言"数据随包走"。
    源码态：CWD 相对的 data/。
    """
    if is_frozen():
        return Path(sys._MEIPASS) / "data"
    return Path("data")


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
