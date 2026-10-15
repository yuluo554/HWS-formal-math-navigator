"""快照生成器"""

import json
from pathlib import Path
from typing import Dict, Any
import hashlib


def generate_snapshots(output_path: Path, model_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成预置模型输出快照
    
    Args:
        output_path: 输出路径
        model_config: 模型配置
        
    Returns:
        快照 manifest
    """
    # TODO: 实现快照生成
    raise NotImplementedError("快照生成待实现")


def compute_sha256(file_path: Path) -> str:
    """计算 sha256"""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
