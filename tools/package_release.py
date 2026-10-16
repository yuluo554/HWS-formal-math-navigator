"""发布附件打包器（确定性）

纪律（ai-tool-project-sprint 阶段 7 / 阶段 8）：
  - 附件名 ASCII（gh CLI 会剥中文名）
  - `ZIP_STORED`（不压缩，避免压缩流跨版本漂移）+ 条目按路径显式排序 + 全条目固定 date_time
    → 同一 dist 树两次独立打包逐字节一致（可复跑的是"打包这一步"，exe 构建本身不承诺跨机一致）
  - 打包面 = 文件系统遍历后**显式 sort**（os.walk 顺序跨调用不稳定）

用法：
    py -3.12 tools/package_release.py --dist dist --output release --tag v0.1.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

# 固定时间戳（2026-01-01 00:00:00），使打包确定性
FIXED_DATE_TIME = (2026, 1, 1, 0, 0, 0)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_zip(source_dir: Path, zip_path: Path, arc_root: str) -> None:
    """把 source_dir 打成确定性 zip（ZIP_STORED + 排序 + 固定时间戳）"""
    files = sorted(
        (p for p in source_dir.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(source_dir).as_posix(),
    )
    if not files:
        raise SystemExit(f"打包面为空：{source_dir}（'成功但 files: 0' 是假绿信号）")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for path in files:
            rel = path.relative_to(source_dir).as_posix()
            info = zipfile.ZipInfo(filename=f"{arc_root}/{rel}", date_time=FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            with open(path, "rb") as f:
                zf.writestr(info, f.read())


def main() -> int:
    from _encoding import ensure_utf8_stdio
    ensure_utf8_stdio()

    parser = argparse.ArgumentParser(description="打包发布附件（确定性 zip）")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--output", type=Path, default=Path("release"))
    parser.add_argument("--tag", default="v0.1.0")
    parser.add_argument("--name", default="hws-formal-math")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    artifacts = []

    # CLI 冻结产物（onedir → zip）
    exe_dir = args.dist / args.name
    if exe_dir.is_dir():
        zip_name = f"{args.name}-{args.tag}-win64.zip"
        zip_path = args.output / zip_name
        build_zip(exe_dir, zip_path, args.name)
        artifacts.append(zip_path)

    # sdist / wheel 直接作为附件
    for pattern in ("*.tar.gz", "*.whl"):
        for path in sorted(args.dist.glob(pattern)):
            artifacts.append(path)

    manifest = []
    for path in artifacts:
        manifest.append({
            "file": path.name,
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        })

    (args.output / "SHA256SUMS.txt").write_bytes(
        ("".join(f"{m['sha256']}  {m['file']}\n" for m in manifest)).encode("utf-8")
    )
    (args.output / "manifest.json").write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
