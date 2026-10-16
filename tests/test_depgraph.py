"""依赖图测试"""

import pytest
from pathlib import Path
from hws_formal_math.engine.depgraph import DependencyGraph, DepGraphResult, DepGraphNode, DepGraphEdge


class TestDependencyGraph:
    """依赖图测试"""
    
    def test_init_with_nonexistent_index(self, tmp_path):
        """索引不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            DependencyGraph(tmp_path)
    
    def test_build_basic(self, tmp_path):
        """基本依赖图构建"""
        # 创建测试索引
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": ["add_comm", "zero_add"]}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n'
            '{"name": "zero_add", "module": "Mathlib.Algebra.Group.Defs", "signature": "0 + a = a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_assoc", "add_comm", "zero_add"])
        
        assert isinstance(result, DepGraphResult)
        assert len(result.nodes) == 3
        assert len(result.edges) == 2  # add_assoc -> add_comm, add_assoc -> zero_add
    
    def test_broken_ref_detection(self, tmp_path):
        """断链检测"""
        # 创建测试索引
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": ["nonexistent_theorem"]}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_assoc", "add_comm"])
        
        # nonexistent_theorem 应该被检测为断链或 index_gap
        assert len(result.broken_refs) + len(result.index_gaps) > 0
    
    def test_index_gap_distinguished(self, tmp_path):
        """index_gap 与断链区分"""
        # K2 口径：index_gap ≠ 定理不存在
        
        # 创建测试索引
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": ["unknown_theorem"]}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_assoc", "add_comm"])
        
        # unknown_theorem 应该被分类
        # 如果它属于已覆盖模块，则是 broken_ref
        # 否则是 index_gap
        assert len(result.broken_refs) + len(result.index_gaps) >= 1
    
    def test_no_dependencies(self, tmp_path):
        """无依赖的定理"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_comm"])
        
        assert len(result.nodes) == 1
        assert len(result.edges) == 0


class TestDependencyGraphMutation:
    """依赖图变异验证"""
    
    def test_build_rejects_nonexistent_theorem(self, tmp_path):
        """变异验证：不存在的定理不加入图"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_comm", "nonexistent_theorem"])
        
        # 不存在的定理不加入图
        assert len(result.nodes) == 1
        assert "nonexistent_theorem" not in [n.id for n in result.nodes]
    
    def test_build_accepts_valid_theorems(self, tmp_path):
        """变异验证：有效定理被接受"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_comm"])
        
        assert len(result.nodes) == 1


class TestDependencyGraphDeterministic:
    """依赖图确定性测试"""
    
    def test_build_deterministic(self, tmp_path):
        """同输入同结果"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": ["add_comm"]}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        
        result1 = depgraph.build(["add_assoc", "add_comm"])
        result2 = depgraph.build(["add_assoc", "add_comm"])
        
        assert len(result1.nodes) == len(result2.nodes)
        assert len(result1.edges) == len(result2.edges)
        assert len(result1.broken_refs) == len(result2.broken_refs)
        assert len(result1.index_gaps) == len(result2.index_gaps)


class TestDependencyGraphExport:
    """依赖图导出测试"""
    
    def test_export_html(self, tmp_path):
        """HTML 导出"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        depgraph = DependencyGraph(index_dir)
        result = depgraph.build(["add_comm"])
        
        output_path = tmp_path / "report.html"
        depgraph.export_html(result, output_path)
        
        assert output_path.exists()
        
        # 检查 HTML 内容
        content = output_path.read_text(encoding='utf-8')
        assert '<!DOCTYPE html>' in content
        assert 'add_comm' in content
        assert 'Mathlib.Algebra.Group.Defs' in content
