"""解析层（M2）

统一中间表示 + 规则优先解析器（LLM 只兜底）。
遵循 K4（同输入同结果）和 K10（UTF-8 输出）口径。
"""

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

from .parser import (
    LeanParser,
    parse_theorem_declaration,
    extract_dependencies,
    parse_lean_file
)

__all__ = [
    # IR 类型
    "LeanDeclaration",
    "TheoremDecl",
    "Definition",
    "InductiveDecl",
    "StructureDecl",
    "ClassDecl",
    "InstanceDecl",
    "ModuleRef",
    "ParseResult",
    "DeclarationType",
    # 解析器
    "LeanParser",
    "parse_lean_file",
    "parse_theorem_declaration",
    "extract_dependencies"
]
