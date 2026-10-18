"""桌面查看器入口（PySide6）

形态口径（plan/04 §3.4 / delivery-forms ㉕）：
  ① 主控件接业务函数：检索按钮 → ViewerController.search；导出按钮 → export_html
  ② 入口到产物有断言：`viewer --selftest` 与 `tests/test_viewer.py` 走同一条控制器链路
  ③ 产物进附件：spec 产出 `hws-formal-math-viewer`，随 Release zip 分发

无 PySide6 时：`python -m hws_formal_math.viewer --selftest` 仍可跑（零 Qt 路径），
窗口模式返回退出码 3（依赖缺失），**不静默退化成成功**。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..config import Config
from ..logging import _ensure_utf8_stdio
from .controller import ViewerController


def _run_selftest(controller: ViewerController) -> int:
    """零 Qt 自检：索引概况 + 检索 + 构图 + 导出，四步全过才算通过。"""
    _ensure_utf8_stdio()
    print("=== 查看器自检（零 Qt 路径）===")

    summary = controller.index_summary()
    if "error" in summary:
        print(f"❌ {summary['error']}")
        return 1
    print(f"✅ 索引可读：{summary['theorem_count']} 条（kind={summary['index_kind']}）")

    state = controller.search("加法结合律", top_k=5)
    if state.error or not state.results:
        print(f"❌ 检索失败：{state.error}")
        return 1
    print(f"✅ 检索命中 {len(state.results)} 条，首条 {state.results[0]['theorem']}")

    top = state.results[0]["theorem"]
    state = controller.build_graph(top, [r["theorem"] for r in state.results[1:4]])
    if state.graph is None:
        print(f"❌ 构图失败：{state.error}")
        return 1
    print(f"✅ 依赖图 {len(state.graph['nodes'])} 节点 / {len(state.graph['edges'])} 边"
          f"（断链 {len(state.graph['broken_refs'])}，index_gap {len(state.graph['index_gaps'])}）")

    out = Path("viewer-selftest.html")
    try:
        controller.export_html(out, top)
    except Exception as exc:
        print(f"❌ 导出失败：{exc}")
        return 1
    text = out.read_text(encoding="utf-8")
    if "http://" in text or "https://" in text:
        print("❌ 导出 HTML 含外链（K8 口径要求 0 外链）")
        return 1
    print(f"✅ 导出 HTML（0 外链）：{out}（{len(text)} 字节）")
    out.unlink(missing_ok=True)
    print("=== 查看器自检通过 ===")
    return 0


def _build_window(controller):
    """构建窗口（延迟导入 Qt，保证零 Qt 路径可跑）"""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
        QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
        QTextEdit, QVBoxLayout, QWidget,
    )

    class ViewerWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("形式化数学库导航 · 查看器")
            self.resize(1000, 680)
            self._build_ui()
            self._load_index_summary()

        def _build_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            outer = QVBoxLayout(central)

            top = QHBoxLayout()
            self.query_input = QLineEdit()
            self.query_input.setPlaceholderText("输入数学命题或关键词，如：加法结合律")
            self.query_input.returnPressed.connect(self._on_search)
            top.addWidget(self.query_input, 1)
            self.search_button = QPushButton("检索定理")
            self.search_button.clicked.connect(self._on_search)
            top.addWidget(self.search_button)
            self.export_button = QPushButton("导出依赖图 HTML")
            self.export_button.clicked.connect(self._on_export)
            top.addWidget(self.export_button)
            outer.addLayout(top)

            self.status_label = QLabel("就绪")
            outer.addWidget(self.status_label)

            splitter = QSplitter(Qt.Horizontal)
            self.result_table = QTableWidget(0, 3)
            self.result_table.setHorizontalHeaderLabels(["定理", "模块", "分数"])
            self.result_table.itemSelectionChanged.connect(self._on_select)
            splitter.addWidget(self.result_table)

            self.detail_view = QTextEdit()
            self.detail_view.setReadOnly(True)
            splitter.addWidget(self.detail_view)
            splitter.setSizes([520, 460])
            outer.addWidget(splitter, 1)

        def _load_index_summary(self):
            summary = controller.index_summary()
            if "error" in summary:
                self.status_label.setText(f"⚠ {summary['error']}")
                return
            self.status_label.setText(
                f"索引 {summary['theorem_count']} 条 · 类型 {summary['index_kind']} · "
                f"上游 {summary['upstream_commit']}")

        def _on_search(self):
            state = controller.search(self.query_input.text())
            self.result_table.setRowCount(0)
            for row, item in enumerate(state.results):
                self.result_table.insertRow(row)
                self.result_table.setItem(row, 0, QTableWidgetItem(item["theorem"]))
                self.result_table.setItem(row, 1, QTableWidgetItem(item["module"]))
                self.result_table.setItem(row, 2, QTableWidgetItem("%.4f" % item["score"]))
            if state.error:
                self.status_label.setText(f"⚠ {state.error}")
            else:
                self.status_label.setText(f"命中 {len(state.results)} 条")

        def _on_select(self):
            items = self.result_table.selectedItems()
            if not items:
                return
            theorem = items[0].text()
            others = [self.result_table.item(r, 0).text()
                      for r in range(self.result_table.rowCount())]
            state = controller.build_graph(theorem, others)
            if state.graph is None:
                self.status_label.setText(f"⚠ {state.error}")
                return
            self.detail_view.setPlainText(self._render_graph(theorem, state.graph))
            self.status_label.setText(
                f"{theorem}：{len(state.graph['nodes'])} 节点 / "
                f"{len(state.graph['edges'])} 边 / 断链 {len(state.graph['broken_refs'])} / "
                f"index_gap {len(state.graph['index_gaps'])}")

        def _render_graph(self, theorem, graph):
            lines = [f"定理：{theorem}", "",
                     f"节点 {len(graph['nodes'])} · 边 {len(graph['edges'])}", ""]
            for edge in graph["edges"][:80]:
                lines.append(f"  {edge['from']} → {edge['to']}")
            if graph["broken_refs"]:
                lines += ["", "断链（索引中不存在）："] + [f"  {x}" for x in graph["broken_refs"]]
            if graph["index_gaps"]:
                lines += ["", "index_gap（索引未覆盖该模块，不等于定理不存在）："] + \
                         [f"  {x}" for x in graph["index_gaps"]]
            return "\n".join(lines)

        def _on_export(self):
            theorem = controller.state.selected
            if not theorem:
                self.status_label.setText("⚠ 请先在结果表中选择一个定理")
                return
            out = Path("dependency-graph.html")
            try:
                controller.export_html(out, theorem)
            except Exception as exc:
                self.status_label.setText(f"⚠ 导出失败：{exc}")
                return
            self.status_label.setText(f"已导出：{out.resolve()}")

    return QApplication, ViewerWindow


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="hws-formal-math-viewer",
                                     description="形式化数学库导航 · 桌面查看器")
    parser.add_argument("--selftest", action="store_true", help="零 Qt 自检（无需图形环境）")
    parser.add_argument("--index-path", type=Path, default=None)
    args = parser.parse_args(argv)

    _ensure_utf8_stdio()
    config = Config.load()
    if args.index_path:
        config.index_path = args.index_path
    controller = ViewerController(config)

    if args.selftest:
        return _run_selftest(controller)

    try:
        import PySide6  # noqa: F401
    except ImportError:
        print("缺少 PySide6 依赖，请安装: pip install hws-formal-math-navigator[gui]",
              file=sys.stderr)
        return 3

    QApplication, ViewerWindow = _build_window(controller)
    app = QApplication(sys.argv)
    window = ViewerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
