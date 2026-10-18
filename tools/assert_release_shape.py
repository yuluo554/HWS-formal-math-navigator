"""发布前断言：冻结产物与 zip 必须同时含 CLI 与查看器

preflight ㉕ 的机械落点：形态写进题面就必须有产物进附件。
CI 的 build job 在打包后调用：python tools/assert_release_shape.py --dist dist --release release
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

CLI = "hws-formal-math"
VIEWER = "hws-formal-math-viewer"


def _exists(directory: Path, stem: str) -> bool:
    return (directory / stem).is_file() or (directory / (stem + ".exe")).is_file()


def main(argv=None) -> int:
    from _encoding import ensure_utf8_stdio
    ensure_utf8_stdio()

    ap = argparse.ArgumentParser(description="发布产物形态断言")
    ap.add_argument("--dist", type=Path, default=Path("dist"))
    ap.add_argument("--release", type=Path, default=Path("release"))
    args = ap.parse_args(argv)

    frozen = args.dist / CLI
    if not frozen.is_dir():
        print(f"❌ 冻结产物目录不存在: {frozen}")
        return 1
    missing = [n for n in (CLI, VIEWER) if not _exists(frozen, n)]
    if missing:
        print(f"❌ 冻结产物缺可执行件: {', '.join(missing)}（preflight ㉕：形态产物必须进附件）")
        print("   实际内容：", sorted(p.name for p in frozen.iterdir())[:20])
        return 1
    print(f"✅ 冻结产物含双 exe：{CLI} / {VIEWER}")

    zips = sorted(args.release.glob("*.zip"))
    if not zips:
        print("❌ release 目录没有 zip")
        return 1
    names = zipfile.ZipFile(zips[0]).namelist()
    if not any(VIEWER in n for n in names):
        print(f"❌ {zips[0].name} 内缺查看器（preflight ㉕）")
        return 1
    if not any(CLI in n for n in names):
        print(f"❌ {zips[0].name} 内缺 CLI")
        return 1
    print(f"✅ {zips[0].name} 内含 CLI + 查看器")

    demo = args.release / "demo.gif"
    if not demo.is_file():
        print("❌ release 目录缺 demo.gif（题面 §三 第 7 项）")
        return 1
    print(f"✅ demo.gif 已就位（{demo.stat().st_size} 字节）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
