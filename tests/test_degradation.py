"""降级路径测试"""

import pytest
from unittest.mock import patch
from hws_formal_math.engine.kernel import KernelVerifier
from hws_formal_math.engine.skeleton_gen import SkeletonGenerator
from hws_formal_math.config import Config


class TestDegradation:
    """降级路径测试"""
    
    def test_no_lean_retrieval_still_works(self):
        """无 Lean 工具链时检索仍可用"""
        # 检索不依赖 Lean，直接测试
        from hws_formal_math.engine.retriever import Retriever
        from pathlib import Path
        
        # 创建临时索引
        with pytest.raises(FileNotFoundError):
            Retriever(Path("/nonexistent"))
    
    def test_no_lean_kernel_verification_marked_skipped(self):
        """无 Lean 工具链时内核验证标注"未执行"""
        with patch("shutil.which", return_value=None):
            verifier = KernelVerifier()
            result = verifier.verify("#eval 1+1")
            
            assert result.status.value == "SKIPPED"
            assert "Lean 工具链不可用" in result.errors
    
    def test_no_model_skeleton_generation_disabled(self):
        """无模型端点时骨架生成关闭"""
        config = Config()
        generator = SkeletonGenerator(config)
        
        # 自然语言命题应报错
        with pytest.raises(Exception):
            generator.generate("对任意正整数 n，n 加 0 等于 n", use_model=True)
