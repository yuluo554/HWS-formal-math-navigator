"""查看器验收（preflight ㉕：主控件接业务 + 入口到产物有断言）

三层：
  1. 控制器层（零 Qt）：检索 → 构图 → 导出 HTML，产物 0 外链；
  2. 接线层（AST）：GUI 的检索/导出按钮必须真的 `connect` 到业务方法；
  3. 产物层（打包）：viewer 入口必须被 spec 收进冻结产物（否则附件里没有它）。
"""

import ast
import json
from pathlib import Path

import pytest

from hws_formal_math.config import Config
from hws_formal_math.viewer.controller import ViewerController

REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWER_DIR = REPO_ROOT / "src" / "hws_formal_math" / "viewer"
SPEC = REPO_ROOT / "tools" / "hws-formal-math.spec"


@pytest.fixture()
def controller():
    return ViewerController(Config.load())


class TestViewerController:
    def test_index_summary_declares_sample_kind(self, controller):
        summary = controller.index_summary()
        assert "error" not in summary
        assert summary["theorem_count"] > 0
        assert summary["index_kind"] == "curated-sample", (
            "随包索引必须显式声明为样例（不得冒充完整 mathlib4 索引）")

    def test_search_returns_ranked_results(self, controller):
        state = controller.search("加法结合律", top_k=5)
        assert state.error is None
        assert state.results, "检索无结果"
        assert state.results[0]["theorem"] == "add_assoc"
        scores = [r["score"] for r in state.results]
        assert scores == sorted(scores, reverse=True), "结果必须按分数降序"

    def test_search_empty_query_reports_error_without_crashing(self, controller):
        state = controller.search("   ")
        assert state.error and state.results == []

    def test_build_graph_records_gaps_separately(self, controller):
        state = controller.build_graph("add_assoc", ["add_comm", "mul_comm"])
        assert state.graph is not None
        assert len(state.graph["nodes"]) >= 2
        # index_gap ≠ 定理不存在：必须单独成列
        assert "index_gaps" in state.graph
        assert "broken_refs" in state.graph

    def test_export_html_has_no_external_links(self, controller, tmp_path):
        out = tmp_path / "graph.html"
        controller.export_html(out, "add_assoc")
        text = out.read_text(encoding="utf-8")
        assert "http://" not in text and "https://" not in text, "K8：导出 HTML 必须 0 外链"
        assert "add_assoc" in text, "导出物必须含所选定理（不是空壳页面）"

    def test_export_without_selection_raises(self, controller, tmp_path):
        with pytest.raises(ValueError):
            controller.export_html(tmp_path / "x.html")


class TestViewerWiring:
    """静态接线断言：按钮没有 connect 就是死壳（HWS-formal 原缺陷）"""

    def _source(self):
        return (VIEWER_DIR / "main.py").read_text(encoding="utf-8")

    def test_search_button_is_connected(self):
        src = self._source()
        tree = ast.parse(src)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "connect":
                target = ast.unparse(node.func.value) if hasattr(ast, "unparse") else ""
                found.append(target)
        assert any("search_button.clicked" in t for t in found), \
            "检索按钮未 connect 到任何槽函数（空壳）"
        assert any("export_button.clicked" in t for t in found), \
            "导出按钮未 connect 到任何槽函数（空壳）"

    def test_window_calls_controller(self):
        src = self._source()
        for call in ("controller.search(", "controller.build_graph(", "controller.export_html("):
            assert call in src, f"GUI 未调用业务层：{call}"

    def test_selftest_path_is_qt_free(self):
        """--selftest 必须能在无 Qt 环境跑（CI 无图形）"""
        src = self._source()
        head, _, _ = src.partition("def _build_window")
        assert "import PySide6" not in head, \
            "--selftest 路径不得在模块顶层导入 Qt"

    def test_qt_missing_returns_exit_3(self):
        """缺 PySide6 时窗口模式返回 3（依赖缺失），不得静默 exit 0"""
        src = self._source()
        assert "return 3" in src


class TestViewerPackaging:
    def test_viewer_in_frozen_spec(self):
        spec = SPEC.read_text(encoding="utf-8")
        assert "viewer" in spec, "冻结产物 spec 未收查看器入口"
        assert "hws-formal-math-viewer" in spec, "查看器产物未命名（Release 附件里不会有它）"

    def test_readme_documents_viewer(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        assert "viewer" in readme.lower(), "README 未写查看器用法"
        assert "--selftest" in readme, "README 未写查看器自检命令"
