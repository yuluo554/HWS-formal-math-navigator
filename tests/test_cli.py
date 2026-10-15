"""CLI 测试"""

import pytest
from click.testing import CliRunner
from hws_formal_math.cli import main


class TestCLI:
    """CLI 测试"""
    
    @pytest.fixture
    def runner(self):
        """CLI runner"""
        return CliRunner()
    
    def test_help(self, runner):
        """帮助信息"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
    
    def test_search(self, runner):
        """搜索命令"""
        result = runner.invoke(main, ["search", "加法结合律"])
        assert result.exit_code == 0
    
    def test_selftest(self, runner):
        """自检命令"""
        result = runner.invoke(main, ["selftest"])
        assert result.exit_code == 0
