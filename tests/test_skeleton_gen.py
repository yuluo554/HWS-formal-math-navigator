"""骨架生成器测试"""

import pytest
from hws_formal_math.engine.skeleton_gen import SkeletonGenerator
from hws_formal_math.config import Config


class TestSkeletonGenerator:
    """骨架生成器测试"""
    
    def test_generate_without_model(self):
        """无模型时接受已形式化输入"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        # Lean 代码应直接返回
        result = generator.generate("theorem add_zero (n : ℕ) : n + 0 := by simp", use_model=False)
        assert result.draft is False
    
    def test_generate_without_model_natural_language(self):
        """无模型时自然语言命题应报错"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        # 自然语言命题应报错
        with pytest.raises(Exception):  # ModelDisabledError
            generator.generate("对任意正整数 n，n 加 0 等于 n", use_model=False)
