"""仓库守门测试（结构性质，不依赖运行环境）

覆盖（ai-tool-project-sprint 验收门）：
  1. 编码守卫覆盖所有会打印的可执行入口（主 CLI + tools/ 下每个脚本）
  2. 每个 workflow 可解析且每个 job 有 runs-on/steps（非法 YAML 会让 GitHub 不建 job）
  3. README 引用的命令/旗标在 CLI 里真实存在（README 指令面 = 测试面）
  4. 测试套件 import 的第三方库都在 dev extra 里（安装面 = 测试面）
  5. 冻结数据不入包断言：data/raw 不被追踪
  6. Python floor 五处一致（pyproject / classifiers / CI 矩阵 / README / RELEASE-NOTES）
  7. 版本号单源（pyproject ↔ __version__）
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
SRC_DIR = REPO_ROOT / "src"
README = REPO_ROOT / "README.md"
RELEASE_NOTES = REPO_ROOT / "RELEASE-NOTES.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# 本项目自有顶层包（非第三方）
LOCAL_PACKAGES = {"hws_formal_math", "tools", "_encoding", "benchmark"}

# 测试期依赖白名单（必须在 dev extra 里声明）
DEV_EXTRAS_REQUIRED = {"pytest"}

# Python floor 单源值（DEC1=B）。改这里之前先读 plan/RELEASE-M8.md 的决策记录。
PYTHON_FLOOR = "3.12"


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
        """tests/ 真 import 的第三方库必须在 dev extra 里

        v0.1.2（floor>=3.12）起用 `sys.stdlib_module_names` 判标准库，
        不再手写 STDLIB_ALLOWLIST（那是 3.8 的绕行：3.8 上该集合为空）。
        """
        pyproject = PYPROJECT.read_text(encoding="utf-8")
        dev_section = pyproject.split("dev = [", 1)
        assert len(dev_section) == 2, "pyproject 未声明 dev extra"
        dev_block = dev_section[1].split("]", 1)[0]

        missing = []
        for path in _iter_python_files(REPO_ROOT / "tests"):
            for name in _collect_imports(path):
                if name in sys.stdlib_module_names or name in LOCAL_PACKAGES:
                    continue
                if name == "yaml":  # PyYAML，核心依赖
                    continue
                if name.startswith("_"):
                    continue
                # 第三方（非本地、非 stdlib）→ 必须在 dev extra 或核心依赖里
                if name not in dev_block and f'"{name}' not in pyproject and f"'{name}" not in pyproject:
                    missing.append(f"{path.name}: {name}")
        assert not missing, f"测试 import 但未声明依赖: {missing}"


class TestSelfReportedTestCount:
    """自述测试数必须等于实际收集数（D13 的机械守门）

    D13 的形态是"文档写 185、实际 212"——已发布的数字与实物不符。
    v0.1.2 期间又复发过一次（README 写 227、实际 263），所以这里把它变成可执行的判据：
    **用当前 pytest 的真实收集数对撞 README 里的数字**。

    自指性说明：本测试自己也算一条，因此 README 里的数字必须等于**含本测试在内**的总数。
    改测试数量后必须同步改 README —— 这就是想要的效果。
    """

    def _collected_total(self) -> int:
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8",
        )
        match = re.search(r"(\d+) tests? collected", result.stdout)
        assert match, f"未解析到收集数：{result.stdout[-400:]}"
        return int(match.group(1))

    def test_readme_count_matches_collection(self):
        total = self._collected_total()
        readme = README.read_text(encoding="utf-8")
        match = re.search(r"\*\*(\d+) 项测试全绿\*\*", readme)
        assert match, "README「验证与质量」未写测试数"
        stated = int(match.group(1))
        assert stated == total, (
            f"README 自述 {stated} 项，实际收集 {total} 项（D13 复发）"
        )

    def test_readme_code_block_count_matches(self):
        """README 里的可粘贴命令注释也必须同数（同一个数字的两处写法）"""
        total = self._collected_total()
        readme = README.read_text(encoding="utf-8")
        assert f"# {total} passed" in readme, f"README 命令注释未写 {total} passed"

    def test_release_notes_count_matches_collection(self):
        """RELEASE-NOTES 的测试数同样必须对撞（它进 Release 正文）"""
        total = self._collected_total()
        notes = RELEASE_NOTES.read_text(encoding="utf-8")
        match = re.search(r"\*\*(\d+) tests passed\*\*", notes)
        assert match, "RELEASE-NOTES 未写 tests passed"
        assert int(match.group(1)) == total, (
            f"RELEASE-NOTES 自述 {match.group(1)}，实际 {total}"
        )


class TestPythonFloorGate:
    """Python floor 五处一致（DEC1=B：>=3.12）

    这条门是"改 floor 只改一半"的机械拦截：pyproject / classifiers /
    CI 矩阵 / README / RELEASE-NOTES 必须同一个数字。
    """

    def test_requires_python_matches_floor(self):
        assert f'requires-python = ">={PYTHON_FLOOR}"' in PYPROJECT.read_text(encoding="utf-8")

    def test_classifier_matches_floor(self):
        text = PYPROJECT.read_text(encoding="utf-8")
        assert f'"Programming Language :: Python :: {PYTHON_FLOOR}"' in text

    def test_no_older_python_classifier(self):
        """不得残留更老的 classifier（改了 floor 却忘删 3.8 的典型形态）"""
        text = PYPROJECT.read_text(encoding="utf-8")
        found = re.findall(r'"Programming Language :: Python :: (\d+\.\d+)"', text)
        assert found, "一个 Python 版本的 classifier 都没有"
        older = [v for v in found if tuple(map(int, v.split("."))) < tuple(map(int, PYTHON_FLOOR.split(".")))]
        assert not older, f"残留更老的 classifier: {older}"

    def test_ci_matrix_matches_floor(self):
        ci = CI_YML.read_text(encoding="utf-8")
        assert f'"{PYTHON_FLOOR}"' in ci, f"CI 矩阵未使用 {PYTHON_FLOOR}"
        assert '"3.8"' not in ci, "CI 矩阵仍含已 EOL 的 3.8"

    def test_ci_floor_job_actually_runs(self):
        """CI 必须**真的跑** floor 版本（不只是出现在字符串里）"""
        ci = CI_YML.read_text(encoding="utf-8")
        block = ci.split("matrix:", 1)[1].split("steps:", 1)[0]
        assert "python-version" in block, "test job 的矩阵里没有 python-version"
        assert PYTHON_FLOOR in block

    def test_readme_states_floor(self):
        readme = README.read_text(encoding="utf-8")
        assert PYTHON_FLOOR in readme, f"README 未写 Python {PYTHON_FLOOR}"
        assert "Python 3.8" not in readme, "README 仍写 Python 3.8"

    def test_release_notes_state_floor(self):
        notes = RELEASE_NOTES.read_text(encoding="utf-8")
        assert "Python 3.8" not in notes, "RELEASE-NOTES 仍写 Python 3.8"

    def test_setuptools_floor_allows_pep639(self):
        """SPDX license 表达式要求 setuptools>=77（与 3.8 不可兼得）"""
        text = PYPROJECT.read_text(encoding="utf-8")
        assert 'setuptools>=77' in text, "build-system 未抬到 setuptools>=77"
        assert re.search(r'^license\s*=\s*"', text, re.MULTILINE), "license 未转 SPDX 表达式"
        assert "license = {text" not in text, "license 仍是旧 table 形态"

    def test_no_python38_workarounds_left(self):
        """3.8 绕行代码必须清掉（is_relative_to 现在可用）"""
        cli = (SRC_DIR / "hws_formal_math" / "cli.py").read_text(encoding="utf-8")
        build_index = (TOOLS_DIR / "build_index.py").read_text(encoding="utf-8")
        assert "is_relative_to" in cli, "cli.py 仍在用 str 前缀比较"
        assert "is_relative_to" in build_index, "build_index.py 仍在用 str 前缀比较"

    def test_stdlib_gate_uses_runtime_truth(self):
        """标准库判定必须来自 `sys.stdlib_module_names`，不得是手写名单

        只查"代码里有没有手写集合"：写一个**名字匹配自身**的字面量断言
        （如 `assert "STDLIB_ALLOWLIST" not in source`）会被它自己的注释绊红，
        这是「字面 grep 门」的经典失效形态。判据改成 AST：文件里不得存在
        名为 STDLIB_ALLOWLIST 的**赋值**。
        """
        tree = ast.parse((REPO_ROOT / "tests" / "test_repo_gate.py").read_text(encoding="utf-8"))
        assigned = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name)
        }
        assert "STDLIB_ALLOWLIST" not in assigned, "守门仍在用手写标准库白名单（3.8 绕行）"
        # 反向锚：必须真的用了运行时真值
        source = (REPO_ROOT / "tests" / "test_repo_gate.py").read_text(encoding="utf-8")
        assert "sys.stdlib_module_names" in source, "未使用 sys.stdlib_module_names 判标准库"


class TestVersionSingleSource:
    """版本号单源（D11）"""

    def test_version_matches_pyproject(self):
        from hws_formal_math import __version__

        match = re.search(r'^version\s*=\s*"([^"]+)"', PYPROJECT.read_text(encoding="utf-8"), re.MULTILINE)
        assert match, "pyproject.toml 没有 version"
        assert __version__ == match.group(1), (
            f"版本双源不一致：__version__={__version__} vs pyproject={match.group(1)}"
        )

    def test_version_has_no_hardcoded_duplicate(self):
        """__init__.py 不得再写死一个与 pyproject 无关的版本字符串

        允许有一个**兜底常量**（源码态读不到 pyproject 时用），
        但它必须与 pyproject 同值 —— 上面那条已覆盖。
        """
        init_source = (SRC_DIR / "hws_formal_math" / "__init__.py").read_text(encoding="utf-8")
        assert "importlib.metadata" in init_source, "未从安装元数据读版本"

    def test_cli_version_flag_works(self):
        """D7c：--version 必须可用且打印版本（此前 exit 2）"""
        from hws_formal_math import __version__
        from hws_formal_math.cli import main

        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        assert __version__


class TestFrozenDataGate:
    """冻结数据纪律

    其中两条门依赖 `git`（check-attr / ls-files）。**sdist 里没有 .git**，
    所以那里必须显式 `skip` 而不是变成假红或假绿：
      - 真红会让"发布物自带测试"永远失败（源码包不是缺陷）
      - 假绿更糟：`git ls-files` 在无 .git 时 stdout 为空，会被当成"没被追踪"
    在仓库与 CI 里 `.git` 一定存在，故这两条门实跑（见
    `test_git_attr_gates_are_active_in_repo` 的反向锚）。
    """

    HAS_GIT = (REPO_ROOT / ".git").exists()
    requires_git = pytest.mark.skipif(
        not HAS_GIT, reason="源码包（无 .git）内无法执行 git 判据；仓库/CI 内实跑"
    )

    def test_git_attr_gates_are_active_in_repo(self):
        """反向锚：仓库态必须有 .git，否则上面两条门会被永久 skip（假门）"""
        if (REPO_ROOT / "pyproject.toml").is_file() and (REPO_ROOT / "PKG-INFO").is_file():
            pytest.skip("源码包形态（有 PKG-INFO 无 .git），git 门按设计 skip")
        assert self.HAS_GIT, "仓库内没有 .git —— git 类守门会全部被 skip"

    @requires_git
    def test_raw_data_not_tracked(self):
        """data/raw 不入仓（K7：不存 mathlib4 源码）"""
        import subprocess
        result = subprocess.run(
            ["git", "ls-files", "data/raw"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "", f"data/raw 被追踪: {result.stdout}"

    def test_snapshot_manifest_not_placeholder(self):
        """快照 manifest 不得留 placeholder（M1 声明已完成）"""
        import json
        manifest = json.loads((REPO_ROOT / "data" / "snapshots" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest.get("sha256") != "placeholder", "快照 manifest 仍是 placeholder"
        assert manifest.get("case_count", 0) > 0, "快照 case_count 为 0"

    def test_all_data_manifests_register_sha256(self):
        """D4：每个承载数据的 manifest 都必须登记 sha256（缺登记 = 漂移无人发现）"""
        import json
        manifests = [
            "data/index/manifest.json",
            "data/snapshots/manifest.json",
            "data/snapshots/v1/manifest.json",
            "data/proposals/v1/manifest.json",
        ]
        missing = []
        for rel in manifests:
            data = json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))
            if not data.get("sha256"):
                missing.append(rel)
        assert not missing, f"manifest 未登记 sha256: {missing}"

    def test_data_integrity_gate_passes(self):
        """数据自证门在仓库当前状态必须通过（篡改时由负控测试覆盖）"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "check_data_integrity", str(TOOLS_DIR / "check_data_integrity.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.check(REPO_ROOT / "data", strict=True) == 0

    def test_data_integrity_gate_detects_tampering(self, tmp_path):
        """负控：把 snapshots.json 追加 1 字节 → 门必须非 0"""
        import importlib.util
        import shutil

        spec = importlib.util.spec_from_file_location(
            "check_data_integrity_neg", str(TOOLS_DIR / "check_data_integrity.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        data_copy = tmp_path / "data"
        shutil.copytree(REPO_ROOT / "data", data_copy,
                        ignore=shutil.ignore_patterns("raw"))
        target = data_copy / "snapshots" / "v1" / "snapshots.json"
        target.write_bytes(target.read_bytes() + b" ")

        assert module.check(data_copy, strict=True) != 0

    @requires_git
    def test_gitattributes_freezes_nested_data(self):
        """D4：二级路径也必须 text: unset（`*` 不匹配子目录）

        这是"验证命令本身"，必须真问 git —— 只读 .gitattributes 文本会漏掉
        "规则写了但不匹配"的形态。
        """
        import subprocess

        paths = [
            "data/index/theorems.jsonl",
            "data/snapshots/manifest.json",
            "data/snapshots/v1/snapshots.json",
            "data/snapshots/v1/manifest.json",
            "data/proposals/v1/proposals.json",
            "data/proposals/v1/manifest.json",
        ]
        result = subprocess.run(
            ["git", "check-attr", "-a", *paths],
            cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode == 0, result.stderr

        by_path = {}
        for line in result.stdout.strip().splitlines():
            path, attr, value = (part.strip() for part in line.split(":", 2))
            by_path.setdefault(path, {})[attr] = value

        not_frozen = [p for p in paths if by_path.get(p, {}).get("text") != "unset"]
        assert not not_frozen, f"以下数据文件未被 -text 冻结（EOL 会漂移）: {not_frozen}"


class TestReleasePackagingGate:
    """发布打包器守门（跨平台附件）"""

    def _pkg(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "package_release", str(TOOLS_DIR / "package_release.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_platform_suffix_is_not_hardcoded(self):
        """平台后缀必须**随平台实算**，不得写死

        关键技术点（本轮变异验证抓出的假门）：不能只断言"后缀等于当前平台的值"——
        在 Windows 上跑时，写死的 `win64` 恰好等于正确值，门**恒绿**（假门）。
        正解 = 用 monkeypatch **伪造 `sys.platform`/`platform.machine()`** 再断言输出随之变化，
        这样与"当前跑在哪个平台"解耦：写死后缀的实现，在伪造 linux 时立刻暴露。
        """
        module = self._pkg()

        # Linux x86_64
        monkeypatch_target = module
        orig_platform, orig_machine = module.sys.platform, module.platform.machine
        try:
            module.sys.platform = "linux"
            module.platform.machine = lambda: "x86_64"
            assert module.platform_suffix() == "linux-x86_64", module.platform_suffix()

            # Linux arm64
            module.platform.machine = lambda: "aarch64"
            assert module.platform_suffix() == "linux-arm64", module.platform_suffix()

            # macOS arm64
            module.sys.platform = "darwin"
            module.platform.machine = lambda: "arm64"
            assert module.platform_suffix() == "macos-arm64", module.platform_suffix()

            # macOS x86_64
            module.platform.machine = lambda: "x86_64"
            assert module.platform_suffix() == "macos-x86_64", module.platform_suffix()

            # Windows
            module.sys.platform = "win32"
            module.platform.machine = lambda: "AMD64"
            assert module.platform_suffix() == "win64", module.platform_suffix()
        finally:
            module.sys.platform = orig_platform
            module.platform.machine = orig_machine

    def test_platform_suffix_varies_with_platform(self):
        """阴性对照：后缀必须随平台**变化**（写死实现的直接判据）"""
        module = self._pkg()

        orig_platform, orig_machine = module.sys.platform, module.platform.machine
        try:
            module.sys.platform = "linux"
            module.platform.machine = lambda: "x86_64"
            linux = module.platform_suffix()

            module.sys.platform = "darwin"
            module.platform.machine = lambda: "arm64"
            macos = module.platform_suffix()

            assert linux != macos, f"平台后缀未随平台变化（疑似写死）: {linux} == {macos}"
            assert linux.startswith("linux-") and macos.startswith("macos-")
        finally:
            module.sys.platform = orig_platform
            module.platform.machine = orig_machine

    def test_suffix_encodes_arch_where_applicable(self):
        """架构须体现在后缀里（arm64 与 x86_64 不可同名，否则用户下错包）

        注意：Windows 的后缀是 `win64`（无短横线），故只对 unix 平台断言含 `-<arch>`。
        断言锚定"架构是否进入后缀"，不含别的判据（防张冠李戴）。
        """
        import sys as _sys

        module = self._pkg()
        source = (TOOLS_DIR / "package_release.py").read_text(encoding="utf-8")
        assert "platform.machine()" in source, "平台后缀未实算架构"

        suffix = module.platform_suffix()
        if not _sys.platform.startswith("win"):
            # linux-x86_64 / macos-arm64 形态：必须含短横线 + 架构段
            assert "-" in suffix, f"unix 后缀应含架构段: {suffix}"
            assert suffix.split("-", 1)[1] in ("x86_64", "arm64"), suffix

    def test_exec_bit_preserved_in_zip(self, tmp_path):
        """Unix 可执行位必须写进 zip（写死 0o644 会让 Linux/macOS 产物解压后不可执行）"""
        module = self._pkg()

        src = tmp_path / "dist" / "hws-formal-math"
        src.mkdir(parents=True)
        exe = src / "hws-formal-math"          # 无扩展名主程序
        exe.write_bytes(b"\x7fELF fake")
        exe.chmod(0o755)
        lib = src / "libfoo.so"
        lib.write_bytes(b"fake")
        lib.chmod(0o644)                        # 共享库无 exec 位 → 兜底规则应补上
        textual = src / "readme.txt"
        textual.write_text("hi", encoding="utf-8")

        zip_path = tmp_path / "out.zip"
        module.build_zip(src, zip_path, "hws-formal-math")

        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            perms = {i.filename.split("/")[-1]: (i.external_attr >> 16) & 0o777
                     for i in zf.infolist()}

        assert perms["hws-formal-math"] & 0o111, f"主程序缺可执行位: {oct(perms['hws-formal-math'])}"
        assert perms["libfoo.so"] & 0o111, "共享库缺可执行位兜底"
        assert not (perms["readme.txt"] & 0o111), "文本文件不应被标可执行"

    def test_build_zip_is_deterministic(self, tmp_path):
        """两次独立打包逐字节一致"""
        module = self._pkg()
        src = tmp_path / "d"
        src.mkdir()
        (src / "a.bin").write_bytes(b"AAA")
        (src / "b.bin").write_bytes(b"BBB")

        z1, z2 = tmp_path / "1.zip", tmp_path / "2.zip"
        module.build_zip(src, z1, "root")
        module.build_zip(src, z2, "root")
        assert z1.read_bytes() == z2.read_bytes(), "打包不确定（顺序/时间戳漂移）"

    def test_empty_source_is_loud(self, tmp_path):
        """打包面为空必须大声失败（'成功但 files: 0' 是假绿）"""
        module = self._pkg()
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(SystemExit):
            module.build_zip(empty, tmp_path / "x.zip", "root")

    def test_python_dist_copied_into_output_dir(self, tmp_path, monkeypatch):
        """--with-python-dist 必须把 sdist/wheel **拷进** output 目录

        实测缺陷：只把 dist 里的路径记进 manifest、没拷进 output 目录 →
        manifest 里有它、产物目录没有它 → 下游"齐备"断言必红
        （上传/发布收集的是 output 目录，不是 dist）。
        """
        module = self._pkg()

        dist = tmp_path / "dist"
        exe_dir = dist / "hws-formal-math"
        exe_dir.mkdir(parents=True)
        (exe_dir / "hws-formal-math").write_bytes(b"bin")
        (dist / "pkg-1.0.tar.gz").write_bytes(b"sdist")
        (dist / "pkg-1.0-py3-none-any.whl").write_bytes(b"wheel")

        out = tmp_path / "release"
        # 脚本按 `python tools/package_release.py` 调用（脚本目录在 sys.path[0]），
        # 故测试须同样把 tools/ 放进 sys.path —— 否则脚本顶部的 `from _encoding import ...` 会失败
        monkeypatch.syspath_prepend(str(TOOLS_DIR))
        monkeypatch.setattr(sys, "argv", [
            "package_release.py",
            "--dist", str(dist), "--output", str(out),
            "--tag", "v9.9.9", "--with-python-dist", "--suffix", "test-suffix",
        ])
        module.main()

        assert (out / "pkg-1.0.tar.gz").is_file(), "sdist 未拷进 output"
        assert (out / "pkg-1.0-py3-none-any.whl").is_file(), "wheel 未拷进 output"
        assert (out / "hws-formal-math-v9.9.9-test-suffix.zip").is_file(), "zip 未产出"


class TestReleaseAssetCompleteness:
    """发布附件齐备性守门"""

    def test_publish_asserts_all_platforms(self):
        """publish job 必须断言三平台 + sdist/wheel 齐备后才发布"""
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        head, sep, _ = ci.partition("Publish release")
        assert sep, "未找到发布步骤"
        for token in ("linux-", "win64", "macos-", ".tar.gz", ".whl"):
            assert token in head, f"发布前未断言附件齐备: {token}"

    def test_grep_pattern_not_starting_with_dash(self):
        """workflow 里的 grep 模式不得以 `-` 开头（会被当选项 → invalid option）

        实测缺陷：`grep -qE "-(linux-|win|macos-)"` 报 `grep: invalid option -- '('`。
        正解 = 显式 `grep -e <pattern>`（模式与选项分离）。
        """
        import re
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        # 找形如 grep [-flag...] "-..." 的裸模式
        bad = re.findall(r'grep\s+(-[A-Za-z]+\s+)+"-(?![eE]\b)', ci)
        assert not bad, f"grep 模式以 - 开头会被当选项: {bad}"


class TestCrossPlatformReleaseGate:
    """跨平台发布链守门"""

    def test_ci_builds_three_platforms(self):
        """CI 必须构建三平台（在对应原生 runner 上——PyInstaller 不能交叉编译）"""
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "ubuntu-latest" in ci, "缺 Linux 构建"
        assert "windows-latest" in ci, "缺 Windows 构建"
        assert "macos-latest" in ci, "缺 macOS 构建"

    def test_ci_smokes_frozen_exe_on_each_platform(self):
        """每个平台必须原生冒烟冻结产物（Linux/macOS 产物的唯一本体证据）"""
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "Smoke test frozen exe (native)" in ci, "缺原生冒烟步骤"

    def test_release_notes_file_exists(self):
        """publish job 读 --notes-file，该文件必须存在（缺则发布步骤必红）"""
        ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        if "--notes-file" in ci:
            import re
            m = re.search(r"--notes-file\s+(\S+)", ci)
            assert m, "未解析到 notes 文件参数"
            assert (REPO_ROOT / m.group(1)).is_file(), f"发布说明文件不存在：{m.group(1)}"

    def test_readme_documents_three_platforms(self):
        """README/发布说明必须写明三平台下载（否则用户不知道有 Linux/macOS 包）"""
        notes = (REPO_ROOT / "RELEASE-NOTES.md").read_text(encoding="utf-8")
        for token in ("win64", "linux-", "macos-"):
            assert token in notes, f"发布说明缺平台标识: {token}"
