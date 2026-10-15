"""内核验证器测试"""

import pytest
from unittest.mock import patch, MagicMock
from hws_formal_math.engine.kernel import KernelVerifier, VerificationStatus


class TestKernelVerifier:
    """内核验证器测试"""
    
    def test_is_available(self):
        """检查 Lean 可用性"""
        with patch("shutil.which", return_value="/usr/bin/lean"):
            verifier = KernelVerifier()
            assert verifier.is_available() is True
        
        with patch("shutil.which", return_value=None):
            verifier = KernelVerifier()
            assert verifier.is_available() is False
    
    def test_verify_skipped_without_lean(self):
        """无 Lean 时返回 SKIPPED"""
        with patch("shutil.which", return_value=None):
            verifier = KernelVerifier()
            result = verifier.verify("#eval 1+1")
            
            assert result.status == VerificationStatus.SKIPPED
            assert "Lean 工具链不可用" in result.errors[0]
