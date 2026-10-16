"""基准套件（确定性指标计算）

设计口径（plan/03-基准套件设计.md）：
- L3 基准测试：检索 Recall@k / MRR、骨架编译通过率、依赖图完整率
- 真值来源 = tests/fixtures/*.json（样本驱动），阈值写进代码常量（规则驱动）
- 坏实现必须被判未达标（探活，见 tests/test_bench_probe.py）
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config
from ..engine.depgraph import DependencyGraph
from ..engine.kernel import KernelVerifier
from ..engine.retriever import Retriever
from ..engine.skeleton_gen import SkeletonGenerator

# ---------------------------------------------------------------- 阈值常量
# 分母反射自代码常量：改阈值必须改这里，不许悄悄做小分母
RECALL_AT_K_MIN = 0.70
MRR_MIN = 0.50
PASS_NO_SORRY_MIN = 0.30
PASS_WITH_SORRY_MIN = 0.50
DEPGRAPH_COMPLETENESS_MIN = 0.90
BROKEN_REF_DETECTION_MIN = 1.00
INDEX_GAP_DISCRIMINATION_MIN = 1.00

# 覆盖度最低项（分母来源 = 代码常量，非文档）
DOMAIN_MIN_COVERAGE = {
    "algebra": 5,
    "analysis": 5,
    "number_theory": 5,
    "combinatorics": 5,
}

SUITE_NAMES = ("retrieval", "skeleton", "depgraph")
ALL_SUITES = SUITE_NAMES


class BenchError(Exception):
    """基准运行错误（用法/数据问题）"""


def _load_cases(path: Path) -> List[Dict[str, Any]]:
    """加载基准用例（确定性：按 id 排序）"""
    if not path.exists():
        raise BenchError(f"基准用例文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    return sorted(cases, key=lambda c: c.get("id", ""))


def _rate(numerator: int, denominator: int) -> float:
    """比率（分母为 0 时返回 0.0，不抛异常）"""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


# ---------------------------------------------------------------- 检索基准


def run_retrieval_suite(fixtures_dir: Path, index_path: Path, top_k: int = 10) -> Dict[str, Any]:
    """检索基准：Recall@k / MRR（样本驱动，真值来自 fixtures）"""
    cases = _load_cases(fixtures_dir / "retrieval_cases.json")
    retriever = Retriever(index_path)

    hits = 0
    reciprocal_ranks: List[float] = []
    by_domain: Dict[str, Dict[str, Any]] = {}

    for case in cases:
        domain = case.get("domain", "other")
        bucket = by_domain.setdefault(domain, {"cases": 0, "hits": 0})
        bucket["cases"] += 1

        results = retriever.search(case["query"], top_k=top_k)
        names = [r.theorem for r in results]
        truth = set(case.get("ground_truth", []))

        rank = None
        for i, name in enumerate(names, 1):
            if name in truth:
                rank = i
                break

        if rank is not None:
            hits += 1
            bucket["hits"] += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    for domain, bucket in by_domain.items():
        bucket["recall"] = _rate(bucket["hits"], bucket["cases"])

    recall = _rate(hits, len(cases))
    mrr = round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4) if reciprocal_ranks else 0.0

    passed = recall >= RECALL_AT_K_MIN and mrr >= MRR_MIN
    return {
        "suite": "retrieval",
        "total_cases": len(cases),
        "recall_at_k": recall,
        "recall_at_10": recall,
        "mrr": mrr,
        "by_domain": by_domain,
        "thresholds": {
            "recall_at_10_min": RECALL_AT_K_MIN,
            "mrr_min": MRR_MIN,
        },
        "passed": passed,
    }


# ---------------------------------------------------------------- 骨架基准


def run_skeleton_suite(
    fixtures_dir: Path,
    config: Config,
    snapshots_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """骨架基准：编译通过率

    真值来源 = 预置模型输出快照（plan/03 §三：不依赖当场跑模型）+ Lean 内核判定。

    两种"未启用"情形（均 passed=False，文本可区分）：
      - 快照缺失：数据未随包提供 → not_enabled_reason="snapshots_missing"
      - 内核不可用：无 Lean 工具链 → 内核判定无法执行 → not_enabled_reason="kernel_unavailable"
    """
    verifier = KernelVerifier(config.lean.lean_path)
    snapshot_file = _resolve_snapshot_file(snapshots_dir or config.data_dir / "snapshots")

    if snapshot_file is None:
        return {
            "suite": "skeleton",
            "not_enabled": True,
            "not_enabled_reason": "snapshots_missing",
            "notes": "预置模型输出快照缺失（data/snapshots/v1/snapshots.json），骨架基准未启用",
            "total_cases": 0,
            "passed": False,
        }

    cases = _load_cases(snapshot_file)

    if not verifier.is_available():
        return {
            "suite": "skeleton",
            "not_enabled": True,
            "not_enabled_reason": "kernel_unavailable",
            "notes": "Lean 工具链不可用，骨架基准的内核真值无法判定（K3 口径：内核判定与模型生成分离）",
            "total_cases": len(cases),
            "passed": False,
        }

    pass_no_sorry = 0
    pass_with_sorry = 0
    fail = 0
    by_domain: Dict[str, Dict[str, int]] = {}

    for case in cases:
        domain = case.get("domain", "other")
        bucket = by_domain.setdefault(
            domain, {"pass_no_sorry": 0, "pass_with_sorry": 0, "fail": 0}
        )

        verification = verifier.verify(case["code"])
        status = verification.status.value

        if status == "PASS_NO_SORRY":
            pass_no_sorry += 1
            bucket["pass_no_sorry"] += 1
        elif status == "PASS_WITH_SORRY":
            pass_with_sorry += 1
            bucket["pass_with_sorry"] += 1
        else:
            fail += 1
            bucket["fail"] += 1

    total = len(cases)
    no_sorry_rate = _rate(pass_no_sorry, total)
    with_sorry_rate = _rate(pass_with_sorry, total)
    fail_rate = _rate(fail, total)

    passed = no_sorry_rate >= PASS_NO_SORRY_MIN and with_sorry_rate >= PASS_WITH_SORRY_MIN
    return {
        "suite": "skeleton",
        "not_enabled": False,
        "total_cases": total,
        "pass_no_sorry": pass_no_sorry,
        "pass_with_sorry": pass_with_sorry,
        "fail": fail,
        "pass_no_sorry_rate": no_sorry_rate,
        "pass_with_sorry_rate": with_sorry_rate,
        "fail_rate": fail_rate,
        "kernel_available": True,
        "by_domain": by_domain,
        "thresholds": {
            "pass_no_sorry_min": PASS_NO_SORRY_MIN,
            "pass_with_sorry_min": PASS_WITH_SORRY_MIN,
        },
        "passed": passed,
    }


def _resolve_snapshot_file(snapshots_dir: Path) -> Optional[Path]:
    """定位预置模型输出快照（版本化目录优先）"""
    candidates = [
        snapshots_dir / "v1" / "snapshots.json",
        snapshots_dir / "snapshots.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


# ---------------------------------------------------------------- 依赖图基准


def run_depgraph_suite(fixtures_dir: Path, index_path: Path) -> Dict[str, Any]:
    """依赖图基准：节点/边完整率、断链检出率、index_gap 区分率"""
    cases = _load_cases(fixtures_dir / "depgraph_cases.json")
    graph_builder = DependencyGraph(index_path)

    node_matches = 0
    edge_matches = 0
    broken_matches = 0
    gap_matches = 0
    total_nodes = 0
    total_edges = 0
    total_broken = 0
    total_gaps = 0
    detail: List[Dict[str, Any]] = []

    for case in cases:
        result = graph_builder.build(case["theorems"])

        exp_nodes = case.get("expected_nodes", 0)
        exp_edges = case.get("expected_edges", 0)
        exp_broken = sorted(case.get("expected_broken_refs", []))
        exp_gaps = sorted(case.get("expected_index_gaps", []))

        actual_nodes = len(result.nodes)
        actual_edges = len(result.edges)
        actual_broken = sorted(result.broken_refs)
        actual_gaps = sorted(result.index_gaps)

        node_matches += 1 if actual_nodes == exp_nodes else 0
        edge_matches += 1 if actual_edges == exp_edges else 0
        broken_matches += 1 if actual_broken == exp_broken else 0
        gap_matches += 1 if actual_gaps == exp_gaps else 0

        total_nodes += 1
        total_edges += 1
        total_broken += 1
        total_gaps += 1

        detail.append({
            "id": case["id"],
            "nodes_ok": actual_nodes == exp_nodes,
            "edges_ok": actual_edges == exp_edges,
            "broken_refs_ok": actual_broken == exp_broken,
            "index_gaps_ok": actual_gaps == exp_gaps,
        })

    completeness = _rate(node_matches + edge_matches, total_nodes + total_edges)
    broken_rate = _rate(broken_matches, total_broken)
    gap_rate = _rate(gap_matches, total_gaps)

    passed = (
        completeness >= DEPGRAPH_COMPLETENESS_MIN
        and broken_rate >= BROKEN_REF_DETECTION_MIN
        and gap_rate >= INDEX_GAP_DISCRIMINATION_MIN
    )
    return {
        "suite": "depgraph",
        "total_cases": len(cases),
        "completeness": completeness,
        "broken_ref_detection_rate": broken_rate,
        "index_gap_discrimination_rate": gap_rate,
        "detail": detail,
        "thresholds": {
            "completeness_min": DEPGRAPH_COMPLETENESS_MIN,
            "broken_ref_detection_min": BROKEN_REF_DETECTION_MIN,
            "index_gap_discrimination_min": INDEX_GAP_DISCRIMINATION_MIN,
        },
        "passed": passed,
    }


# ---------------------------------------------------------------- 覆盖度


def compute_domain_coverage(index_path: Path) -> Dict[str, Any]:
    """覆盖度双登记：最低项（代码常量）vs 实际项（索引元数据）"""
    index_file = index_path / "theorems.jsonl"
    if not index_file.exists():
        raise BenchError(f"索引文件不存在: {index_file}")

    actual: Dict[str, int] = {d: 0 for d in DOMAIN_MIN_COVERAGE}
    with open(index_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            module = row.get("module", "")
            for domain in DOMAIN_MIN_COVERAGE:
                if domain.lower() in module.lower():
                    actual[domain] += 1

    domains = {}
    for domain, minimum in DOMAIN_MIN_COVERAGE.items():
        count = actual.get(domain, 0)
        domains[domain] = {
            "min_theorems": minimum,
            "actual": count,
            "status": "verified" if count >= minimum else "insufficient",
        }

    return {
        "domains": domains,
        "all_verified": all(d["status"] == "verified" for d in domains.values()),
    }


# ---------------------------------------------------------------- 编排


def run_suite(
    suite: str,
    fixtures_dir: Path,
    index_path: Path,
    config: Optional[Config] = None,
    top_k: int = 10,
) -> Dict[str, Any]:
    """运行单个基准套件"""
    if suite == "retrieval":
        return run_retrieval_suite(fixtures_dir, index_path, top_k=top_k)
    if suite == "skeleton":
        cfg = config or Config()
        return run_skeleton_suite(fixtures_dir, cfg, snapshots_dir=cfg.data_dir / "snapshots")
    if suite == "depgraph":
        return run_depgraph_suite(fixtures_dir, index_path)
    raise BenchError(f"未知套件: {suite}")


def run_all(
    fixtures_dir: Path,
    index_path: Path,
    config: Optional[Config] = None,
    suites: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """运行全部（或指定）基准套件

    "未启用"套件不冒充通过：not_enabled=True 的套件使 all_passed=False，
    但文本可区分（not_enabled_reason）——"整套件数据缺失/依赖缺失"与"跑了没过"同码不同义。
    """
    selected = list(suites) if suites else list(ALL_SUITES)
    for name in selected:
        if name not in SUITE_NAMES:
            raise BenchError(f"未知套件: {name}")

    results = {}
    for name in selected:
        results[name] = run_suite(name, fixtures_dir, index_path, config=config)

    results["coverage"] = compute_domain_coverage(index_path)
    results["all_passed"] = all(
        results[name].get("passed", False) and not results[name].get("not_enabled", False)
        for name in selected
    )
    results["not_enabled_suites"] = [
        name for name in selected if results[name].get("not_enabled", False)
    ]
    return results
