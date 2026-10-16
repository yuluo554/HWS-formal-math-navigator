"""依赖图构建器（确定性图算法）"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
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
        self.modules: set = set()  # 所有被覆盖的模块
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
                    self.modules.add(data.get("module", ""))
    
    def build(self, theorems: List[str]) -> DepGraphResult:
        """
        构建依赖图
        
        K2 口径：index_gap ≠ 定理不存在
        
        Args:
            theorems: 定理列表
            
        Returns:
            DepGraphResult: 依赖图结果
        """
        # 构建图结构
        graph, nodes = self._build_graph(theorems)
        
        # 检测断链和 index_gap
        broken_refs, index_gaps = self._detect_broken_refs(graph)
        
        # 计算最短路径（从第一个节点开始）
        shortest_paths = {}
        if nodes:
            shortest_paths = self._find_shortest_paths(graph, nodes[0])
        
        # 构建边列表
        edges = []
        for from_node, deps in graph.items():
            for to_node in deps:
                edges.append(DepGraphEdge(
                    from_node=from_node,
                    to_node=to_node,
                    type="depends_on"
                ))
        
        return DepGraphResult(
            nodes=[DepGraphNode(id=n, module=self.index.get(n, {}).get("module", "")) for n in nodes],
            edges=edges,
            broken_refs=broken_refs,
            index_gaps=index_gaps,
            shortest_paths=shortest_paths
        )
    
    def _build_graph(self, theorems: List[str]) -> tuple:
        """
        构建图结构
        
        Args:
            theorems: 定理列表
            
        Returns:
            Tuple[graph, nodes]
        """
        graph = {}
        nodes = []
        
        for theorem in theorems:
            if theorem not in self.index:
                continue
            
            nodes.append(theorem)
            deps = self.index[theorem].get("deps", [])
            graph[theorem] = deps
        
        return graph, nodes
    
    def _detect_broken_refs(self, graph: Dict[str, List[str]]) -> tuple:
        """
        检测断链与 index_gap

        K2 口径：index_gap ≠ 定理不存在。

        本索引的 deps 字段承载 Lean `import` 提取出的**模块名**（见 plan/02 §一 步骤 3），
        故分类规则按"依赖项形态"确定（纯函数，不猜测）：

        | 依赖项形态 | 在索引中 | 分类 |
        |---|---|---|
        | 模块名（含 `.`） | 被覆盖 | 正常边（不计入 gap/broken） |
        | 模块名（含 `.`） | 未覆盖 | **index_gap**（索引未覆盖该模块，绝不判"定理不存在"） |
        | 裸名（不含 `.`） | 在索引 | 正常边 |
        | 裸名（不含 `.`） | 不在索引 | **broken_ref**（引用定理不在索引中） |

        Args:
            graph: 依赖图（{定理名: [依赖项...]}）

        Returns:
            Tuple[broken_refs, index_gaps]
        """
        broken_refs = []
        index_gaps = []

        for node, deps in graph.items():
            for dep in deps:
                if dep in self.index:
                    continue  # 定理级依赖，已被索引收录
                if "." in dep:
                    # 模块级依赖：covered 则正常，未覆盖则 index_gap
                    if not self._is_module_covered(dep):
                        index_gaps.append(dep)
                else:
                    # 裸名依赖：定理级引用但索引未收录 → 断链
                    broken_refs.append(dep)

        # 去重（确定性：排序）
        broken_refs = sorted(set(broken_refs))
        index_gaps = sorted(set(index_gaps))

        return broken_refs, index_gaps
    
    def _is_module_covered(self, module_name: str) -> bool:
        """
        检查模块是否被索引覆盖

        K2 口径：index_gap ≠ 定理不存在。
        本项目的 deps 字段承载 Lean `import` 语句提取出的**模块名**，
        故"覆盖"的判据是：该模块名下确有定理被索引收录（self.modules 由索引实际内容构建）。

        Args:
            module_name: 模块名（如 Mathlib.Algebra.Group.Defs）

        Returns:
            bool: 该模块是否被索引覆盖
        """
        return module_name in self.modules
    
    def _find_shortest_paths(self, graph: Dict[str, List[str]], start: str) -> Dict[str, List[str]]:
        """
        BFS 求最短路径
        
        Args:
            graph: 依赖图
            start: 起始节点
            
        Returns:
            Dict[node, path]
        """
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
        
        K8 口径：HTML 0 外链
        
        Args:
            result: 依赖图结果
            output_path: 输出路径
        """
        # 生成内嵌 CSS/JS 的 HTML
        html_content = self._generate_html(result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html(self, result: DepGraphResult) -> str:
        """
        生成 HTML 内容
        
        Args:
            result: 依赖图结果
            
        Returns:
            HTML 字符串
        """
        # 生成节点列表
        nodes_html = "\n".join(
            f'            <li>{node.id} ({node.module})</li>'
            for node in result.nodes
        )
        
        # 生成边列表
        edges_html = "\n".join(
            f'            <li>{edge.from_node} → {edge.to_node}</li>'
            for edge in result.edges
        )
        
        # 生成断链列表
        broken_html = "\n".join(
            f'            <li class="broken">{ref}</li>'
            for ref in result.broken_refs
        ) if result.broken_refs else '            <li>无</li>'
        
        # 生成 index_gap 列表
        gaps_html = "\n".join(
            f'            <li class="gap">{gap}</li>'
            for gap in result.index_gaps
        ) if result.index_gaps else '            <li>无</li>'
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>依赖图报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        .section {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 5px 0; border-bottom: 1px solid #eee; }}
        .broken {{ color: #d32f2f; font-weight: bold; }}
        .gap {{ color: #f57c00; font-weight: bold; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #1976d2; }}
        .stat-label {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>依赖图报告</h1>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{len(result.nodes)}</div>
            <div class="stat-label">节点数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(result.edges)}</div>
            <div class="stat-label">边数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(result.broken_refs)}</div>
            <div class="stat-label">断链</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(result.index_gaps)}</div>
            <div class="stat-label">Index Gaps</div>
        </div>
    </div>
    
    <div class="section">
        <h2>节点</h2>
        <ul>
{nodes_html}
        </ul>
    </div>
    
    <div class="section">
        <h2>边</h2>
        <ul>
{edges_html}
        </ul>
    </div>
    
    <div class="section">
        <h2>断链（Broken Refs）</h2>
        <p>索引覆盖范围内但当前定理未收录的依赖</p>
        <ul>
{broken_html}
        </ul>
    </div>
    
    <div class="section">
        <h2>Index Gaps</h2>
        <p>索引未覆盖的模块中的定理（可能是用户误导）</p>
        <ul>
{gaps_html}
        </ul>
    </div>
</body>
</html>"""
        
        return html
