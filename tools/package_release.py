"""发布附件打包器（确定性 + 跨平台）

纪律（ai-tool-project-sprint 阶段 7 / 阶段 8）：
  - 附件名 ASCII + **带平台后缀**（gh CLI 会剥中文名；三平台 zip 不可同名）
  - `ZIP_STORED`（不压缩，避免压缩流跨版本漂移）+ 条目按路径显式排序 + 全条目固定 date_time
    → 同一 dist 树两次独立打包逐字节一致（可复跑的是"打包这一步"，exe 构建本身不承诺跨机一致）
  - **保留可执行位**：Unix 二进制解压后必须可直接运行——按源树 `stat` 的 exec 位定
    `0o755`/`0o644`（写死 0o644 会让 Linux/macOS 产物解压后不可执行）
  - 打包面 = 文件系统遍历后**显式 sort**（os.walk 顺序跨调用不稳定）

平台后缀由 `sys.platform` + `platform.machine()` 实算（不手写，防"在 mac 上打出 win64 名"）。

用法：
    py -3.12 tools/package_release.py --dist dist --output release --tag v0.1.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
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


def platform_suffix() -> str:
    """实算平台后缀（win64 / linux64 / macos-arm64 / macos-x86_64）

    不写死：避免在 mac 上打出 win64 名。arm64 与 x86_64 如实区分
    （PyInstaller 产物与架构绑定，同名会让用户下错）。
    """
    machine = platform.machine().lower()
    arch = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, machine)

    if sys.platform.startswith("win"):
        return "win64"
    if sys.platform == "darwin":
        return f"macos-{arch}"
    return f"linux-{arch}"


def _is_executable(path: Path) -> bool:
    """该文件在 zip 中是否应带可执行位

    两条判据（任一成立即 0o755）：
      ① 源树实算的 exec 位（PyInstaller 通常会给主程序设好；Windows 上恒无此位）
      ② 二进制形态兜底：无扩展名的主程序、`.so`/`.so.N`/`.dylib` 共享库
         —— 部分工具链拷进 dist 的 `.so` 是 0644，解压后 dlopen 可能因权限失败；
         兜底给 exec 位（对 Windows 无害，Windows 忽略 Unix 模式位）
    """
    try:
        if path.stat().st_mode & 0o111:
            return True
    except OSError:
        pass

    name = path.name.lower()
    if name.endswith((".so", ".dylib")):
        return True
    if ".so." in name:          # 带版本号的共享库，如 libfoo.so.1.2
        return True
    if "." not in name:         # 无扩展名 → 主程序（hws-formal-math）
        return True
    return False


def build_zip(source_dir: Path, zip_path: Path, arc_root: str) -> None:
    """把 source_dir 打成确定性 zip（ZIP_STORED + 排序 + 固定时间戳 + 保留可执行位）"""
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
            # Unix 可执行位：按源树实算（0o755 vs 0o644）——写死 0o644 会让
            # Linux/macOS 产物解压后不可执行
            mode = 0o755 if _is_executable(path) else 0o644
            info.external_attr = mode << 16
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
    parser.add_argument(
        "--with-python-dist",
        action="store_true",
        help="同时收取 sdist/wheel（平台无关，只应在单一平台构建一次，避免附件重名）",
    )
    parser.add_argument("--suffix", default=None, help="覆盖平台后缀（默认实算）")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    suffix = args.suffix or platform_suffix()

    artifacts = []

    # CLI 冻结产物（onedir → zip）
    exe_dir = args.dist / args.name
    if exe_dir.is_dir():
        zip_name = f"{args.name}-{args.tag}-{suffix}.zip"
        zip_path = args.output / zip_name
        build_zip(exe_dir, zip_path, args.name)
        artifacts.append(zip_path)
    else:
        print(f"警告：未找到冻结产物目录 {exe_dir}，跳过 zip 打包")

    # sdist / wheel（平台无关，加 --with-python-dist 才收）
    if args.with_python_dist:
        for pattern in ("*.tar.gz", "*.whl"):
            for path in sorted(args.dist.glob(pattern)):
                artifacts.append(path)

    if not artifacts:
        print("错误：没有任何可打包产物")
        return 1

    manifest = []
    for path in artifacts:
        manifest.append({
            "file": path.name,
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        })

    # 每个平台各自写往自己的子目录，避免三平台互相覆盖
    sums_path = args.output / f"SHA256SUMS-{suffix}.txt"
    sums_path.write_bytes(
        ("".join(f"{m['sha256']}  {m['file']}\n" for m in manifest)).encode("utf-8")
    )
    (args.output / f"manifest-{suffix}.json").write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
