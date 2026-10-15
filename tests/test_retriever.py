"""检索器测试"""

import pytest
from pathlib import Path
from hws_formal_math.engine.retriever import Retriever


class TestRetriever:
    """检索器测试"""
    
    def test_init_with_nonexistent_index(self, tmp_path):
        """索引不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            Retriever(tmp_path)
    
    def test_search_basic(self):
        """基本检索功能"""
        # TODO: 实现测试
        pass
    
    def test_deterministic(self):
        """同输入同结果"""
        # TODO: 实现测试
        pass
