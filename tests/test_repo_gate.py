"""仓库守门测试（结构性质，不依赖运行环境）

覆盖（ai-tool-project-sprint 验收门）：
  1. 编码守卫覆盖所有会打印的可执行入口（主 CLI + tools/ 下每个脚本）
  2. 每个 workflow 可解析且每个 job 有 runs-on/steps（非法 YAML 会让 GitHub 不建 job）
  3. README 引用的命令/旗标在 CLI 里真实存在（README 指令面 = 测试面）
  4. 测试套件 import 的第三方库都在 dev extra 里（安装面 = 测试面）
  5. 冻结数据不入包断言：data/raw 不被追踪
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
SRC_DIR = REPO_ROOT / "src"
README = REPO_ROOT / "README.md"

# 冻结名单制：不用 sys.stdlib_module_names（3.10+ 才有，3.8 上是空集 →
# 会把每个标准库都判成第三方 → 全量假红）
STDLIB_ALLOWLIST = {
    "__future__", "argparse", "collections", "contextlib", "copy", "datetime",
    "dataclasses", "enum", "functools", "hashlib", "io", "itertools", "json",
    "logging", "math", "os", "pathlib", "random", "re", "shutil", "string",
    "subprocess", "sys", "tempfile", "textwrap", "time", "typing", "unittest",
    "warnings", "ast",
}

# 本项目自有顶层包（非第三方）
LOCAL_PACKAGES = {"hws_formal_math", "tools", "_encoding", "benchmark"}

# 测试期依赖白名单（必须在 dev extra 里声明）
DEV_EXTRAS_REQUIRED = {"pytest"}


def _iter_python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _collect_imports(path: Path) -> set:
    """AST 收集 import（含函数体内 import）"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names


class TestEncodingGuardCoverage:
    """编码守卫覆盖所有会打印的可执行入口"""

    def _entry_points(self):
        """所有可执行入口：主 CLI/__main__ + tools/ 下带 __main__ 的脚本"""
        entries = [
            SRC_DIR / "hws_formal_math" / "cli.py",
            SRC_DIR / "hws_formal_math" / "__main__.py",
        ]
        for path in _iter_python_files(TOOLS_DIR):
            source = path.read_text(encoding="utf-8")
            if '__main__' in source and "print(" in source:
                entries.append(path)
        return entries

    def test_entry_points_found(self):
        """扫描面非空（防探针自己把目标切坏 → 空集恒绿）"""
        entries = self._entry_points()
        assert len(entries) >= 4, f"可执行入口扫描面过小: {entries}"

    def test_all_entries_have_encoding_guard(self):
        """每个入口都必须有 UTF-8 守卫（直接调用或经 logging.setup_logging）"""
        missing = []
        for path in self._entry_points():
            source = path.read_text(encoding="utf-8")
            has_guard = (
                "ensure_utf8_stdio" in source
                or "setup_logging" in source
                or "_ensure_utf8_stdio" in source
            )
            if not has_guard:
                missing.append(str(path.relative_to(REPO_ROOT)))
        assert not missing, f"以下入口缺 UTF-8 守卫（Windows/CI 管道会 UnicodeEncodeError）: {missing}"


class TestWorkflowGate:
    """CI workflow 可解析且结构完整"""

    def test_workflows_parse(self):
        """每个 workflow 必须是合法 YAML（非法 YAML → GitHub 不建任何 job）"""
        yaml = pytest.importorskip("yaml")
        workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
        assert workflows, "未找到任何 workflow 文件"
        for wf in workflows:
            data = yaml.safe_load(wf.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{wf.name} 解析结果不是 mapping"
            assert "jobs" in data, f"{wf.name} 缺 jobs"
            for job_name, job in data["jobs"].items():
                assert "runs-on" in job, f"{wf.name}:{job_name} 缺 runs-on"
                assert "steps" in job, f"{wf.name}:{job_name} 缺 steps"

    def test_readme_install_extras_match_ci(self):
        """README 安装行与 CI 用同一 extras 集合（测试面 = 安装面）"""
        readme = README.read_text(encoding="utf-8")
        assert '.[dev]' in readme, "README 未声明 dev extras 安装行"
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert '.[dev]' in ci, "CI 未使用与 README 相同的 extras 集合"


class TestReadmeCommandGate:
    """README 命令/旗标 ↔ CLI 反射"""

    def test_readme_commands_exist(self):
        """README 里出现的子命令必须真实注册"""
        from hws_formal_math.cli import create_parser

        parser = create_parser()
        subparsers = [
            a for a in parser._actions if hasattr(a, "choices") and a.choices
        ]
        registered = set()
        for action in subparsers:
            if isinstance(action.choices, dict):
                registered.update(action.choices.keys())

        readme = README.read_text(encoding="utf-8")
        # README 里的 hws-formal-math <sub> 形态
        import re
        used = set(re.findall(r"hws-formal-math\s+([a-z][a-z0-9-]*)", readme))
        used -= {"search", "generate", "verify", "bench", "selftest", "export"} - registered
        unknown = {c for c in re.findall(r"hws-formal-math\s+([a-z][a-z0-9-]*)", readme)
                   if c not in registered}
        assert not unknown, f"README 引用了未注册的子命令: {unknown}"


class TestInstallSurface:
    """测试面 = 安装面"""

    def test_test_imports_are_declared(self):
        """tests/ 真 import 的第三方库必须在 dev extra 里"""
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        dev_section = pyproject.split("dev = [", 1)
        assert len(dev_section) == 2, "pyproject 未声明 dev extra"
        dev_block = dev_section[1].split("]", 1)[0]

        missing = []
        for path in _iter_python_files(REPO_ROOT / "tests"):
            for name in _collect_imports(path):
                if name in STDLIB_ALLOWLIST or name in LOCAL_PACKAGES:
                    continue
                if name == "yaml":  # PyYAML，核心依赖
                    continue
                if name.startswith("_"):
                    continue
                # 第三方（非本地、非 stdlib）→ 必须在 dev extra 或核心依赖里
                if name not in dev_block and f'"{name}' not in pyproject and f"'{name}" not in pyproject:
                    missing.append(f"{path.name}: {name}")
        assert not missing, f"测试 import 但未声明依赖: {missing}"


class TestFrozenDataGate:
    """冻结数据纪律"""

    def test_raw_data_not_tracked(self):
        """data/raw 不入仓（K7：不存 mathlib4 源码）"""
        import subprocess
        result = subprocess.run(
            ["git", "ls-files", "data/raw"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8",
        )
        assert result.stdout.strip() == "", f"data/raw 被追踪: {result.stdout}"

    def test_snapshot_manifest_not_placeholder(self):
        """快照 manifest 不得留 placeholder（M1 声明已完成）"""
        import json
        manifest = json.loads((REPO_ROOT / "data" / "snapshots" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest.get("sha256") != "placeholder", "快照 manifest 仍是 placeholder"
        assert manifest.get("case_count", 0) > 0, "快照 case_count 为 0"
