"""桌面查看器：业务编排层（零 Qt，可在无 GUI 环境测试）

口径（plan/04 §3.4）：查看器不是"能开窗口"，而是**能跑通一条从输入到产物的链路**：
    查询 → BM25 检索结果 → 选定定理 → 依赖图 → 导出 HTML（0 外链）
本模块只依赖引擎层，不 import Qt；`main.py` 的窗口只做"控件 ↔ 本模块"的接线。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config
from ..core import Orchestrator


@dataclass
class ViewerState:
    """查看器一次会话的状态（可序列化，便于测试断言）"""

    query: str = ""
    results: List[Dict[str, Any]] = field(default_factory=list)
    selected: Optional[str] = None
    graph: Optional[Dict[str, Any]] = None
    exported: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "result_count": len(self.results),
            "results": self.results,
            "selected": self.selected,
            "graph": self.graph,
            "exported": self.exported,
            "error": self.error,
        }


class ViewerController:
    """查看器控制器：检索 / 构图 / 导出三件事"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self._orchestrator: Optional[Orchestrator] = None
        self.state = ViewerState()

    @property
    def orchestrator(self) -> Orchestrator:
        if self._orchestrator is None:
            self._orchestrator = Orchestrator(self.config)
        return self._orchestrator

    def index_summary(self) -> Dict[str, Any]:
        """索引概况（查看器首屏展示；数据缺失时返回 error 而不是抛异常）"""
        manifest = self.config.index_path / "manifest.json"
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return {"error": f"索引 manifest 不可读: {exc}"}
        return {
            "theorem_count": data.get("theorem_count"),
            "index_kind": data.get("index_kind", "full"),
            "upstream_commit": data.get("upstream_commit") or data.get("commit_hash"),
            "path": str(self.config.index_path),
        }

    def search(self, query: str, top_k: int = 10) -> ViewerState:
        """执行检索；空查询/无结果都落在 state.error，不抛异常（GUI 需要可展示的错误）"""
        query = (query or "").strip()
        self.state = ViewerState(query=query)
        if not query:
            self.state.error = "请输入查询内容"
            return self.state
        try:
            results = self.orchestrator.search(query, top_k=top_k)
        except Exception as exc:  # 索引缺失等 → 展示错误，不崩窗口
            self.state.error = f"检索失败: {exc}"
            return self.state
        self.state.results = results
        if not results:
            self.state.error = f"未找到与 '{query}' 相关的定理"
        return self.state

    def build_graph(self, theorem: str, extra: Optional[List[str]] = None) -> ViewerState:
        """以选定定理为起点构建依赖图"""
        names = [theorem] + [t for t in (extra or []) if t != theorem]
        try:
            result = self.orchestrator.depgraph.build(names)
        except Exception as exc:
            self.state.error = f"依赖图构建失败: {exc}"
            return self.state
        self.state.selected = theorem
        self.state.graph = {
            "nodes": [{"id": n.id, "module": n.module} for n in result.nodes],
            "edges": [{"from": e.from_node, "to": e.to_node} for e in result.edges],
            "broken_refs": list(result.broken_refs),
            "index_gaps": list(result.index_gaps),
            "shortest_paths": result.shortest_paths,
        }
        return self.state

    def export_html(self, output: Path, theorem: Optional[str] = None) -> Path:
        """导出依赖图 HTML（0 外链）；未构图时先构图"""
        target = theorem or self.state.selected
        if not target:
            raise ValueError("尚未选定定理，无法导出")
        if self.state.graph is None or self.state.selected != target:
            self.build_graph(target)
        if self.state.graph is None:
            raise ValueError(self.state.error or "依赖图不可用")
        result = self.orchestrator.depgraph.build(
            [target] + [n["id"] for n in self.state.graph["nodes"] if n["id"] != target]
        )
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.orchestrator.depgraph.export_html(result, output)
        self.state.exported.append(str(output))
        return output
