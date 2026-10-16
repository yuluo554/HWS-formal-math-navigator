"""基准探活测试

口径（plan/03-基准套件设计.md §六）：
  **坏实现必须被判未达标** —— 探活打在**消费处**（基准的实际运行路径），
  不是断言"函数存在"。注入缺陷 → 基准必须报未达标；探活全绿则说明基准是假门。

纪律：每类探活都做"坏实现→未达标"与"好实现→达标"的**双向对照**，
只测一侧的探活本身无法证明基准有效。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hws_formal_math import benchmark

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "data" / "index"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def fixtures(tmp_path):
    """临时用例目录（探活用，不污染仓库 fixtures）"""
    d = tmp_path / "fixtures"
    d.mkdir()
    return d


class TestRetrievalProbe:
    """检索基准探活"""

    def test_good_implementation_passes(self):
        """好实现（真检索器）→ 达标"""
        result = benchmark.run_retrieval_suite(FIXTURES_DIR, INDEX_PATH)
        assert result["passed"] is True
        assert result["recall_at_10"] >= benchmark.RECALL_AT_K_MIN

    def test_bad_implementation_fails(self, fixtures, monkeypatch):
        """坏实现（检索恒返回空）→ 必须判未达标"""
        cases = [{"id": "c1", "query": "加法结合律", "ground_truth": ["add_assoc"], "domain": "algebra"}]
        (fixtures / "retrieval_cases.json").write_text(
            json.dumps(cases, ensure_ascii=False), encoding="utf-8"
        )

        from hws_formal_math.engine.retriever import Retriever

        # 注入缺陷：检索恒返回空列表
        monkeypatch.setattr(Retriever, "search", lambda self, q, top_k=10: [])

        result = benchmark.run_retrieval_suite(fixtures, INDEX_PATH)
        assert result["passed"] is False, "坏实现必须被判未达标（否则基准是假门）"
        assert result["recall_at_10"] == 0.0

    def test_wrong_ranking_fails(self, fixtures, monkeypatch):
        """坏实现（排序反转，真值沉底）→ 必须判未达标"""
        cases = [{"id": "c1", "query": "add_assoc", "ground_truth": ["add_assoc"], "domain": "algebra"}]
        (fixtures / "retrieval_cases.json").write_text(
            json.dumps(cases, ensure_ascii=False), encoding="utf-8"
        )

        from hws_formal_math.engine.retriever import Retriever, SearchResult

        def reversed_search(self, query, top_k=10):
            # 真值排最后，前面塞满不相关项 → MRR 极低
            filler = [
                SearchResult(
                    theorem="filler_%d" % i, module="M", signature="", score=1.0,
                    match_fields=[], dep_distance=0, source="index",
                )
                for i in range(10)
            ]
            filler.append(SearchResult(
                theorem="add_assoc", module="M", signature="", score=0.1,
                match_fields=[], dep_distance=0, source="index",
            ))
            return filler

        monkeypatch.setattr(Retriever, "search", reversed_search)

        result = benchmark.run_retrieval_suite(fixtures, INDEX_PATH)
        assert result["passed"] is False
        assert result["mrr"] < benchmark.MRR_MIN


class TestDepgraphProbe:
    """依赖图基准探活"""

    def test_good_implementation_passes(self):
        """好实现 → 达标"""
        result = benchmark.run_depgraph_suite(FIXTURES_DIR, INDEX_PATH)
        assert result["passed"] is True

    def test_bad_implementation_fails(self, fixtures, monkeypatch):
        """坏实现（漏检断链：broken_refs 恒空）→ 必须判未达标"""
        cases = [{
            "id": "d1",
            "theorems": ["add_assoc"],
            "expected_nodes": 1,
            "expected_edges": 0,
            "expected_broken_refs": ["MissingTheorem"],
            "expected_index_gaps": [],
        }]
        (fixtures / "depgraph_cases.json").write_text(
            json.dumps(cases, ensure_ascii=False), encoding="utf-8"
        )

        from hws_formal_math.engine.depgraph import DependencyGraph, DepGraphResult

        def broken(self, theorems):
            # 漏检断链：broken_refs 恒空
            return DepGraphResult(nodes=[], edges=[], broken_refs=[], index_gaps=[], shortest_paths={})

        monkeypatch.setattr(DependencyGraph, "build", broken)

        result = benchmark.run_depgraph_suite(fixtures, INDEX_PATH)
        assert result["passed"] is False, "漏检断链必须被判未达标"
        assert result["broken_ref_detection_rate"] < benchmark.BROKEN_REF_DETECTION_MIN

    def test_index_gap_confusion_fails(self, fixtures, monkeypatch):
        """坏实现（把 index_gap 当断链，违反 K2）→ 必须判未达标"""
        cases = [{
            "id": "d1",
            "theorems": ["add_assoc"],
            "expected_nodes": 1,
            "expected_edges": 2,
            "expected_broken_refs": [],
            "expected_index_gaps": ["Mathlib.Init"],
        }]
        (fixtures / "depgraph_cases.json").write_text(
            json.dumps(cases, ensure_ascii=False), encoding="utf-8"
        )

        from hws_formal_math.engine.depgraph import DependencyGraph, DepGraphResult, DepGraphNode

        def confused(self, theorems):
            # 违反 K2：把未覆盖模块误判为断链
            return DepGraphResult(
                nodes=[DepGraphNode(id="add_assoc", module="M")],
                edges=[],
                broken_refs=["Mathlib.Init"],
                index_gaps=[],
                shortest_paths={},
            )

        monkeypatch.setattr(DependencyGraph, "build", confused)

        result = benchmark.run_depgraph_suite(fixtures, INDEX_PATH)
        assert result["passed"] is False
        assert result["index_gap_discrimination_rate"] < benchmark.INDEX_GAP_DISCRIMINATION_MIN


class TestSkeletonProbe:
    """骨架基准探活"""

    def test_missing_snapshots_not_enabled(self, tmp_path):
        """快照缺失 → not_enabled（不冒充通过）"""
        from hws_formal_math.config import Config

        cfg = Config()
        cfg.data_dir = tmp_path / "no_such_data"
        result = benchmark.run_skeleton_suite(FIXTURES_DIR, cfg)
        assert result["not_enabled"] is True
        assert result["not_enabled_reason"] == "snapshots_missing"
        assert result["passed"] is False, "未启用不得冒充通过"

    def test_kernel_unavailable_not_enabled(self, tmp_path):
        """内核不可用 → not_enabled（与'跑了没过'同码不同义）"""
        from hws_formal_math.config import Config

        snapshots = tmp_path / "snapshots" / "v1"
        snapshots.mkdir(parents=True)
        (snapshots / "snapshots.json").write_text("[]", encoding="utf-8")

        cfg = Config()
        cfg.data_dir = tmp_path
        result = benchmark.run_skeleton_suite(FIXTURES_DIR, cfg)
        assert result["not_enabled"] is True
        assert result["not_enabled_reason"] == "kernel_unavailable"


class TestBenchmarkAggregate:
    """汇总口径探活"""

    def test_not_enabled_suite_blocks_all_passed(self, tmp_path):
        """任一 not_enabled 套件 → all_passed 必须为 False"""
        from hws_formal_math.config import Config

        cfg = Config()
        cfg.data_dir = tmp_path / "no_such_data"  # 触发 snapshots_missing

        results = benchmark.run_all(FIXTURES_DIR, INDEX_PATH, config=cfg)
        assert results["all_passed"] is False
        assert "skeleton" in results["not_enabled_suites"]

    def test_unknown_suite_raises(self):
        """未知名套件 → BenchError（不静默通过）"""
        with pytest.raises(benchmark.BenchError):
            benchmark.run_all(FIXTURES_DIR, INDEX_PATH, suites=["nonexistent"])

    def test_thresholds_reflect_code_constants(self):
        """阈值反射自代码常量（分母不许悄悄变小）"""
        result = benchmark.run_retrieval_suite(FIXTURES_DIR, INDEX_PATH)
        assert result["thresholds"]["recall_at_10_min"] == benchmark.RECALL_AT_K_MIN
        assert result["thresholds"]["mrr_min"] == benchmark.MRR_MIN
