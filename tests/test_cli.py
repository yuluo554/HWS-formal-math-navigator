"""CLI 测试"""

import pytest
import subprocess
import sys
from pathlib import Path
from hws_formal_math.cli import main, ExitCode


class TestCLI:
    """CLI 测试"""

    def test_help(self, capsys):
        """帮助信息"""
        # argparse --help 会调用 sys.exit(0)
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_no_command(self, capsys):
        """无命令时显示帮助"""
        result = main([])
        assert result == ExitCode.USAGE_ERROR

    def test_search_basic(self, tmp_path, capsys):
        """搜索命令"""
        # 创建测试索引
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )

        # --index-path 是全局参数，必须在子命令之前
        result = main(["--index-path", str(index_dir), "search", "add"])
        assert result == ExitCode.SUCCESS

    def test_search_no_results(self, tmp_path, capsys):
        """搜索无结果"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )

        result = main(["--index-path", str(index_dir), "search", "不存在的定理"])
        assert result == ExitCode.FAILURE

    def test_search_index_not_found(self, tmp_path, capsys):
        """索引不存在"""
        result = main(["--index-path", str(tmp_path / "nonexistent"), "search", "add"])
        assert result == ExitCode.FAILURE

    def test_selftest_with_index(self, tmp_path, capsys):
        """自检命令（有索引）"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )

        result = main(["--index-path", str(index_dir), "selftest"])
        assert result == ExitCode.SUCCESS

    def test_selftest_no_index(self, tmp_path, capsys):
        """自检命令（无索引）"""
        result = main(["--index-path", str(tmp_path / "nonexistent"), "selftest"])
        assert result == ExitCode.FAILURE

    def test_generate_with_model_disabled(self, tmp_path, capsys):
        """生成骨架（模型关闭，已形式化输入）"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )

        # 提供已形式化的 Lean 代码
        lean_code = "theorem add_assoc (a b c : Nat) : a + b + c = a + (b + c) := by rfl"
        result = main(["--index-path", str(index_dir), "generate", lean_code, "--no-model"])
        assert result == ExitCode.SUCCESS

    def test_generate_natural_language_no_model(self, tmp_path, capsys):
        """生成骨架（模型关闭，自然语言输入）"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )

        # 自然语言输入，模型关闭
        result = main(["--index-path", str(index_dir), "generate", "加法结合律", "--no-model"])
        assert result == ExitCode.FAILURE

    def test_verify_basic(self, tmp_path, capsys):
        """验证命令"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )

        lean_code = "theorem add_assoc (a b c : Nat) : a + b + c = a + (b + c) := by rfl"
        result = main(["--index-path", str(index_dir), "verify", lean_code])
        # 无 Lean 时返回 FAIL（SKIPPED 状态）
        assert result == ExitCode.FAILURE


class TestCLIDeterministic:
    """CLI 确定性测试"""

    def test_search_deterministic(self, tmp_path, capsys):
        """同输入同结果"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n'
            '{"name": "add_comm", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b = b + a", "deps": []}\n',
            encoding='utf-8'
        )

        # 第一次运行
        import io
        import contextlib

        out1 = io.StringIO()
        with contextlib.redirect_stdout(out1):
            result1 = main(["--index-path", str(index_dir), "search", "add"])

        # 第二次运行
        out2 = io.StringIO()
        with contextlib.redirect_stdout(out2):
            result2 = main(["--index-path", str(index_dir), "search", "add"])

        # 退出码应该一致
        assert result1 == result2
        # 输出应该一致
        assert out1.getvalue() == out2.getvalue()


class TestCLIMutation:
    """CLI 变异验证"""

    def test_search_wrong_index_path_fails(self, tmp_path, capsys):
        """变异验证：错误索引路径应失败"""
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )

        # 正确的索引路径
        result = main(["--index-path", str(index_dir), "search", "add"])
        assert result == ExitCode.SUCCESS

        # 错误的索引路径
        result = main(["--index-path", str(tmp_path / "wrong_index"), "search", "add"])
        assert result == ExitCode.FAILURE

    def test_selftest_missing_index_fails(self, tmp_path, capsys):
        """变异验证：缺少索引时自检失败"""
        # 有索引
        index_dir = tmp_path / "index"
        index_dir.mkdir()
        index_file = index_dir / "theorems.jsonl"
        index_file.write_text(
            '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", "signature": "a + b + c = a + (b + c)", "deps": []}\n',
            encoding='utf-8'
        )
        result = main(["--index-path", str(index_dir), "selftest"])
        assert result == ExitCode.SUCCESS

        # 无索引
        result = main(["--index-path", str(tmp_path / "nonexistent"), "selftest"])
        assert result == ExitCode.FAILURE
