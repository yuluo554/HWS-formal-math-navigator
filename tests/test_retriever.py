"""检索器测试"""

import pytest
from pathlib import Path
from hws_formal_math.engine.retriever import Retriever, SearchResult


class TestRetriever:
    """检索器测试"""
    
    def test_init_with_nonexistent_index(self, tmp_path):
        """索引不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            Retriever(tmp_path)
    
    def test_search_basic(self, tmp_path):
        """基本检索功能"""
        # 创建测试索引
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n'
            '{"name": "mul_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a * b * c = a * (b * c)", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        results = retriever.search("add")
        
        # 验证返回结果
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        
        # 验证排序：add_assoc 和 add_comm 应该排在前面
        assert results[0].theorem in ["add_assoc", "add_comm"]
        assert results[0].score > 0
    
    def test_search_by_signature(self, tmp_path):
        """通过签名检索"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        results = retriever.search("b + a")
        
        assert len(results) > 0
        assert results[0].theorem == "add_comm"
    
    def test_search_empty_query(self, tmp_path):
        """空查询返回空列表"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        results = retriever.search("")
        
        assert len(results) == 0
    
    def test_search_top_k(self, tmp_path):
        """限制返回结果数"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        # 创建 10 个定理
        lines = []
        for i in range(10):
            lines.append(f'{{"name": "test_{i}", "module": "Test", "signature": "test {i}", "deps": []}}')
        index_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')

        retriever = Retriever(index_dir)
        results = retriever.search("test", top_k=5)

        assert len(results) == 5
    
    def test_deterministic(self, tmp_path):
        """同输入同结果"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        
        # 两次相同查询结果应该一致
        results1 = retriever.search("add")
        results2 = retriever.search("add")
        
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.theorem == r2.theorem
            assert r1.score == r2.score
    
    def test_deterministic_different_order(self, tmp_path):
        """索引顺序不同不影响结果"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        # 不同顺序写入
        index_file.write_text(
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n'
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        results = retriever.search("add")
        
        # 结果应该相同（按分数排序）
        assert len(results) == 2
        assert results[0].theorem in ["add_assoc", "add_comm"]


class TestRetrieverMutation:
    """检索器变异验证"""
    
    def test_bm25_score_returns_zero_for_no_match(self, tmp_path):
        """变异验证：不匹配的词返回 0 分"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        results = retriever.search("multiplication")
        
        # 不匹配的词应该返回空列表
        assert len(results) == 0
    
    def test_bm25_score_higher_for_exact_match(self, tmp_path):
        """变异验证：精确匹配分数更高"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )
        
        retriever = Retriever(index_dir)
        
        # 搜索 "add_assoc" 应该精确匹配
        results = retriever.search("add_assoc")
        
        assert len(results) > 0
        assert results[0].theorem == "add_assoc"
