"""检索器（BM25，零模型）"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class SearchResult:
    """检索结果"""
    theorem: str
    module: str
    signature: str
    score: float
    match_fields: List[str]
    dep_distance: int
    source: str


class Retriever:
    """BM25 检索器（零模型依赖）"""
    
    def __init__(self, index_path: Path):
        """
        初始化检索器
        
        Args:
            index_path: 索引元数据路径
        """
        self.index_path = index_path
        self.index: List[Dict[str, Any]] = []
        self._load_index()
    
    def _load_index(self):
        """加载索引元数据"""
        index_file = self.index_path / "theorems.jsonl"
        if not index_file.exists():
            raise FileNotFoundError(f"索引文件不存在: {index_file}")
        
        with open(index_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.index.append(json.loads(line))
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        检索定理
        
        Args:
            query: 查询关键词
            top_k: 返回结果数
            
        Returns:
            List[SearchResult]: 检索结果列表
        """
        # TODO: 实现 BM25 检索
        raise NotImplementedError("Retriever.search 待实现")
    
    def _compute_bm25_score(self, query_terms: List[str], doc: Dict[str, Any]) -> float:
        """计算 BM25 分数"""
        # TODO: 实现 BM25 评分
        raise NotImplementedError("BM25 评分待实现")
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 简单按空格和符号分词
        import re
        tokens = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        return tokens
