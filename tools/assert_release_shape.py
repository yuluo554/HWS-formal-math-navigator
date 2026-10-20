"""发布前断言：冻结产物与 zip 必须同时含 CLI 与查看器

preflight ㉕ 的机械落点：形态写进题面就必须有产物进附件。
CI 的 build job 在打包后调用：python tools/assert_release_shape.py --dist dist --release release

D3 修复要点：旧实现用子串判定 `any(CLI in n for n in names)`，而
CLI='hws-formal-math' 是 VIEWER='hws-formal-math-viewer' 的**前缀** ——
一个只含查看器的 zip 会被判 "✅ 含 CLI + 查看器"。负控实测过 rc=0。
现在一律 `PurePosixPath(n).name` 精确比较（== stem 或 == stem + '.exe'）。
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import PurePosixPath
from pathlib import Path

CLI = "hws-formal-math"
VIEWER = "hws-formal-math-viewer"

EXECUTABLE_SUFFIXES = ("", ".exe")


def _is_executable_entry(name: str, stem: str) -> bool:
    """zip 内某条目是否是 `stem` 本体（**精确** basename 比较）

    D3：不能用 `stem in name` —— 前缀关系会让 viewer 顶替 CLI。
    """
    base = PurePosixPath(name.replace("\\", "/")).name
    return base in {stem + suffix for suffix in EXECUTABLE_SUFFIXES}


def _exists(directory: Path, stem: str) -> bool:
    return (directory / stem).is_file() or (directory / (stem + ".exe")).is_file()


def _zip_entries(zip_path: Path) -> list:
    return zipfile.ZipFile(zip_path).namelist()


def check(dist_dir: Path, release_dir: Path) -> int:
    """形态断言主逻辑（测试直接调用，CI 走 main）"""
    frozen = dist_dir / CLI
    if not frozen.is_dir():
        print(f"❌ 冻结产物目录不存在: {frozen}")
        return 1

    missing = [n for n in (CLI, VIEWER) if not _exists(frozen, n)]
    if missing:
        print(f"❌ 冻结产物缺可执行件: {', '.join(missing)}（preflight ㉕：形态产物必须进附件）")
        print("   实际内容：", sorted(p.name for p in frozen.iterdir())[:20])
        return 1
    print(f"✅ 冻结产物含双 exe：{CLI} / {VIEWER}")

    zips = sorted(release_dir.glob("*.zip"))
    if not zips:
        print("❌ release 目录没有 zip")
        return 1

    zip_path = zips[0]
    names = _zip_entries(zip_path)

    has_cli = any(_is_executable_entry(n, CLI) for n in names)
    has_viewer = any(_is_executable_entry(n, VIEWER) for n in names)

    if not has_viewer:
        print(f"❌ {zip_path.name} 内缺查看器（preflight ㉕）")
        return 1
    if not has_cli:
        print(f"❌ {zip_path.name} 内缺 CLI（注意：CLI 名是查看器名的前缀，必须精确比较）")
        return 1
    print(f"✅ {zip_path.name} 内含 CLI + 查看器（basename 精确匹配）")

    demo = release_dir / "demo.gif"
    if not demo.is_file():
        print("❌ release 目录缺 demo.gif（题面 §三 第 7 项）")
        return 1
    print(f"✅ demo.gif 已就位（{demo.stat().st_size} 字节）")
    return 0


def main(argv=None) -> int:
    from _encoding import ensure_utf8_stdio
    ensure_utf8_stdio()

    ap = argparse.ArgumentParser(description="发布产物形态断言")
    ap.add_argument("--dist", type=Path, default=Path("dist"))
    ap.add_argument("--release", type=Path, default=Path("release"))
    args = ap.parse_args(argv)
    return check(args.dist, args.release)


if __name__ == "__main__":
    sys.exit(main())
