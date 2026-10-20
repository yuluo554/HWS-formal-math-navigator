"""内核验证器（Lean 4 调用）

D2 修复要点：**`lean --check` 不是 Lean 4 的合法选项**。
上游 `src/util/shell.cpp` 的 `g_long_options[]` 里没有 `check`，
未知选项走 `eprint "Unknown command line option"` + `throw 1` —— 真装 Lean 后
正确证明也会被判 FAIL，`PASS_NO_SORRY` 永远达不到。

现在的调用形态：`lean <file>`（裸文件参数，`shell.cpp` 支持），
以**退出码**为唯一编译判据（rc=0 编译通过 / 非 0 编译失败）。
`sorry` 不改变退出码（Lean 只是 warning），所以 sorry 判定走源码侧正则
（见 `_detect_sorry`，D10 已修块注释与行尾注释假阳性）。
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import shutil
import tempfile
import re
import time

# 单次编译超时（秒）。Lean 首次编译 Mathlib 依赖可能很久，但骨架是独立小文件，
# 30s 足够；超时按 FAIL 处理并如实标注原因。
DEFAULT_TIMEOUT_SECONDS = 30


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
    exit_code: Optional[int] = None
    command: Optional[list] = None

    def __post_init__(self):
        if self.sorry_locations is None:
            self.sorry_locations = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class KernelVerifier:
    """Lean 4 内核验证器"""

    def __init__(self, lean_path: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        """
        初始化内核验证器

        Args:
            lean_path: Lean 可执行文件路径
            timeout: 单次编译超时（秒）
        """
        self.lean_path = lean_path or shutil.which("lean")
        self.timeout = timeout

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

        # 运行 lean <file>（D2：不是 --check）
        exit_code, stdout, stderr, command = self._run_lean_check(code)

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
                    exit_code=exit_code,
                    command=command,
                    warnings=["代码编译通过但包含 sorry，不计入成功"]
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.PASS_NO_SORRY,
                    has_sorry=False,
                    sorry_count=0,
                    sorry_locations=[],
                    kernel_version=self._get_lean_version(),
                    verification_time_ms=verification_time_ms,
                    exit_code=exit_code,
                    command=command,
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
                verification_time_ms=verification_time_ms,
                exit_code=exit_code,
                command=command,
            )

    def build_command(self, lean_file: str) -> List[str]:
        """构造 Lean 4 编译命令（**唯一构造点**，测试据此断言参数表）

        Lean 4 的合法形态是 `lean <file>`：`shell.cpp` 的 `g_opt_str` 收裸文件参数。
        `--check` 不存在（上游 `g_long_options[]` 无该项）——这条断言由
        tests/test_kernel.py::test_command_has_no_check_flag 守。
        """
        return [self.lean_path, lean_file]

    def _run_lean_check(self, code: str) -> Tuple[int, str, str, List[str]]:
        """
        运行 lean <file>

        Args:
            code: Lean 代码

        Returns:
            Tuple[exit_code, stdout, stderr, command]
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lean', delete=False,
                                         encoding='utf-8', newline='\n') as f:
            f.write(code)
            temp_file = f.name

        command = self.build_command(temp_file)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout,
            )
            return result.returncode, result.stdout, result.stderr, command
        except subprocess.TimeoutExpired:
            return -1, "", f"Lean 编译超时（{self.timeout} 秒）", command
        except Exception as e:
            return -1, "", str(e), command
        finally:
            # 清理临时文件
            try:
                Path(temp_file).unlink()
            except OSError:
                pass

    def _strip_comments(self, code: str) -> List[str]:
        """去掉 `/- … -/` 块注释与 `--` 行尾注释，保留行号结构

        D10：旧实现只跳过 `stripped.startswith('--')` 的整行，于是
          `/- markdown: sorry -/` 与 `trivial -- no sorry here` 都被误判。
        这里做逐行状态机：`/-` 进入块注释（Lean 块注释可嵌套），`-/` 退出；
        行内 `--` 之后全丢弃（Lean 的行注释不吞换行）。

        Returns:
            每行"去掉注释后"的文本（行数与输入一致，注释被替换为空）
        """
        result: List[str] = []
        depth = 0  # 块注释嵌套深度

        for line in code.split("\n"):
            out_chars: List[str] = []
            i = 0
            length = len(line)
            while i < length:
                if depth > 0:
                    if line.startswith("/-", i):
                        depth += 1
                        i += 2
                        continue
                    if line.startswith("-/", i):
                        depth -= 1
                        i += 2
                        continue
                    i += 1
                    continue

                if line.startswith("/-", i):
                    depth += 1
                    i += 2
                    continue
                if line.startswith("--", i):
                    break  # 行注释：本行后面全部丢弃
                out_chars.append(line[i])
                i += 1

            result.append("".join(out_chars))

        return result

    def _detect_sorry(self, code: str) -> Tuple[bool, int, List[Dict[str, Any]]]:
        """
        检测 sorry 存在

        K1 口径：sorry 不计入成功

        Args:
            code: Lean 代码

        Returns:
            Tuple[has_sorry, count, locations]
        """
        locations = []
        sorry_pattern = r'\bsorry\b'

        for line_num, line in enumerate(self._strip_comments(code), 1):
            for match in re.finditer(sorry_pattern, line):
                locations.append({
                    'line': line_num,
                    'column': match.start() + 1,
                    'context': line.strip(),
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
                errors='replace',
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None
