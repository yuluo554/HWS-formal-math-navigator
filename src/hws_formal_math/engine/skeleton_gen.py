"""骨架生成器（模型在环）"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from ..config import Config
from ..core.model_gateway import ModelGateway, SkeletonResult
from ..exceptions import ModelDisabledError


@dataclass
class GenerationResult:
    """生成结果"""
    code: str
    draft: bool
    uncertainties: list
    model_used: bool


class SkeletonGenerator:
    """证明骨架生成器"""
    
    def __init__(self, config: Config):
        """
        初始化骨架生成器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.model_gateway = ModelGateway(config.model) if config.model.enabled else None
    
    def generate(self, proposition: str, use_model: bool = True) -> GenerationResult:
        """
        生成证明骨架
        
        Args:
            proposition: 数学命题
            use_model: 是否使用模型
            
        Returns:
            GenerationResult: 生成结果
        """
        if use_model and self.model_gateway:
            return self._generate_with_model(proposition)
        else:
            return self._generate_without_model(proposition)
    
    def _generate_with_model(self, proposition: str) -> GenerationResult:
        """使用模型生成骨架"""
        if not self.model_gateway:
            raise ModelDisabledError("模型未启用")
        
        result = self.model_gateway.generate_skeleton(proposition)
        return GenerationResult(
            code=result.code,
            draft=result.draft,
            uncertainties=result.uncertainties,
            model_used=True
        )
    
    def _generate_without_model(self, proposition: str) -> GenerationResult:
        """不使用模型（接受已形式化输入）"""
        # 检查命题是否为已形式化的 Lean 代码
        # 如果是 Lean 代码，直接返回
        # 否则报错，提示需要模型或人工形式化
        stripped = proposition.strip()
        if stripped.startswith("theorem ") or stripped.startswith("lemma ") or stripped.startswith("def "):
            return GenerationResult(
                code=proposition,
                draft=False,
                uncertainties=[],
                model_used=False
            )
        else:
            # 自然语言命题，需要模型
            raise ModelDisabledError(
                "模型已关闭，请提供已形式化的 Lean 代码，或启用模型端点"
            )
    
    def validate_syntax(self, code: str) -> bool:
        """
        语法校验
        
        基于规则的轻量级 Lean 语法检查：
        1. 必须以 theorem/lemma/def/inductive/structure/class/instance 开头
        2. 必须有冒号分隔名称和类型（冒号必须在参数列表之后）
        3. 必须有类型签名
        4. 必须有证明体（:= 或 by）
        
        Args:
            code: Lean 代码
            
        Returns:
            bool: 语法是否有效
            
        Raises:
            ValueError: 语法无效时抛出，包含具体错误信息
        """
        code = code.strip()
        
        if not code:
            raise ValueError("代码为空")
        
        # 检查声明类型
        valid_prefixes = ['theorem ', 'lemma ', 'def ', 'inductive ', 'structure ', 'class ', 'instance ']
        has_valid_prefix = any(code.startswith(prefix) for prefix in valid_prefixes)
        
        if not has_valid_prefix:
            raise ValueError(
                f"声明必须以以下关键字开头: {', '.join(p.strip() for p in valid_prefixes)}"
            )
        
        # 找到声明关键字后的第一个冒号（应该是分隔参数和返回类型的冒号）
        # Lean 语法: theorem name (params) : return_type := proof
        # 冒号应该在参数列表的右括号之后
        
        # 找到声明关键字结束位置
        prefix_end = 0
        for prefix in valid_prefixes:
            if code.startswith(prefix):
                prefix_end = len(prefix)
                break
        
        # 提取声明名称部分（到第一个冒号或括号之前）
        remaining = code[prefix_end:]
        
        # 找到第一个左括号（参数列表开始）
        paren_start = remaining.find('(')
        
        if paren_start != -1:
            # 有参数列表，找到对应的右括号
            paren_end = remaining.find(')', paren_start)
            if paren_end == -1:
                raise ValueError("参数列表缺少右括号 ')'")
            
            # 冒号应该在右括号之后，且不能是 := 的一部分
            # 查找不在 := 中的冒号
            colon_pos = -1
            for i in range(paren_end, len(remaining)):
                if remaining[i] == ':':
                    # 检查是否是 := 的一部分
                    if i + 1 < len(remaining) and remaining[i + 1] == '=':
                        continue  # 跳过 :=
                    colon_pos = i
                    break
            
            if colon_pos == -1:
                raise ValueError("缺少冒号 ':' 分隔参数和返回类型")
        else:
            # 无参数列表，冒号应该在名称之后（且不能是 := 的一部分）
            colon_pos = -1
            for i in range(len(remaining)):
                if remaining[i] == ':':
                    if i + 1 < len(remaining) and remaining[i + 1] == '=':
                        continue
                    colon_pos = i
                    break
            
            if colon_pos == -1:
                raise ValueError("缺少冒号 ':' 分隔名称和类型")
        
        # 检查证明体
        has_proof = ':=' in code or ' by ' in code or ' := by' in code
        if not has_proof:
            raise ValueError("缺少证明体 ':=' 或 'by'")
        
        # 检查括号平衡（简单检查）
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            raise ValueError(f"括号不平衡: ({open_parens}) vs ){close_parens}")
        
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            raise ValueError(f"大括号不平衡: {{{open_braces}}} vs }}{close_braces}")
        
        open_brackets = code.count('[')
        close_brackets = code.count(']')
        if open_brackets != close_brackets:
            raise ValueError(f"方括号不平衡: [{open_brackets}] vs ]{close_brackets}")
        
        return True
