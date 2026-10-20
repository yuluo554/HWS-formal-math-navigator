"""CLI 行为回归（D7 / D9 / D11）

覆盖本批修的三处"文档有、实现没有"：
  - D7a：退出码 4（配置错误）此前只有定义、无任何 return
  - D7c：`--version` 此前 unrecognized arguments → exit 2
  - D9：`export -o` 此前只取父目录，输出文件名写死 report.html/report.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hws_formal_math import __version__
from hws_formal_math.cli import ExitCode, main

REPO_INDEX = Path(__file__).resolve().parent.parent / "data" / "index"


@pytest.fixture
def index_dir(tmp_path):
    d = tmp_path / "index"
    d.mkdir()
    (d / "theorems.jsonl").write_text(
        '{"name": "add_assoc", "module": "Mathlib.Algebra.Group.Defs", '
        '"signature": "a + b + c = a + (b + c)", "deps": []}\n',
        encoding="utf-8",
    )
    return d


class TestVersionFlag:
    """D7c：--version 必须可用"""

    def test_version_exits_zero_and_prints(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert __version__ in out

    def test_version_matches_package_metadata(self):
        """D11：__version__ 与 pyproject 单源（源码态读 pyproject）"""
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        assert f'version = "{__version__}"' in text


class TestConfigErrorExitCode:
    """D7a：模型启用但无端点 → exit 4（此前一律落 1）"""

    def test_missing_endpoint_returns_config_error(self, tmp_path, index_dir, capsys):
        config = tmp_path / "cfg.yaml"
        config.write_text("model:\n  enabled: true\n  endpoint: null\n", encoding="utf-8")

        result = main([
            "--config", str(config), "--index-path", str(index_dir),
            "generate", "加法结合律",
        ])
        assert result == ExitCode.CONFIG_ERROR
        assert result == 4

    def test_unimplemented_endpoint_is_failure_not_success(self, tmp_path, index_dir):
        """端点配了但未实现 → exit 1（不能静默成功，也不能冒充依赖缺失）"""
        config = tmp_path / "cfg.yaml"
        config.write_text(
            "model:\n  enabled: true\n  endpoint: http://localhost:9/v1\n",
            encoding="utf-8",
        )
        result = main([
            "--config", str(config), "--index-path", str(index_dir),
            "generate", "加法结合律",
        ])
        assert result == ExitCode.FAILURE


class TestExportOutputPath:
    """D9：-o 必须真正决定文件名，且不再凭空多写一份"""

    def test_custom_json_filename_created(self, tmp_path, index_dir):
        out = tmp_path / "out3" / "custom.json"
        result = main([
            "--index-path", str(index_dir),
            "export", "--format", "json", "-o", str(out),
        ])
        assert result == ExitCode.SUCCESS
        assert out.is_file(), "-o 指定的文件不存在（D9 复现）"
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "proposition" in data

    def test_no_side_effect_report_json(self, tmp_path, index_dir):
        """只产 -o 指定的那一份（以前会多写 report.json / report.html）"""
        out = tmp_path / "x" / "custom.json"
        assert main([
            "--index-path", str(index_dir),
            "export", "--format", "json", "-o", str(out),
        ]) == ExitCode.SUCCESS

        siblings = sorted(p.name for p in out.parent.iterdir())
        assert siblings == ["custom.json"], f"多写了文件: {siblings}"

    def test_html_format_writes_html(self, tmp_path, index_dir):
        out = tmp_path / "r" / "page.html"
        assert main([
            "--index-path", str(index_dir),
            "export", "--format", "html", "-o", str(out),
        ]) == ExitCode.SUCCESS
        assert out.is_file()
        assert "<html" in out.read_text(encoding="utf-8").lower()

    def test_proposition_flag_is_used(self, tmp_path, index_dir):
        """D9：命题不再写死（--proposition 应进报告内容）"""
        out = tmp_path / "p" / "r.json"
        assert main([
            "--index-path", str(index_dir),
            "export", "--format", "json", "-o", str(out),
            "--proposition", "自定义命题XYZ",
        ]) == ExitCode.SUCCESS
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["proposition"] == "自定义命题XYZ"

    def test_default_proposition_is_announced(self, tmp_path, index_dir, capsys):
        """不给 --proposition 时必须明示"用了内置示例"，不静默"""
        out = tmp_path / "d" / "r.json"
        main(["--index-path", str(index_dir), "export", "-o", str(out)])
        out_text = capsys.readouterr().out
        assert "内置示例命题" in out_text


class TestCoveragePrinting:
    """D8：领域覆盖度必须进人读输出"""

    def test_bench_prints_coverage_section(self, capsys):
        result = main(["--index-path", str(REPO_INDEX), "bench", "--suite", "retrieval"])
        assert result == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "[coverage]" in out
        assert "不参与 all_passed" in out

    def test_coverage_does_not_flip_bench_exit_code(self):
        """覆盖度不足不得影响达标判定（否则基准恒红；静默降级则是开后门）"""
        result = main(["--index-path", str(REPO_INDEX), "bench", "--suite", "retrieval"])
        assert result == ExitCode.SUCCESS

    def test_bench_without_suite_still_fails_when_skeleton_disabled(self):
        """不带 --suite → exit 1 是设计行为（不许改成 0）"""
        result = main(["--index-path", str(REPO_INDEX), "bench"])
        assert result == ExitCode.FAILURE
