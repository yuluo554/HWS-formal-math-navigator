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
    
    def test_verify_skipped_detects_sorry(self):
        """无 Lean 时仍检测 sorry"""
        with patch("shutil.which", return_value=None):
            verifier = KernelVerifier()
            result = verifier.verify("theorem test : True := by sorry")
            
            assert result.status == VerificationStatus.SKIPPED
            assert result.has_sorry is True
            assert result.sorry_count == 1
    
    def test_detect_sorry_basic(self):
        """基本 sorry 检测"""
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "theorem test : True := by sorry"
        )
        
        assert has_sorry is True
        assert count == 1
        assert len(locations) == 1
    
    def test_detect_sorry_multiple(self):
        """多个 sorry 检测"""
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "theorem test : True := by { sorry; sorry }"
        )
        
        assert has_sorry is True
        assert count >= 1
    
    def test_detect_sorry_in_comment(self):
        """注释中的 sorry 不计入"""
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "-- this is a sorry comment\ntheorem test : True := by trivial"
        )
        
        assert has_sorry is False
        assert count == 0
    
    def test_detect_no_sorry(self):
        """无 sorry 时返回 False"""
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "theorem test : True := by trivial"
        )
        
        assert has_sorry is False
        assert count == 0
        assert len(locations) == 0
    
    def test_parse_errors(self):
        """错误解析"""
        verifier = KernelVerifier()
        output = """
test.lean:1:1: error: unknown identifier 'foo'
test.lean:2:5: error: type mismatch
"""
        errors = verifier._parse_errors(output)
        
        assert len(errors) > 0
        assert any("unknown identifier" in e for e in errors)


class TestKernelVerifierMutation:
    """内核验证器变异验证"""
    
    def test_sorry_detection_rejects_code_with_sorry(self):
        """变异验证：包含 sorry 的代码应被检测"""
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "theorem test : True := by sorry"
        )
        
        assert has_sorry is True
        assert count > 0
    
    def test_sorry_detection_accepts_valid_code(self):
        """变异验证：无 sorry 的代码应通过"""
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "theorem test : True := by trivial"
        )
        
        assert has_sorry is False
        assert count == 0
    
    def test_skipped_status_with_lean_unavailable(self):
        """变异验证：Lean 不可用时返回 SKIPPED"""
        with patch("shutil.which", return_value=None):
            verifier = KernelVerifier()
            result = verifier.verify("theorem test : True := by trivial")
            
            assert result.status == VerificationStatus.SKIPPED


class TestKernelVerifierDeterministic:
    """内核验证器确定性测试"""
    
    def test_sorry_detection_deterministic(self):
        """同输入同结果"""
        verifier = KernelVerifier()
        code = "theorem test : True := by sorry"
        
        result1 = verifier._detect_sorry(code)
        result2 = verifier._detect_sorry(code)
        
        assert result1 == result2
