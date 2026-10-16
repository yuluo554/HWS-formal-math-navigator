"""规则优先解析器

纯正则 + 状态机解析 Lean 4 源码，不依赖 LLM。
遵循 K4（同输入同结果）和 K10（UTF-8 输出）口径。
"""

import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .ir import (
    LeanDeclaration,
    TheoremDecl,
    Definition,
    InductiveDecl,
    StructureDecl,
    ClassDecl,
    InstanceDecl,
    ModuleRef,
    ParseResult,
    DeclarationType
)


# 声明类型匹配模式
DECLARATION_PATTERNS = {
    DeclarationType.THEOREM: re.compile(
        r'^\s*theorem\s+(\w+)(?:\s+\{[^}]*\}|\s+\[[^\]]*\]|\s+\([^)]*\))*\s*:\s*'
    ),
    DeclarationType.LEMMA: re.compile(
        r'^\s*lemma\s+(\w+)(?:\s+\{[^}]*\}|\s+\[[^\]]*\]|\s+\([^)]*\))*\s*:\s*'
    ),
    DeclarationType.DEFINITION: re.compile(
        r'^\s*def\s+(\w+)(?:\s+\{[^}]*\}|\s+\[[^\]]*\]|\s+\([^)]*\))*\s*:\s*'
    ),
    DeclarationType.INDUCTIVE: re.compile(
        r'^\s*inductive\s+(\w+)(?:\s+\{[^}]*\}|\s+\[[^\]]*\]|\s+\([^)]*\))*\s*:\s*'
    ),
    DeclarationType.STRUCTURE: re.compile(
        r'^\s*structure\s+(\w+)(?:\s+\{[^}]*\}|\s+\[[^\]]*\]|\s+\([^)]*\))*\s*:\s*'
    ),
    DeclarationType.CLASS: re.compile(
        r'^\s*class\s+(\w+)(?:\s+\{[^}]*\}|\s+\[[^\]]*\]|\s+\([^)]*\))*\s*(?:\s+extends\s+[^\n]*)?\s*:\s*'
    ),
    DeclarationType.INSTANCE: re.compile(
        r'^\s*instance\s+(\w+)?(?:\s*:\s*[^\n]*)?\s*where'
    ),
}

# import 语句模式
IMPORT_PATTERN = re.compile(
    r'^\s*import\s+(.+?)(?:\s*$|--)',
    re.MULTILINE
)

# 文档注释模式
DOC_COMMENT_PATTERN = re.compile(
    r'/--(.*?)\n(?:\s*--.*?\n)*',
    re.DOTALL
)


@dataclass
class _ParseContext:
    """解析上下文（内部状态）"""
    module: str
    source_file: str
    lines: List[str]
    dependencies: List[str]
    declarations: List[LeanDeclaration]
    current_doc_comment: Optional[str] = None


def parse_lean_file(
    file_path: Path,
    module: str,
    mathlib4_root: Optional[Path] = None
) -> ParseResult:
    """
    解析单个 .lean 文件

    Args:
        file_path: .lean 文件路径
        module: 模块名
        mathlib4_root: mathlib4 根路径（用于计算相对路径）

    Returns:
        ParseResult: 解析结果
    """
    start_time = time.time()

    # 读取文件内容
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # 提取依赖
    dependencies = extract_dependencies(content)

    # 解析声明
    declarations = _parse_declarations(content, lines, module)

    parse_time_ms = int((time.time() - start_time) * 1000)

    return ParseResult(
        declarations=declarations,
        dependencies=dependencies,
        module=module,
        source_file=str(file_path),
        parse_time_ms=parse_time_ms
    )


def extract_dependencies(content: str) -> List[str]:
    """
    提取依赖

    解析 import 语句，返回依赖模块列表。
    遵循 K4（同输入同结果）：去重并排序。

    Args:
        content: .lean 文件内容

    Returns:
        依赖模块列表（已排序）
    """
    deps = []

    for match in IMPORT_PATTERN.finditer(content):
        import_stmt = match.group(1)
        # 分割多个 import（用空格分隔）
        for dep in import_stmt.split():
            dep = dep.strip()
            if dep:
                deps.append(dep)

    # 去重并排序（K4 确定性）
    return sorted(list(set(deps)))


def _parse_declarations(
    content: str,
    lines: List[str],
    module: str
) -> List[LeanDeclaration]:
    """
    解析所有声明

    Args:
        content: 文件内容
        lines: 行列表
        module: 模块名

    Returns:
        声明列表（按名字排序，确保确定性）
    """
    declarations = []
    doc_comments = _extract_doc_comments(content)

    i = 0
    while i < len(lines):
        line = lines[i]

        # 跳过空行和注释行
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            i += 1
            continue

        # 尝试匹配每种声明类型
        for decl_type, pattern in DECLARATION_PATTERNS.items():
            match = pattern.match(line)
            if match:
                name = match.group(1) if decl_type != DeclarationType.INSTANCE else ""
                
                # 提取签名
                signature = _extract_signature(lines, i, match.end())
                
                # 获取文档注释
                doc_comment = doc_comments.get(i)

                # 创建声明对象
                decl = _create_declaration(
                    decl_type=decl_type,
                    name=name,
                    module=module,
                    signature=signature,
                    line=i + 1,
                    doc_comment=doc_comment
                )
                
                if decl:
                    declarations.append(decl)
                break

        i += 1

    # 按名字排序（K4 确定性）
    declarations.sort(key=lambda d: d.name)
    
    return declarations


def _extract_signature(
    lines: List[str],
    start_line: int,
    colon_pos: int
) -> str:
    """
    提取类型签名

    从冒号后开始，读取直到括号平衡或遇到 := 或 where。

    Args:
        lines: 行列表
        start_line: 起始行号
        colon_pos: 冒号位置

    Returns:
        类型签名
    """
    # 第一行冒号后的内容
    first_line = lines[start_line]
    signature = first_line[colon_pos + 1:].strip()

    # 计算括号平衡
    brace_count = signature.count('{') + signature.count('(') + signature.count('[')
    brace_count -= signature.count('}') + signature.count(')') + signature.count(']')

    # 如果冒号后内容为空，也继续读取下一行
    j = start_line + 1
    while (brace_count > 0 or not signature) and j < len(lines):
        next_line = lines[j]
        signature += ' ' + next_line.strip()
        brace_count += next_line.count('{') + next_line.count('(') + next_line.count('[')
        brace_count -= next_line.count('}') + next_line.count(')') + next_line.count(']')
        j += 1

    # 移除行内注释
    signature = re.sub(r'--.*$', '', signature, flags=re.MULTILINE)
    signature = signature.strip()

    # 移除尾部的 := 或 where
    signature = re.split(r'\s*:=\s*|\s+where\s*$', signature)[0]

    return signature


def _extract_doc_comments(content: str) -> Dict[int, str]:
    """
    提取文档注释

    Args:
        content: 文件内容

    Returns:
        行号到文档注释的映射
    """
    doc_comments = {}

    for match in DOC_COMMENT_PATTERN.finditer(content):
        comment = match.group(1).strip()
        # 计算文档注释结束的行号
        end_pos = match.end()
        line_num = content[:end_pos].count('\n')
        doc_comments[line_num] = comment

    return doc_comments


def _create_declaration(
    decl_type: DeclarationType,
    name: str,
    module: str,
    signature: str,
    line: int,
    doc_comment: Optional[str] = None
) -> Optional[LeanDeclaration]:
    """
    创建声明对象

    Args:
        decl_type: 声明类型
        name: 声明名
        module: 模块名
        signature: 类型签名
        line: 行号
        doc_comment: 文档注释

    Returns:
        声明对象或 None
    """
    base_kwargs = {
        "name": name,
        "module": module,
        "signature": signature,
        "line": line,
        "doc_comment": doc_comment
    }

    if decl_type == DeclarationType.THEOREM:
        return TheoremDecl(**base_kwargs)
    elif decl_type == DeclarationType.LEMMA:
        return TheoremDecl(**base_kwargs)  # lemma 与 theorem 同结构
    elif decl_type == DeclarationType.DEFINITION:
        return Definition(**base_kwargs)
    elif decl_type == DeclarationType.INDUCTIVE:
        return InductiveDecl(**base_kwargs)
    elif decl_type == DeclarationType.STRUCTURE:
        return StructureDecl(**base_kwargs)
    elif decl_type == DeclarationType.CLASS:
        return ClassDecl(**base_kwargs)
    elif decl_type == DeclarationType.INSTANCE:
        return InstanceDecl(**base_kwargs, class_name=signature.split()[0] if signature else "")

    return None


# 兼容旧接口（用于 build_index.py）
def parse_theorem_declaration(
    content: str,
    module_path: str,
    deps: List[str]
) -> List[Dict[str, Any]]:
    """
    解析定理声明（兼容旧接口）

    Args:
        content: .lean 文件内容
        module_path: 模块路径
        deps: 依赖列表

    Returns:
        定理声明字典列表
    """
    # 直接解析内容，不依赖文件
    lines = content.split('\n')
    declarations = _parse_declarations(content, lines, module_path)

    # 转换为旧格式
    theorems = []
    for decl in declarations:
        if isinstance(decl, (TheoremDecl, Definition)):
            theorems.append({
                "module": decl.module,
                "name": decl.name,
                "signature": decl.signature,
                "deps": deps,
                "line": decl.line
            })

    return theorems


class LeanParser:
    """Lean 4 解析器（规则优先）"""

    def __init__(self):
        self._cache: Dict[str, ParseResult] = {}

    def parse_file(self, file_path: Path, module: str) -> ParseResult:
        """
        解析文件

        Args:
            file_path: 文件路径
            module: 模块名

        Returns:
            ParseResult
        """
        cache_key = f"{module}:{file_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = parse_lean_file(file_path, module)
        self._cache[cache_key] = result
        return result

    def parse_directory(
        self,
        directory: Path,
        base_module: str = ""
    ) -> List[ParseResult]:
        """
        解析目录下所有 .lean 文件

        Args:
            directory: 目录路径
            base_module: 基础模块名

        Returns:
            解析结果列表
        """
        results = []

        for lean_file in sorted(directory.rglob("*.lean")):
            # 计算模块名
            if base_module:
                rel_path = lean_file.relative_to(directory)
                module = f"{base_module}.{rel_path.with_suffix('').name}"
            else:
                module = lean_file.with_suffix('').name

            result = self.parse_file(lean_file, module)
            results.append(result)

        return results

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
