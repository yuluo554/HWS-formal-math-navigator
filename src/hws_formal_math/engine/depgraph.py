"""依赖图构建器（确定性图算法）"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
from collections import deque


@dataclass
class DepGraphNode:
    """依赖图节点"""
    id: str
    module: str


@dataclass
class DepGraphEdge:
    """依赖图边"""
    from_node: str
    to_node: str
    type: str


@dataclass
class DepGraphResult:
    """依赖图结果"""
    nodes: List[DepGraphNode]
    edges: List[DepGraphEdge]
    broken_refs: List[str]
    index_gaps: List[str]
    shortest_paths: Dict[str, List[str]]


class DependencyGraph:
    """依赖图构建器"""
    
    def __init__(self, index_path: Path):
        """
        初始化依赖图构建器
        
        Args:
            index_path: 索引元数据路径
        """
        self.index_path = index_path
        self.index: Dict[str, Dict[str, Any]] = {}
        self._load_index()
    
    def _load_index(self):
        """加载索引元数据"""
        index_file = self.index_path / "theorems.jsonl"
        if not index_file.exists():
            raise FileNotFoundError(f"索引文件不存在: {index_file}")
        
        with open(index_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    self.index[data["name"]] = data
    
    def build(self, theorems: List[str]) -> DepGraphResult:
        """
        构建依赖图
        
        Args:
            theorems: 定理列表
            
        Returns:
            DepGraphResult: 依赖图结果
        """
        # TODO: 实现依赖图构建
        raise NotImplementedError("依赖图构建待实现")
    
    def _build_graph(self, theorems: List[str]) -> tuple:
        """构建图结构"""
        # TODO: 实现
        raise NotImplementedError("_build_graph 待实现")
    
    def _detect_broken_refs(self, graph: Dict[str, List[str]]) -> tuple:
        """检测断链"""
        broken_refs = []
        index_gaps = []
        
        for node, deps in graph.items():
            for dep in deps:
                if dep not in self.index:
                    # 检查是否在索引覆盖范围内
                    # 简化判断：如果模块名在索引中出现过，则可能是断链
                    # 否则是 index_gap
                    if self._is_module_covered(dep):
                        broken_refs.append(dep)
                    else:
                        index_gaps.append(dep)
        
        return broken_refs, index_gaps
    
    def _is_module_covered(self, theorem: str) -> bool:
        """检查定理所在模块是否被索引覆盖"""
        # TODO: 实现
        raise NotImplementedError("_is_module_covered 待实现")
    
    def _find_shortest_paths(self, graph: Dict[str, List[str]], start: str) -> Dict[str, List[str]]:
        """BFS 求最短路径"""
        paths = {}
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            node, path = queue.popleft()
            paths[node] = path
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return paths
    
    def export_html(self, result: DepGraphResult, output_path: Path) -> None:
        """
        导出 HTML（0 外链）
        
        Args:
            result: 依赖图结果
            output_path: 输出路径
        """
        # TODO: 实现 HTML 导出
        # 内嵌 CSS/JS，无 CDN 引用
        raise NotImplementedError("HTML 导出待实现")
