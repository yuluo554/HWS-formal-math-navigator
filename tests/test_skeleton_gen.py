"""骨架生成器测试"""

import pytest
from hws_formal_math.engine.skeleton_gen import SkeletonGenerator, GenerationResult
from hws_formal_math.config import Config
from hws_formal_math.exceptions import ModelDisabledError


class TestSkeletonGenerator:
    """骨架生成器测试"""
    
    def test_generate_without_model(self):
        """无模型时接受已形式化输入"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        # Lean 代码应直接返回
        result = generator.generate("theorem add_zero (n : ℕ) : n + 0 := by simp", use_model=False)
        assert result.draft is False
        assert result.model_used is False
        assert "add_zero" in result.code
    
    def test_generate_without_model_natural_language(self):
        """无模型时自然语言命题应报错"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        # 自然语言命题应报错
        with pytest.raises(ModelDisabledError):
            generator.generate("对任意正整数 n，n 加 0 等于 n", use_model=False)
    
    def test_generate_with_lemma(self):
        """支持 lemma 声明"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        result = generator.generate("lemma add_comm (a b : ℕ) : a + b = b + a := by rw [add_comm]", use_model=False)
        assert result.draft is False
        assert result.model_used is False
    
    def test_generate_with_def(self):
        """支持 def 声明"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        result = generator.generate("def my_id (α : Type) (x : α) : α := x", use_model=False)
        assert result.draft is False
        assert result.model_used is False


class TestSkeletonGeneratorSyntaxValidation:
    """语法校验测试"""
    
    def setup_method(self):
        self.config = Config()
        self.generator = SkeletonGenerator(self.config)
    
    def test_validate_valid_theorem(self):
        """验证有效的定理声明"""
        code = "theorem add_zero (n : ℕ) : n + 0 := by simp"
        assert self.generator.validate_syntax(code) is True
    
    def test_validate_valid_lemma(self):
        """有效的引理声明"""
        code = "lemma add_comm (a b : ℕ) : a + b = b + a := by rw [add_comm]"
        assert self.generator.validate_syntax(code) is True
    
    def test_validate_valid_def(self):
        """有效的定义声明"""
        code = "def my_id (α : Type) (x : α) : α := x"
        assert self.generator.validate_syntax(code) is True
    
    def test_validate_empty_code(self):
        """空代码报错"""
        with pytest.raises(ValueError, match="代码为空"):
            self.generator.validate_syntax("")
    
    def test_validate_missing_prefix(self):
        """缺少声明关键字"""
        with pytest.raises(ValueError, match="必须以以下关键字开头"):
            self.generator.validate_syntax("add_zero (n : ℕ) : n + 0 := by simp")
    
    def test_validate_missing_colon(self):
        """缺少冒号（类型分隔符）"""
        # 参数列表后缺少冒号，只有 := 证明分隔符
        # 注意：(n : ℕ) 中的冒号是参数类型注解，不是返回类型分隔符
        with pytest.raises(ValueError, match="缺少冒号"):
            self.generator.validate_syntax("theorem add_zero (n : ℕ) := by simp")
    
    def test_validate_missing_proof(self):
        """缺少证明体"""
        with pytest.raises(ValueError, match="缺少证明体"):
            self.generator.validate_syntax("theorem add_zero (n : ℕ) : n + 0")
    
    def test_validate_unbalanced_parens(self):
        """括号不平衡"""
        with pytest.raises(ValueError, match="参数列表缺少右括号"):
            self.generator.validate_syntax("theorem add_zero (n : ℕ : n + 0 := by simp")
    
    def test_validate_unbalanced_braces(self):
        """大括号不平衡"""
        with pytest.raises(ValueError, match="大括号不平衡"):
            self.generator.validate_syntax("theorem add_zero {{n : ℕ} : n + 0 := by simp")
    
    def test_validate_unbalanced_brackets(self):
        """方括号不平衡"""
        with pytest.raises(ValueError, match="方括号不平衡"):
            self.generator.validate_syntax("theorem add_zero [n : ℕ : n + 0 := by simp")


class TestSkeletonGeneratorMutation:
    """骨架生成器变异验证"""
    
    def setup_method(self):
        self.config = Config()
        self.generator = SkeletonGenerator(self.config)
    
    def test_syntax_validation_rejects_garbage(self):
        """变异验证：垃圾输入应被拒绝"""
        with pytest.raises(ValueError):
            self.generator.validate_syntax("this is not lean code at all")
    
    def test_syntax_validation_accepts_valid(self):
        """变异验证：有效代码应被接受"""
        assert self.generator.validate_syntax("theorem test : True := by trivial") is True
    
    def test_without_model_rejects_natural_language(self):
        """变异验证：无模型时拒绝自然语言"""
        with pytest.raises(ModelDisabledError):
            self.generator.generate("所有自然数加 0 等于自身", use_model=False)
    
    def test_without_model_accepts_lean(self):
        """变异验证：无模型时接受 Lean 代码"""
        result = self.generator.generate("theorem test : True := by trivial", use_model=False)
        assert result.draft is False
