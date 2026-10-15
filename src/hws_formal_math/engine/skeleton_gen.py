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
        if proposition.strip().startswith("theorem ") or proposition.strip().startswith("lemma "):
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
        
        Args:
            code: Lean 代码
            
        Returns:
            bool: 语法是否有效
        """
        # TODO: 实现 Lean 语法校验
        # 不通过即报错，不静默修补
        raise NotImplementedError("语法校验待实现")
