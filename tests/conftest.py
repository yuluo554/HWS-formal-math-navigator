"""测试初始化"""

import pytest
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def config_path():
    """配置路径 fixture"""
    return None


@pytest.fixture
def index_path():
    """索引路径 fixture"""
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
