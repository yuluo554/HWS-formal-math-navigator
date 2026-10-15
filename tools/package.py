"""打包脚本"""

import subprocess
import shutil
from pathlib import Path
import hashlib


def build_cli():
    """构建 CLI exe"""
    subprocess.run([
        "pyinstaller",
        "--name", "hws-formal-math",
        "--console",
        "--hidden-import", "hws_formal_math.cli",
        "src/hws_formal_math/cli.py"
    ], check=True)


def build_gui():
    """构建 GUI exe"""
    subprocess.run([
        "pyinstaller",
        "--name", "hws-formal-math-viewer",
        "--windowed",
        "--hidden-import", "hws_formal_math.viewer.main",
        "--collect-all", "PySide6",
        "src/hws_formal_math/viewer/main.py"
    ], check=True)


def build_distribution():
    """构建全部产物"""
    # 清理
    shutil.rmtree("dist", ignore_errors=True)
    
    # CLI
    build_cli()
    
    # GUI
    build_gui()
    
    # 源码包
    subprocess.run(["python", "-m", "build", "--sdist"], check=True)
    
    # wheel
    subprocess.run(["python", "-m", "build", "--wheel"], check=True)


def compute_sha256(file_path: Path) -> str:
    """计算 sha256"""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_manifest():
    """生成产物清单"""
    manifest = []
    for file_path in Path("dist").iterdir():
        if file_path.is_file():
            manifest.append({
                "file": file_path.name,
                "size": file_path.stat().st_size,
                "sha256": compute_sha256(file_path)
            })
    return manifest


if __name__ == "__main__":
    build_distribution()
