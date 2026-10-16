"""统一中间表示（IR）

定义 Lean 4 源码解析后的统一数据结构。
遵循 K4（同输入同结果）和 K10（UTF-8 输出）口径。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class DeclarationType(Enum):
    """声明类型"""
    THEOREM = "theorem"
    LEMMA = "lemma"
    DEFINITION = "def"
    INDUCTIVE = "inductive"
    STRUCTURE = "structure"
    CLASS = "class"
    INSTANCE = "instance"


@dataclass(frozen=True)
class ModuleRef:
    """模块引用"""
    module: str
    name: str

    def __str__(self) -> str:
        return f"{self.module}.{self.name}" if self.module else self.name

    def to_dict(self) -> Dict[str, str]:
        return {"module": self.module, "name": self.name}


@dataclass(frozen=True)
class LeanDeclaration:
    """声明基类（不可变，确保确定性）"""
    name: str
    module: str
    signature: str
    line: int = 0
    deps: List[str] = field(default_factory=list)
    doc_comment: Optional[str] = None
    decl_type: DeclarationType = DeclarationType.THEOREM

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 JSON 序列化）"""
        return {
            "name": self.name,
            "decl_type": self.decl_type.value,
            "module": self.module,
            "signature": self.signature,
            "line": self.line,
            "deps": sorted(self.deps),  # 排序确保确定性
            "doc_comment": self.doc_comment
        }


@dataclass(frozen=True)
class TheoremDecl(LeanDeclaration):
    """定理声明"""
    decl_type: DeclarationType = DeclarationType.THEOREM


@dataclass(frozen=True)
class Definition(LeanDeclaration):
    """定义声明"""
    decl_type: DeclarationType = DeclarationType.DEFINITION
    is_transparent: bool = True


@dataclass(frozen=True)
class InductiveDecl(LeanDeclaration):
    """归纳类型声明"""
    decl_type: DeclarationType = DeclarationType.INDUCTIVE
    constructors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class StructureDecl(LeanDeclaration):
    """结构体声明"""
    decl_type: DeclarationType = DeclarationType.STRUCTURE
    parent: Optional[str] = None
    fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClassDecl(LeanDeclaration):
    """类声明"""
    decl_type: DeclarationType = DeclarationType.CLASS
    parent_classes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class InstanceDecl(LeanDeclaration):
    """实例声明"""
    decl_type: DeclarationType = DeclarationType.INSTANCE
    class_name: str = ""


@dataclass(frozen=True)
class ParseResult:
    """解析结果"""
    declarations: List[LeanDeclaration]
    dependencies: List[str]
    module: str
    source_file: str
    parse_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 JSON 序列化）

        注意：parse_time_ms 被排除，因为解析时间不是确定性内容。
        这是 K4（同输入同结果）口径的要求。
        """
        return {
            "module": self.module,
            "source_file": self.source_file,
            "dependencies": sorted(self.dependencies),
            "declaration_count": len(self.declarations),
            "declarations": [d.to_dict() for d in self.declarations],
        }

    def __eq__(self, other: object) -> bool:
        """相等性比较（用于确定性验证）"""
        if not isinstance(other, ParseResult):
            return False
        return self.to_dict() == other.to_dict()
