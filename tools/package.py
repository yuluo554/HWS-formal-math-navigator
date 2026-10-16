"""打包脚本

构建 CLI 冻结产物 + sdist/wheel。

纪律（crash-loop-rescue）：
  - 构建产物留底到仓库树外，因为 `--clean` 类构建会先删 dist（构建失败时旧产物已没了）
  - 本脚本**不**先 rmtree 正式 dist：先建到临时目录，成功后原子替换（防"删了旧的、没建出新的"窗口）
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = REPO_ROOT / "tools" / "hws-formal-math.spec"


def build_cli(dist_dir: Path | None = None) -> None:
    """构建 CLI exe（走 spec 文件，保证 hiddenimports/datas 口径一致）"""
    cmd = ["pyinstaller", "--noconfirm", str(SPEC_FILE)]
    if dist_dir is not None:
        cmd.extend(["--distpath", str(dist_dir)])
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


def build_distribution() -> None:
    """构建全部产物（先建临时目录，成功后替换 dist）"""
    staging = REPO_ROOT / "dist.staging"
    if staging.exists():
        shutil.rmtree(staging)

    build_cli(dist_dir=staging)

    # 源码包与 wheel 直接进 staging
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", str(staging)],
        check=True,
        cwd=str(REPO_ROOT),
    )

    dist = REPO_ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    staging.rename(dist)


def compute_sha256(file_path: Path) -> str:
    """计算 sha256"""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_manifest(dist_dir: Path | None = None) -> list:
    """生成产物清单（确定性：按文件名排序）"""
    target = dist_dir or (REPO_ROOT / "dist")
    manifest = []
    for file_path in sorted(target.iterdir(), key=lambda p: p.name):
        if file_path.is_file():
            manifest.append({
                "file": file_path.name,
                "size": file_path.stat().st_size,
                "sha256": compute_sha256(file_path),
            })
    return manifest


if __name__ == "__main__":
    from _encoding import ensure_utf8_stdio

    ensure_utf8_stdio()
    build_distribution()
    print(json.dumps(generate_manifest(), ensure_ascii=False, indent=2))
