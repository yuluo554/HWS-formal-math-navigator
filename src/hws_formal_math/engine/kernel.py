"""内核验证器（Lean 4 调用）"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import shutil
import tempfile
import re
import time


class VerificationStatus(str, Enum):
    """验证状态"""
    PASS_NO_SORRY = "PASS_NO_SORRY"
    PASS_WITH_SORRY = "PASS_WITH_SORRY"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


@dataclass
class VerificationResult:
    """验证结果"""
    status: VerificationStatus
    has_sorry: bool
    sorry_count: int = 0
    sorry_locations: list = None
    errors: list = None
    warnings: list = None
    kernel_version: Optional[str] = None
    verification_time_ms: int = 0

    def __post_init__(self):
        if self.sorry_locations is None:
            self.sorry_locations = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class KernelVerifier:
    """Lean 4 内核验证器"""

    def __init__(self, lean_path: Optional[str] = None):
        """
        初始化内核验证器

        Args:
            lean_path: Lean 可执行文件路径
        """
        self.lean_path = lean_path or shutil.which("lean")

    def is_available(self) -> bool:
        """检查 Lean 是否可用"""
        return self.lean_path is not None

    def verify(self, code: str) -> VerificationResult:
        """
        验证 Lean 代码

        三态判定：
        - PASS_NO_SORRY: 编译通过且无 sorry
        - PASS_WITH_SORRY: 编译通过但有 sorry（K1：不计入成功）
        - FAIL: 编译失败
        - SKIPPED: Lean 工具链不可用

        Args:
            code: Lean 代码片段

        Returns:
            VerificationResult: 验证结果
        """
        start_time = time.time()

        if not self.is_available():
            # Lean 不可用，但仍检测 sorry
            has_sorry, sorry_count, sorry_locations = self._detect_sorry(code)
            return VerificationResult(
                status=VerificationStatus.SKIPPED,
                has_sorry=has_sorry,
                sorry_count=sorry_count,
                sorry_locations=sorry_locations,
                errors=["Lean 工具链不可用"],
                warnings=["内核验证未执行，仅进行 sorry 检测"]
            )

        # 先检测 sorry（快速检查）
        has_sorry, sorry_count, sorry_locations = self._detect_sorry(code)

        # 运行 lean --check
        exit_code, stdout, stderr = self._run_lean_check(code)

        verification_time_ms = int((time.time() - start_time) * 1000)

        if exit_code == 0:
            # 编译通过
            if has_sorry:
                return VerificationResult(
                    status=VerificationStatus.PASS_WITH_SORRY,
                    has_sorry=True,
                    sorry_count=sorry_count,
                    sorry_locations=sorry_locations,
                    kernel_version=self._get_lean_version(),
                    verification_time_ms=verification_time_ms,
                    warnings=["代码编译通过但包含 sorry，不计入成功"]
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.PASS_NO_SORRY,
                    has_sorry=False,
                    sorry_count=0,
                    sorry_locations=[],
                    kernel_version=self._get_lean_version(),
                    verification_time_ms=verification_time_ms
                )
        else:
            # 编译失败
            errors = self._parse_errors(stderr or stdout)
            return VerificationResult(
                status=VerificationStatus.FAIL,
                has_sorry=has_sorry,
                sorry_count=sorry_count,
                sorry_locations=sorry_locations,
                errors=errors,
                kernel_version=self._get_lean_version(),
                verification_time_ms=verification_time_ms
            )

    def _run_lean_check(self, code: str) -> Tuple[int, str, str]:
        """
        运行 lean --check

        Args:
            code: Lean 代码

        Returns:
            Tuple[exit_code, stdout, stderr]
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lean', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name

        try:
            # 使用 lean --check 检查代码
            result = subprocess.run(
                [self.lean_path, '--check', temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Lean check timed out after 30 seconds"
        except Exception as e:
            return -1, "", str(e)
        finally:
            # 清理临时文件
            try:
                Path(temp_file).unlink()
            except:
                pass

    def _detect_sorry(self, code: str) -> Tuple[bool, int, List[Dict[str, Any]]]:
        """
        检测 sorry 存在

        K1 口径：sorry 不计入成功

        Args:
            code: Lean 代码

        Returns:
            Tuple[has_sorry, count, locations]
        """
        # 匹配 sorry 模式（排除注释中的 sorry）
        # 简单实现：查找 "sorry" 关键字
        # 注意：这是一个简化实现，实际应该解析 Lean 语法树
        locations = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            stripped = line.strip()
            if stripped.startswith('--'):
                continue

            # 查找 sorry
            # 使用正则匹配 sorry 作为独立单词
            sorry_pattern = r'\bsorry\b'
            for match in re.finditer(sorry_pattern, line):
                locations.append({
                    'line': line_num,
                    'column': match.start() + 1,
                    'context': line.strip()
                })

        return len(locations) > 0, len(locations), locations

    def _parse_errors(self, output: str) -> List[str]:
        """
        解析错误信息

        Args:
            output: Lean 输出

        Returns:
            错误信息列表
        """
        errors = []
        if not output:
            return errors

        # 解析 Lean 错误信息格式
        # 格式通常为：**文件:行:列: 错误信息**
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith(' '):
                # 可能是错误信息
                errors.append(line)

        return errors

    def _get_lean_version(self) -> Optional[str]:
        """获取 Lean 版本"""
        if not self.lean_path:
            return None

        try:
            result = subprocess.run(
                [self.lean_path, '--version'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None
