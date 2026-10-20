"""内核验证真子进程实测（D2 / DEC3=A）

回答两个问题，都要**真跑子进程**：
  ① 命令行参数是不是 `lean <file>`（不含 `--check`）
  ② 三种输入（正确 / 错误 / 含 sorry）的 rc 映射对不对

关于"真 Lean"：本机没有 Lean 工具链（`command -v lean` 无输出、`~/.elan` 不存在），
所以这里的 `lean` 是**可注入的假 lean 夹具**（fakes/ 下，行为按 true-Lean 语义模拟：
编译失败 → rc 1 + stderr 报错；`sorry` → 编译通过 + warning，rc 0）。
**这不是真 Lean 实测**——真 Lean 的 rc/stdout 记录见 plan/RELEASE-M8.md §三。
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hws_formal_math.engine.kernel import KernelVerifier, VerificationStatus  # noqa: E402

PYTHON = sys.executable

FAKE_LEAN_PY = '''
# 假 lean（夹具）：模拟 Lean 4 的 `lean <file>` 行为
#
# 语义（与真 Lean 对齐的部分）：
#   - 裸文件参数 → 编译该文件
#   - 文件里出现 `#error` 标记 → rc 1 + stderr 报错（模拟"错误证明"）
#   - `sorry` → 编译通过（rc 0）+ stderr 打 warning（真 Lean 只告警不改 rc）
#   - 收到 `--check` 等未知长选项 → rc 1 + "Unknown command line option"
#
# **为什么模拟 `--check` 的拒绝**：上游 `shell.cpp` 的 `g_long_options[]` 无该项，
# 未知选项走 eprint + throw 1。夹具照抄这个行为，好让"用 --check 的实现"必判 FAIL。
import re
import sys
from pathlib import Path

args = sys.argv[1:]

if args == ["--version"]:
    print("Lean (version 4.0.0, fake-fixture)")
    raise SystemExit(0)

if not args:
    sys.stderr.write("usage: lean <file>\\n")
    raise SystemExit(1)

for arg in args:
    if arg.startswith("--"):
        sys.stderr.write("Unknown command line option '%s'\\n" % arg)
        raise SystemExit(1)

path = Path(args[-1])
if not path.is_file():
    sys.stderr.write("error: no such file '%s'\\n" % path)
    raise SystemExit(1)

text = path.read_text(encoding="utf-8")

if "#error" in text:
    sys.stderr.write("%s:1:1: error: fixture-injected failure\\n" % path)
    raise SystemExit(1)

if re.search(r"\\bsorry\\b", text):
    sys.stderr.write("%s:1:1: warning: declaration uses 'sorry'\\n" % path)

raise SystemExit(0)
'''


def _install_fake_lean(tmp_path: Path) -> Path:
    """把假 lean 装成一个可执行文件，返回其路径"""
    fixture = tmp_path / "_fake_lean_impl.py"
    fixture.write_text(FAKE_LEAN_PY, encoding="utf-8")

    if os.name == "nt":
        launcher = tmp_path / "lean.cmd"
        launcher.write_text(
            f'@echo off\r\n"{PYTHON}" "{fixture}" %*\r\n', encoding="utf-8"
        )
        return launcher

    launcher = tmp_path / "lean"
    launcher.write_text(
        f'#!/bin/sh\nexec "{PYTHON}" "{fixture}" "$@"\n', encoding="utf-8"
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return launcher


@pytest.fixture
def fake_lean(tmp_path):
    return _install_fake_lean(tmp_path)


class TestLeanCommandShape:
    """命令行形态（D2 的机械判据：不含 --check）"""

    def test_command_is_bare_file(self, tmp_path):
        """build_command 只产 [lean, <file>]"""
        verifier = KernelVerifier(lean_path=str(tmp_path / "lean"))
        command = verifier.build_command("/tmp/x.lean")
        assert command == [str(tmp_path / "lean"), "/tmp/x.lean"]

    def test_command_has_no_check_flag(self, tmp_path):
        """**回归守门**：参数表里不得出现 --check（D2 上游不认这个选项）"""
        verifier = KernelVerifier(lean_path=str(tmp_path / "lean"))
        command = verifier.build_command("x.lean")
        assert "--check" not in command
        assert not any(c.startswith("--") for c in command), command

    def test_fake_lean_rejects_check_like_upstream(self, fake_lean, tmp_path):
        """夹具本身要复刻上游拒绝语义（防夹具变成永远通过的假绿）"""
        import subprocess

        lean_file = tmp_path / "t.lean"
        lean_file.write_text("theorem t : True := by trivial\n", encoding="utf-8")
        result = subprocess.run(
            [str(fake_lean), "--check", str(lean_file)],
            capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode != 0
        assert "Unknown command line option" in result.stderr


class TestVerifyWithRealSubprocess:
    """真子进程三态判定（正确 / 错误 / 含 sorry）"""

    def test_correct_proof_passes(self, fake_lean):
        """正确证明 → PASS_NO_SORRY，exit_code 0"""
        verifier = KernelVerifier(lean_path=str(fake_lean))
        result = verifier.verify("theorem t : True := by trivial")
        assert result.status == VerificationStatus.PASS_NO_SORRY
        assert result.exit_code == 0
        assert result.command is not None and "--check" not in result.command

    def test_wrong_proof_fails(self, fake_lean):
        """错误证明 → FAIL，exit_code 非 0"""
        verifier = KernelVerifier(lean_path=str(fake_lean))
        result = verifier.verify("theorem bad : 1 = 2 := by rfl #error")
        assert result.status == VerificationStatus.FAIL
        assert result.exit_code != 0
        assert result.errors

    def test_sorry_proof_is_pass_with_sorry(self, fake_lean):
        """含 sorry → 编译通过但判 PASS_WITH_SORRY（K1：不计入成功）"""
        verifier = KernelVerifier(lean_path=str(fake_lean))
        result = verifier.verify("theorem s : 1 = 2 := by sorry")
        assert result.status == VerificationStatus.PASS_WITH_SORRY
        assert result.exit_code == 0
        assert result.has_sorry is True
        assert result.sorry_count == 1

    def test_missing_lean_binary_is_fail_not_pass(self, tmp_path):
        """路径存在的假可执行件缺失 → FAIL（不能静默当通过）"""
        verifier = KernelVerifier(lean_path=str(tmp_path / "no-such-lean"))
        result = verifier.verify("theorem t : True := by trivial")
        assert result.status == VerificationStatus.FAIL


class TestSorryDetectionComments:
    """D10：块注释 / 行尾注释不得计入 sorry"""

    def test_block_comment_sorry_ignored(self):
        verifier = KernelVerifier()
        has_sorry, count, _ = verifier._detect_sorry(
            "/- markdown: sorry -/\ntheorem t : True := by trivial"
        )
        assert has_sorry is False
        assert count == 0

    def test_trailing_line_comment_sorry_ignored(self):
        verifier = KernelVerifier()
        has_sorry, count, _ = verifier._detect_sorry(
            "theorem t : True := by\n  trivial -- no sorry here"
        )
        assert has_sorry is False
        assert count == 0

    def test_nested_block_comment_sorry_ignored(self):
        """Lean 块注释可嵌套：内外层的 sorry 都不算"""
        verifier = KernelVerifier()
        has_sorry, count, _ = verifier._detect_sorry(
            "/- outer sorry /- inner sorry -/ still sorry -/\ntheorem t : True := by trivial"
        )
        assert has_sorry is False
        assert count == 0

    def test_real_sorry_still_detected(self):
        """阴性对照：真 sorry 必须仍被抓到（修假阳性不能修成漏检）"""
        verifier = KernelVerifier()
        has_sorry, count, _ = verifier._detect_sorry(
            "theorem t : True := by sorry"
        )
        assert has_sorry is True
        assert count == 1

    def test_sorry_after_comment_on_same_line_detected(self):
        verifier = KernelVerifier()
        has_sorry, count, locations = verifier._detect_sorry(
            "theorem t : True := by sorry -- 这里真的用了 sorry"
        )
        assert has_sorry is True
        assert count == 1
        assert locations[0]["line"] == 1
