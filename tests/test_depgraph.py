"""依赖图测试"""

import pytest
from pathlib import Path
from hws_formal_math.engine.depgraph import DependencyGraph


class TestDependencyGraph:
    """依赖图测试"""
    
    def test_init_with_nonexistent_index(self, tmp_path):
        """索引不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            DependencyGraph(tmp_path)
    
    def test_build_basic(self):
        """基本依赖图构建"""
        # TODO: 实现测试
        pass
    
    def test_broken_ref_detection(self):
        """断链检测"""
        # TODO: 实现测试
        pass
    
    def test_index_gap_distinguished(self):
        """index_gap 与断链区分"""
        # TODO: 实现测试
        pass
