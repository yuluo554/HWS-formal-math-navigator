"""编排器测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from hws_formal_math.core.orchestrator import Orchestrator, OrchestrationResult
from hws_formal_math.config import Config
from hws_formal_math.exceptions import IndexNotFoundError, ModelDisabledError


INDEX_FIXTURE = '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": ["add_comm"]}\n' \
                 '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n' \
                 '{"name": "mul_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a * b * c = a * (b * c)", "deps": []}\n'


class TestOrchestrator:
    """编排器测试"""

    @pytest.fixture
    def index_dir(self, tmp_path):
        """创建测试索引"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(INDEX_FIXTURE, encoding='utf-8')
        return index_dir

    @pytest.fixture
    def config(self, index_dir):
        """创建配置"""
        config = Config()
        config.index_path = index_dir
        config.model.enabled = False
        return config

    @pytest.fixture
    def orchestrator(self, config):
        """创建编排器"""
        return Orchestrator(config)

    def test_init_with_nonexistent_index(self, tmp_path):
        """索引不存在时抛出异常"""
        config = Config()
        config.index_path = tmp_path / "nonexistent"
        with pytest.raises(IndexNotFoundError):
            Orchestrator(config)

    def test_search_basic(self, orchestrator):
        """基本检索功能"""
        results = orchestrator.search("add")
        assert len(results) > 0
        assert all("theorem" in r for r in results)
        assert all("score" in r for r in results)

    def test_search_empty_query(self, orchestrator):
        """空查询返回空列表"""
        results = orchestrator.search("")
        assert len(results) == 0

    def test_search_deterministic(self, orchestrator):
        """同输入同结果"""
        results1 = orchestrator.search("add")
        results2 = orchestrator.search("add")
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1["theorem"] == r2["theorem"]
            assert r1["score"] == r2["score"]

    def test_run_with_formalized_proposition(self, orchestrator):
        """运行完整流程（已形式化命题）"""
        lean_code = "theorem add_assoc (a b c : Nat) : a + b + c = a + (b + c) := by rfl"
        result = orchestrator.run(lean_code)

        assert isinstance(result, OrchestrationResult)
        assert result.proposition == lean_code
        assert result.skeleton == lean_code

    def test_run_with_natural_language(self, orchestrator):
        """运行完整流程（自然语言命题，模型关闭）"""
        result = orchestrator.run("加法结合律")

        assert isinstance(result, OrchestrationResult)
        assert result.proposition == "加法结合律"
        # 模型关闭，自然语言输入应该失败
        assert len(result.errors) > 0

    def test_verify_basic(self, orchestrator):
        """验证 Lean 代码"""
        lean_code = "theorem add_assoc (a b c : Nat) : a + b + c = a + (b + c) := by rfl"
        result = orchestrator.verify(lean_code)

        assert "status" in result
        assert "has_sorry" in result

    def test_verify_with_sorry(self, orchestrator):
        """验证含 sorry 的代码"""
        lean_code = "theorem add_assoc (a b c : Nat) : a + b + c = a + (b + c) := by sorry"
        result = orchestrator.verify(lean_code)

        assert result["has_sorry"] is True
        assert result["sorry_count"] > 0


class TestOrchestratorDeterministic:
    """编排器确定性测试"""

    @pytest.fixture
    def index_dir(self, tmp_path):
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(INDEX_FIXTURE, encoding='utf-8')
        return index_dir

    @pytest.fixture
    def config(self, index_dir):
        config = Config()
        config.index_path = index_dir
        config.model.enabled = False
        return config

    def test_run_deterministic(self, config):
        """同输入同结果"""
        orchestrator1 = Orchestrator(config)
        orchestrator2 = Orchestrator(config)

        lean_code = "theorem add_assoc (a b c : Nat) : a + b + c = a + (b + c) := by rfl"
        result1 = orchestrator1.run(lean_code)
        result2 = orchestrator2.run(lean_code)

        assert result1.status == result2.status
        assert result1.proposition == result2.proposition
        assert result1.skeleton == result2.skeleton


class TestOrchestratorMutation:
    """编排器变异验证"""

    @pytest.fixture
    def index_dir(self, tmp_path):
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(INDEX_FIXTURE, encoding='utf-8')
        return index_dir

    @pytest.fixture
    def config(self, index_dir):
        config = Config()
        config.index_path = index_dir
        config.model.enabled = False
        return config

    def test_search_no_index_fails(self, tmp_path):
        """变异验证：无索引时初始化失败"""
        config = Config()
        config.index_path = tmp_path / "nonexistent"
        with pytest.raises(IndexNotFoundError):
            Orchestrator(config)

    def test_search_empty_index_returns_empty(self, tmp_path):
        """变异验证：空索引返回空结果"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text("", encoding='utf-8')

        config = Config()
        config.index_path = index_dir
        config.model.enabled = False
        orchestrator = Orchestrator(config)

        results = orchestrator.search("add")
        assert len(results) == 0

    def test_verify_with_invalid_code(self, config):
        """变异验证：无效代码应返回错误"""
        orchestrator = Orchestrator(config)
        result = orchestrator.verify("invalid lean code")

        # 无效代码应该返回 FAIL 状态
        assert result["status"] in ["FAIL", "SKIPPED"]

    def test_run_with_model_enabled(self, config):
        """变异验证：模型启用时行为不同"""
        config.model.enabled = True
        config.model.endpoint = "http://localhost:11434/v1"
        config.model.api_key = "test-key"
        orchestrator = Orchestrator(config)

        # 模型启用时，自然语言命题应该尝试生成骨架
        # 但由于端点不可达，会抛出 ModelConfigError
        # 注意：编排器会捕获异常并添加到 errors 中
        result = orchestrator.run("加法结合律")
        assert len(result.errors) > 0
