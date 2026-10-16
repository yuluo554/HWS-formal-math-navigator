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
    "__future__", "argparse", "ast", "collections", "contextlib", "copy",
    "datetime", "dataclasses", "enum", "functools", "hashlib", "importlib",
    "io", "itertools", "json", "logging", "math", "os", "pathlib", "platform",
    "random", "re", "shutil", "string", "subprocess", "sys", "tempfile",
    "textwrap", "time", "typing", "unittest", "warnings", "zipfile",
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
