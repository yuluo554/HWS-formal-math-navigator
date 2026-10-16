"""编排层：主流程编排（检索 → 骨架 → 验证 → 报告）"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import date

from ..config import Config
from ..exceptions import (
    HWSFormalMathError, ModelDisabledError, LeanNotAvailableError,
    IndexNotFoundError, ExitCode
)
from ..engine import Retriever, SkeletonGenerator, KernelVerifier, DependencyGraph


@dataclass
class OrchestrationResult:
    """编排结果"""
    status: str  # PASS_NO_SORRY, PASS_WITH_SORRY, FAIL, SKIPPED, INDEX_GAP
    proposition: str
    skeleton: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    kernel_verification: Optional[Dict[str, Any]] = field(default_factory=dict)
    retrieval_results: List[Dict[str, Any]] = field(default_factory=list)
    depgraph_result: Optional[Dict[str, Any]] = field(default_factory=dict)
    generation_date: str = field(default_factory=lambda: date.today().isoformat())


class Orchestrator:
    """主流程编排器

    流程：检索 → 骨架生成 → 内核验证 → 依赖图 → 报告
    """

    def __init__(self, config: Config):
        """
        初始化编排器

        Args:
            config: 配置对象
        """
        self.config = config
        self._init_engines()

    def _init_engines(self):
        """初始化各引擎模块"""
        # 检索器
        index_path = self.config.index_path
        if not index_path.exists():
            raise IndexNotFoundError(f"索引目录不存在: {index_path}")
        self.retriever = Retriever(index_path)

        # 骨架生成器
        self.skeleton_gen = SkeletonGenerator(self.config)

        # 内核验证器
        self.kernel = KernelVerifier(self.config.lean.lean_path)

        # 依赖图构建器
        self.depgraph = DependencyGraph(index_path)

    def run(self, proposition: str) -> OrchestrationResult:
        """
        执行完整流程：检索 → 骨架生成 → 内核验证 → 依赖图

        Args:
            proposition: 数学命题

        Returns:
            OrchestrationResult: 编排结果
        """
        errors = []
        warnings = []
        retrieval_results = []
        kernel_result = None
        depgraph_result = None
        skeleton = None

        # 步骤 1：检索相关定理
        try:
            search_results = self.retriever.search(proposition, top_k=10)
            retrieval_results = [
                {
                    "theorem": r.theorem,
                    "module": r.module,
                    "score": r.score,
                    "match_fields": r.match_fields,
                    "signature": r.signature,
                }
                for r in search_results
            ]
        except Exception as e:
            errors.append(f"检索失败: {e}")

        # 步骤 2：骨架生成
        try:
            gen_result = self.skeleton_gen.generate(proposition, use_model=self.config.model.enabled)
            skeleton = gen_result.code
            if gen_result.uncertainties:
                warnings.extend(gen_result.uncertainties)
        except ModelDisabledError:
            # 模型关闭，尝试将命题作为已形式化的 Lean 代码处理
            stripped = proposition.strip()
            if stripped.startswith("theorem ") or stripped.startswith("lemma ") or stripped.startswith("def "):
                skeleton = proposition
            else:
                errors.append(
                    "模型已关闭且命题未形式化。请提供已形式化的 Lean 代码，或启用模型端点。"
                )
        except Exception as e:
            errors.append(f"骨架生成失败: {e}")

        # 步骤 3：内核验证
        if skeleton:
            try:
                kernel_result = self.kernel.verify(skeleton)
                if kernel_result.status.value == "SKIPPED":
                    warnings.extend(kernel_result.warnings)
            except Exception as e:
                errors.append(f"内核验证失败: {e}")

        # 步骤 4：依赖图分析
        try:
            # 从骨架中提取定理名（简化实现）
            theorems = [r["theorem"] for r in retrieval_results[:5]]
            if skeleton:
                # 尝试从骨架中提取引用的定理
                import re
                refs = re.findall(r'\b(\w+_\w+)\b', skeleton)
                theorems.extend(refs[:5])

            if theorems:
                graph_result = self.depgraph.build(theorems[:10])
                depgraph_result = {
                    "nodes": [{"id": n.id, "module": n.module} for n in graph_result.nodes],
                    "edges": [{"from": e.from_node, "to": e.to_node} for e in graph_result.edges],
                    "broken_refs": graph_result.broken_refs,
                    "index_gaps": graph_result.index_gaps,
                }
        except Exception as e:
            warnings.append(f"依赖图分析失败: {e}")

        # 确定最终状态
        if kernel_result:
            status = kernel_result.status.value
        elif errors:
            status = "FAIL"
        else:
            status = "SKIPPED"

        return OrchestrationResult(
            status=status,
            proposition=proposition,
            skeleton=skeleton,
            errors=errors,
            warnings=warnings,
            kernel_verification={
                "status": kernel_result.status.value if kernel_result else None,
                "has_sorry": kernel_result.has_sorry if kernel_result else None,
                "sorry_count": kernel_result.sorry_count if kernel_result else None,
                "errors": kernel_result.errors if kernel_result else [],
            } if kernel_result else None,
            retrieval_results=retrieval_results,
            depgraph_result=depgraph_result,
        )

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """检索定理

        Args:
            query: 查询关键词
            top_k: 返回结果数

        Returns:
            检索结果列表
        """
        results = self.retriever.search(query, top_k)
        return [
            {
                "theorem": r.theorem,
                "module": r.module,
                "score": r.score,
                "match_fields": r.match_fields,
                "signature": r.signature,
            }
            for r in results
        ]

    def generate_skeleton(self, proposition: str, use_model: bool = True) -> str:
        """生成证明骨架

        Args:
            proposition: 数学命题
            use_model: 是否使用模型

        Returns:
            骨架代码
        """
        result = self.skeleton_gen.generate(proposition, use_model=use_model)
        return result.code

    def verify(self, code: str) -> Dict[str, Any]:
        """验证 Lean 代码

        Args:
            code: Lean 代码片段

        Returns:
            验证结果字典
        """
        result = self.kernel.verify(code)
        return {
            "status": result.status.value,
            "has_sorry": result.has_sorry,
            "sorry_count": result.sorry_count,
            "sorry_locations": result.sorry_locations,
            "errors": result.errors,
            "warnings": result.warnings,
        }
