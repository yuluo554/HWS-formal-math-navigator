"""检索器（BM25，零模型）"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import math
import re


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
    
    # BM25 参数
    K1 = 1.2
    B = 0.75
    
    def __init__(self, index_path: Path):
        """
        初始化检索器
        
        Args:
            index_path: 索引元数据路径
        """
        self.index_path = index_path
        self.index: List[Dict[str, Any]] = []
        self.doc_freq: Dict[str, int] = {}  # 文档频率
        self.avg_doc_len: float = 0.0
        self.aliases: Dict[str, str] = {}
        self._load_aliases()
        self._load_index()
        self._build_doc_freq()

    def _load_aliases(self):
        """加载确定性中文→Lean 词元别名表（规则优先，零模型依赖）

        别名表缺失时静默降级为空表（检索仍可用，只是中文查询命中率降低）——
        K5 口径：核心检索不得因可选数据缺失而不可用。
        """
        alias_file = self.index_path / "query_aliases.json"
        if not alias_file.exists():
            return
        with open(alias_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("term_aliases", {})
        # 长词优先：保证"加法结合律"整体映射先于"加法"匹配
        self.aliases = dict(sorted(raw.items(), key=lambda kv: -len(kv[0])))

    def _normalize_query(self, query: str) -> str:
        """查询预处理：中文概念 → Lean 词元（plan/02 §2.3 承诺的查询预处理）

        确定性规则：按别名表长度降序做一次性替换，命中即消费（不重叠替换）。
        未在表中的中文按原样保留，交由分词处理（不做猜测，不引入模型）。
        """
        if not self.aliases:
            return query
        result = query
        for term, token in self.aliases.items():
            if term and term in result:
                result = result.replace(term, f" {token} ")
        return result
    
    def _load_index(self):
        """加载索引元数据"""
        index_file = self.index_path / "theorems.jsonl"
        if not index_file.exists():
            raise FileNotFoundError(f"索引文件不存在: {index_file}")
        
        with open(index_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.index.append(json.loads(line))
    
    def _build_doc_freq(self):
        """构建文档频率和平均文档长度"""
        if not self.index:
            return
        
        # 计算文档频率（每个词出现在多少文档中）
        all_terms = set()
        total_len = 0
        
        for doc in self.index:
            # 合并所有字段的文本
            text = f"{doc.get('name', '')} {doc.get('signature', '')} {doc.get('module', '')}"
            terms = self._tokenize(text)
            total_len += len(terms)
            
            # 文档频率：每个词只计一次
            unique_terms = set(terms)
            for term in unique_terms:
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1
            all_terms.update(terms)
        
        self.avg_doc_len = total_len / len(self.index) if self.index else 0
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 按空格、下划线、符号分词，保留中文和英文
        # 将下划线替换为空格，以便 "add_assoc" 分成 "add" 和 "assoc"
        text = text.replace('_', ' ')
        tokens = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        return tokens
    
    def _get_doc_terms(self, doc: Dict[str, Any]) -> Dict[str, List[str]]:
        """获取文档各字段的分词结果"""
        return {
            'name': self._tokenize(doc.get('name', '')),
            'signature': self._tokenize(doc.get('signature', '')),
            'module': self._tokenize(doc.get('module', '')),
        }
    
    def _compute_bm25_score(self, query_terms: List[str], doc: Dict[str, Any]) -> float:
        """
        计算 BM25 分数
        
        Args:
            query_terms: 查询分词列表
            doc: 文档
            
        Returns:
            BM25 分数
        """
        if not query_terms:
            return 0.0
        
        score = 0.0
        doc_terms = self._get_doc_terms(doc)
        all_doc_terms = doc_terms['name'] + doc_terms['signature'] + doc_terms['module']
        doc_len = len(all_doc_terms)
        
        N = len(self.index)
        
        for term in query_terms:
            # 文档频率
            n_qi = self.doc_freq.get(term, 0)
            if n_qi == 0:
                continue
            
            # IDF 计算
            idf = math.log((N - n_qi + 0.5) / (n_qi + 0.5) + 1)
            
            # 词频（在所有字段中）
            tf = sum(1 for t in all_doc_terms if t == term)
            
            # BM25 公式
            numerator = tf * (self.K1 + 1)
            denominator = tf + self.K1 * (1 - self.B + self.B * doc_len / self.avg_doc_len)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def _get_match_fields(self, query_terms: List[str], doc: Dict[str, Any]) -> List[str]:
        """获取匹配的字段"""
        doc_terms = self._get_doc_terms(doc)
        match_fields = []
        
        for term in query_terms:
            if term in doc_terms['name']:
                match_fields.append('name')
            if term in doc_terms['signature']:
                match_fields.append('signature')
            if term in doc_terms['module']:
                match_fields.append('module')
        
        return list(set(match_fields))
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        检索定理
        
        Args:
            query: 查询关键词
            top_k: 返回结果数
            
        Returns:
            List[SearchResult]: 检索结果列表
        """
        query_terms = self._tokenize(self._normalize_query(query))
        
        if not query_terms:
            return []
        
        results = []
        for doc in self.index:
            score = self._compute_bm25_score(query_terms, doc)
            if score > 0:
                match_fields = self._get_match_fields(query_terms, doc)
                results.append(SearchResult(
                    theorem=doc.get('name', ''),
                    module=doc.get('module', ''),
                    signature=doc.get('signature', ''),
                    score=round(score, 6),
                    match_fields=match_fields,
                    dep_distance=0,  # 需要后续计算
                    source='index'
                ))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
