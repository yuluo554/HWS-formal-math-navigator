"""数据自证门：manifest 登记的 sha256 ↔ 磁盘实算（D4）

为什么需要它：D4 实测过三个文件的字节漂移（本机 CRLF / clone LF），
而 `grep -rn sha256 src/` 显示**运行时一次都没校验过**——manifest 里的数字
只是装饰。这个门把它变成可执行的判据。

口径：
  - 校验对象 = manifest 里**登记了** sha256 的每个数据文件
  - 无 sha256 字段 → 记「未登记」并按 `--strict` 决定是否算失败
    （非 strict 下只警告：缺登记本身就是缺陷，但不该让历史数据变红）
  - 不一致 → 非 0 退出，并打印两边的 sha256 与字节数

用法：
    python tools/check_data_integrity.py                 # 校验仓内 data/
    python tools/check_data_integrity.py --data-dir <p>  # 校验别处的数据树
    python tools/check_data_integrity.py --strict        # 缺登记也算失败
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# (manifest 相对路径, 被校验文件相对路径)
# 每条对应"manifest 里那个 sha256 描述的是谁"的既定语义。
CHECKS: Tuple[Tuple[str, str], ...] = (
    ("index/manifest.json", "index/theorems.jsonl"),
    ("snapshots/manifest.json", "snapshots/v1/snapshots.json"),
    ("snapshots/v1/manifest.json", "snapshots/v1/snapshots.json"),
    ("proposals/v1/manifest.json", "proposals/v1/proposals.json"),
)


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def check(data_dir: Path, strict: bool = False) -> int:
    """校验数据树；返回退出码（0 = 全部一致）"""
    if not data_dir.is_dir():
        print(f"❌ 数据目录不存在: {data_dir}")
        return 1

    failures: List[str] = []
    warnings: List[str] = []
    verified = 0

    for manifest_rel, target_rel in CHECKS:
        manifest_path = data_dir / manifest_rel
        target_path = data_dir / target_rel

        if not manifest_path.is_file():
            failures.append(f"{manifest_rel}: manifest 缺失")
            continue
        if not target_path.is_file():
            failures.append(f"{target_rel}: 被校验文件缺失")
            continue

        manifest = _load_json(manifest_path)
        if manifest is None:
            failures.append(f"{manifest_rel}: 不是合法 JSON")
            continue

        expected = manifest.get("sha256")
        actual = _sha256_of(target_path)

        if not expected:
            warnings.append(f"{manifest_rel}: 未登记 {target_rel} 的 sha256")
            continue

        if expected != actual:
            failures.append(
                f"{target_rel}: sha256 不一致\n"
                f"    期望 {expected}（{manifest_rel}）\n"
                f"    实际 {actual}（{target_path.stat().st_size} 字节）"
            )
            continue

        verified += 1
        print(f"✅ {target_rel}  sha256 {actual[:16]}…  （登记于 {manifest_rel}）")

    for warning in warnings:
        print(f"⚠️  {warning}")

    if failures:
        print()
        for failure in failures:
            print(f"❌ {failure}")
        print(f"\n数据自证失败：{len(failures)} 项不一致 / {verified} 项通过")
        return 1

    if strict and warnings:
        print(f"\n数据自证失败（--strict）：{len(warnings)} 项未登记")
        return 1

    print(f"\n✅ 数据自证通过：{verified} 实现对撞全一致")
    return 0


def main(argv=None) -> int:
    from _encoding import ensure_utf8_stdio
    ensure_utf8_stdio()

    ap = argparse.ArgumentParser(description="数据自证门（manifest.sha256 ↔ 磁盘实算）")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument(
        "--strict",
        action="store_true",
        help="manifest 缺 sha256 字段也算失败（CI 用这个）",
    )
    args = ap.parse_args(argv)
    return check(args.data_dir, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
