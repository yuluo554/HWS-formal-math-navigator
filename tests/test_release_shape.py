"""发布形态门禁测试（D3）

D3 的失效形态：`assert_release_shape.py` 用子串判 zip 是否含 CLI，
而 CLI='hws-formal-math' 是 VIEWER='hws-formal-math-viewer' 的前缀 ——
一个**只含查看器**的 zip 会被判 "✅ 含 CLI + 查看器"，rc=0。

纪律：这类门必须做双向对照（正控 + 两条负控），只测一侧的探活本身无意义。
"""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
CLI = "hws-formal-math"
VIEWER = "hws-formal-math-viewer"


def _module():
    spec = importlib.util.spec_from_file_location(
        "assert_release_shape", str(TOOLS_DIR / "assert_release_shape.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_dist(tmp_path: Path, *, cli: bool = True, viewer: bool = True) -> Path:
    """造一个冻结产物目录（双 exe 可按需缺）"""
    dist = tmp_path / "dist"
    frozen = dist / CLI
    frozen.mkdir(parents=True)
    if cli:
        (frozen / f"{CLI}.exe").write_bytes(b"cli")
    if viewer:
        (frozen / f"{VIEWER}.exe").write_bytes(b"viewer")
    return dist


def _make_release(tmp_path: Path, entries, *, demo: bool = True) -> Path:
    """造 release 目录；entries 是 zip 内条目名列表"""
    release = tmp_path / "release"
    release.mkdir()
    with zipfile.ZipFile(release / "artifact-win64.zip", "w") as zf:
        for entry in entries:
            zf.writestr(entry, b"x")
    if demo:
        (release / "demo.gif").write_bytes(b"GIF89a")
    return release


class TestReleaseShapePositiveControl:
    """正控：双 exe 齐备 → exit 0"""

    def test_both_present_passes(self, tmp_path):
        module = _module()
        dist = _make_dist(tmp_path)
        release = _make_release(tmp_path, [
            f"{CLI}/{CLI}.exe",
            f"{CLI}/{VIEWER}.exe",
        ])
        assert module.check(dist, release) == 0


class TestReleaseShapeNegativeControls:
    """负控：任缺其一都必须非 0（这是 D3 的机械判据）"""

    def test_zip_with_only_viewer_fails(self, tmp_path):
        """**D3 的原始缺陷形态**：zip 只放查看器 → 必须非 0

        旧实现会打印 "✅ 内含 CLI + 查看器" 并 exit 0。
        """
        module = _module()
        dist = _make_dist(tmp_path)
        release = _make_release(tmp_path, [f"{CLI}/{VIEWER}.exe"])
        assert module.check(dist, release) != 0

    def test_zip_with_only_cli_fails(self, tmp_path):
        """zip 只放 CLI → 必须非 0"""
        module = _module()
        dist = _make_dist(tmp_path)
        release = _make_release(tmp_path, [f"{CLI}/{CLI}.exe"])
        assert module.check(dist, release) != 0

    def test_frozen_dist_missing_cli_fails(self, tmp_path):
        """冻结产物目录缺 CLI → 必须非 0"""
        module = _module()
        dist = _make_dist(tmp_path, cli=False)
        release = _make_release(tmp_path, [f"{CLI}/{CLI}.exe", f"{CLI}/{VIEWER}.exe"])
        assert module.check(dist, release) != 0

    def test_missing_demo_gif_fails(self, tmp_path):
        """缺 demo.gif → 必须非 0"""
        module = _module()
        dist = _make_dist(tmp_path)
        release = _make_release(
            tmp_path, [f"{CLI}/{CLI}.exe", f"{CLI}/{VIEWER}.exe"], demo=False
        )
        assert module.check(dist, release) != 0


class TestBasenameMatcher:
    """匹配器本身：前缀陷阱的直接判据"""

    def test_viewer_does_not_satisfy_cli(self):
        module = _module()
        assert not module._is_executable_entry(
            f"hws-formal-math/{VIEWER}.exe", CLI
        ), "查看器条目被误判成 CLI（前缀陷阱复现）"

    def test_cli_entry_satisfies_cli(self):
        module = _module()
        assert module._is_executable_entry(f"hws-formal-math/{CLI}.exe", CLI)

    def test_cli_without_exe_suffix(self):
        """Unix 产物没有 .exe，必须同样命中"""
        module = _module()
        assert module._is_executable_entry(f"hws-formal-math/{CLI}", CLI)

    def test_substring_is_not_enough(self):
        """文件名里含 CLI 但 basename 不等的条目不得命中"""
        module = _module()
        assert not module._is_executable_entry(
            f"hws-formal-math/{CLI}-backup.exe", CLI
        )
