"""索引构建器

从 mathlib4 源码抽取索引元数据，只存定理名/签名/依赖边，不存源码。

遵循 K7（不存 mathlib4 源码）和 K4（同输入同结果）口径。
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


# 固定生成日期，确保确定性写盘
GENERATION_DATE = "2026-01-01"

# 确定性种子：文件扫描按文件名排序
def _sorted_paths(paths: List[Path]) -> List[Path]:
    """按路径字符串排序，确保确定性"""
    return sorted(paths, key=lambda p: str(p))


def build_index(mathlib4_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    构建 mathlib4 索引元数据
    
    Args:
        mathlib4_path: mathlib4 源码路径（用户自备，符合 K5）
        output_path: 输出路径
        
    Returns:
        索引 manifest
        
    Raises:
        FileNotFoundError: mathlib4_path 不存在
        ValueError: mathlib4_path 不是目录
    """
    if not mathlib4_path.exists():
        raise FileNotFoundError(f"mathlib4 路径不存在: {mathlib4_path}")
    
    if not mathlib4_path.is_dir():
        raise ValueError(f"mathlib4 路径不是目录: {mathlib4_path}")
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 扫描 .lean 文件
    lean_files = scan_lean_files(mathlib4_path)
    
    # 2. 解析定理声明和依赖
    theorems = []
    for lean_file in lean_files:
        # 计算模块路径
        module_path = _lean_file_to_module(lean_file, mathlib4_path)
        
        # 读取文件内容
        content = lean_file.read_text(encoding='utf-8')
        
        # 提取依赖
        deps = extract_dependencies(content)
        
        # 解析定理声明
        parsed_theorems = parse_theorem_declaration(content, module_path, deps)
        theorems.extend(parsed_theorems)
    
    # 3. 生成 theorems.jsonl
    theorems_file = output_path / "theorems.jsonl"
    _write_theorems_jsonl(theorems, theorems_file)
    
    # 4. 计算 sha256
    sha256_hash = _compute_sha256(theorems_file)
    
    # 5. 生成 manifest
    manifest = {
        "version": "1.1",
        "index_kind": "extracted",       # 由 mathlib4 源码实抽
        "upstream": "mathlib4",
        "upstream_commit": None,          # 由 build_index_with_commit 填入；不留 "unknown"
        "sha256": sha256_hash,
        "generation_date": GENERATION_DATE,
        "theorem_count": len(theorems),
        "domain_coverage": _compute_domain_coverage(theorems)
    }
    
    manifest_file = output_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    return manifest


def build_index_with_commit(
    mathlib4_path: Path,
    output_path: Path,
    commit_hash: str
) -> Dict[str, Any]:
    """
    构建 mathlib4 索引元数据（带 commit hash）
    
    Args:
        mathlib4_path: mathlib4 源码路径
        output_path: 输出路径
        commit_hash: mathlib4 commit hash
        
    Returns:
        索引 manifest
    """
    if not commit_hash or commit_hash.strip().lower() in ("unknown", "none", "null", "-"):
        raise ValueError("commit_hash 必须是 mathlib4 的真实 commit（不允许 unknown）")
    manifest = build_index(mathlib4_path, output_path)
    manifest["upstream_commit"] = commit_hash
    
    # 更新 manifest 文件
    manifest_file = output_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    return manifest


def scan_lean_files(mathlib4_path: Path) -> List[Path]:
    """
    扫描 .lean 文件
    
    递归扫描 src/ 目录，过滤 .git/ 等隐藏目录。
    文件按路径排序，确保确定性（K4）。
    
    Args:
        mathlib4_path: mathlib4 源码路径
        
    Returns:
        排序后的 .lean 文件路径列表
    """
    src_path = mathlib4_path / "src"
    if not src_path.exists():
        # 如果没有 src 目录，直接扫描根目录
        src_path = mathlib4_path
    
    # 使用 set 去重（Windows 文件系统不区分大小写，**/*.lean 和 **/*.Lean 可能匹配同一文件）
    lean_files = set()
    for pattern in ["**/*.lean", "**/*.Lean"]:
        lean_files.update(src_path.glob(pattern))
    
    # 过滤隐藏目录
    lean_files = {
        f for f in lean_files
        if not any(part.startswith('.') for part in f.parts)
    }
    
    return _sorted_paths(list(lean_files))


def _lean_file_to_module(lean_file: Path, mathlib4_path: Path) -> str:
    """
    将 .lean 文件路径转换为模块名
    
    例如：Mathlib/Algebra/Group/Defs.lean -> Mathlib.Algebra.Group.Defs
    """
    # 获取相对于 mathlib4_path 的路径
    # 注意：使用 str 比较而非 is_relative_to（Python 3.8 兼容）
    src_path = mathlib4_path / "src"
    src_str = str(src_path.resolve())
    lean_str = str(lean_file.resolve())
    
    if lean_str.startswith(src_str):
        rel_path = lean_file.relative_to(src_path)
    elif lean_str.startswith(str(mathlib4_path.resolve())):
        rel_path = lean_file.relative_to(mathlib4_path)
    else:
        rel_path = lean_file
    
    # 移除 .lean 后缀，替换路径分隔符
    module_name = str(rel_path.with_suffix(''))
    module_name = module_name.replace('/', '.').replace('\\', '.')
    
    return module_name


# 定理声明正则表达式
# 匹配：theorem/lemma/def 声明，包括类型签名
THEOREM_DECL_PATTERN = re.compile(
    r'^\s*(?:theorem|lemma|def|inductive|structure|class|instance)\s+'
    r'(\w+)'  # 名称
    r'\s*(?:\{[^}]*\}|\[[^\]]*\]|\([^)]*\))*'  # 类型参数（可选）
    r'\s*:\s*'  # 冒号
    r'(.+?)'  # 类型签名（非贪婪）
    r'\s*$',  # 行尾
    re.MULTILINE | re.DOTALL
)


def parse_theorem_declaration(
    content: str,
    module_path: str,
    deps: List[str]
) -> List[Dict[str, Any]]:
    """
    解析定理声明
    
    提取 theorem/lemma/def 名、类型签名、行号。
    
    Args:
        content: .lean 文件内容
        module_path: 模块路径
        deps: 依赖列表
        
    Returns:
        定理声明列表
    """
    theorems = []
    
    # 按行分割，逐行匹配
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 匹配定理声明
        match = re.match(
            r'^\s*(?:theorem|lemma|def|inductive|structure|class|instance)\s+(\w+)',
            line
        )
        
        if match:
            name = match.group(1)
            
            # 找到定理名后的冒号（不是参数列表中的冒号）
            # 定理名后的冒号是第一个不在括号内的冒号
            name_end = match.end()
            
            # 扫描从定理名结束位置开始，找到不在括号内的冒号
            colon_pos = -1
            brace_depth = 0
            paren_depth = 0
            bracket_depth = 0
            
            for pos in range(name_end, len(line)):
                char = line[pos]
                if char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
                elif char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1
                elif char == ':' and brace_depth == 0 and paren_depth == 0 and bracket_depth == 0:
                    colon_pos = pos
                    break
            
            if colon_pos != -1:
                signature = line[colon_pos + 1:].strip()
                
                # 如果签名跨多行，继续读取
                # 计算括号/大括号/中括号的平衡
                brace_count = signature.count('{') + signature.count('(') + signature.count('[')
                brace_count -= signature.count('}') + signature.count(')') + signature.count(']')
                
                # 如果冒号后内容为空，也继续读取下一行
                j = i + 1
                while (brace_count > 0 or not signature) and j < len(lines):
                    next_line = lines[j]
                    signature += ' ' + next_line.strip()
                    brace_count += next_line.count('{') + next_line.count('(') + next_line.count('[')
                    brace_count -= next_line.count('}') + next_line.count(')') + next_line.count(']')
                    j += 1
                
                # 移除行内注释
                signature = re.sub(r'--.*$', '', signature, flags=re.MULTILINE)
                signature = signature.strip()
                
                # 移除尾部的 := 或 where
                signature = re.split(r'\s*:=\s*|\s+where\s*$', signature)[0]
                
                theorems.append({
                    "module": module_path,
                    "name": name,
                    "signature": signature,
                    "deps": deps,
                    "line": i + 1  # 1-based 行号
                })
        
        i += 1
    
    return theorems


# import 语句正则表达式
# 匹配：import 后跟一个或多个模块名（空格分隔）
IMPORT_PATTERN = re.compile(
    r'^\s*import\s+(.+?)(?:\s*$|--)',
    re.MULTILINE
)


def extract_dependencies(content: str) -> List[str]:
    """
    提取依赖
    
    解析 import 语句，返回依赖模块列表。
    
    Args:
        content: .lean 文件内容
        
    Returns:
        依赖模块列表（已排序，确保确定性）
    """
    deps = []
    
    for match in IMPORT_PATTERN.finditer(content):
        import_stmt = match.group(1)
        # 分割多个 import（用空格分隔）
        for dep in import_stmt.split():
            dep = dep.strip()
            if dep:
                deps.append(dep)
    
    # 去重并排序（K4 确定性）
    return sorted(list(set(deps)))


def _write_theorems_jsonl(
    theorems: List[Dict[str, Any]],
    output_file: Path
) -> None:
    """
    写入 theorems.jsonl
    
    每行一个 JSON 对象，按模块名和定理名排序（K4 确定性）。
    """
    # 排序：先按模块名，再按定理名
    sorted_theorems = sorted(
        theorems,
        key=lambda t: (t["module"], t["name"])
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for theorem in sorted_theorems:
            # 确保 JSON key 排序（K4 确定性）
            line = json.dumps(theorem, sort_keys=True, ensure_ascii=False)
            f.write(line + '\n')


def _compute_sha256(file_path: Path) -> str:
    """计算文件 sha256"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def _compute_domain_coverage(theorems: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    计算领域覆盖度
    
    基于模块名前缀分类。
    """
    coverage = {
        "algebra": 0,
        "analysis": 0,
        "number_theory": 0,
        "combinatorics": 0,
        "geometry": 0,
        "topology": 0,
        "logic": 0,
        "other": 0
    }
    
    for theorem in theorems:
        module = theorem["module"].lower()
        
        # 按优先级匹配：先检查更具体的模式
        if "algebra" in module:
            coverage["algebra"] += 1
        elif "analysis" in module or "calculus" in module:
            coverage["analysis"] += 1
        elif "combinat" in module:
            coverage["combinatorics"] += 1
        elif "geometry" in module:
            coverage["geometry"] += 1
        elif "topology" in module:
            coverage["topology"] += 1
        elif "logic" in module or "tactic" in module:
            coverage["logic"] += 1
        elif "number" in module or module.startswith("mathlib.data.nat") or module.startswith("mathlib.data.int"):
            coverage["number_theory"] += 1
        else:
            coverage["other"] += 1
    
    return coverage


if __name__ == "__main__":
    import argparse
    from _encoding import ensure_utf8_stdio

    ensure_utf8_stdio()

    parser = argparse.ArgumentParser(description="构建 mathlib4 索引")
    parser.add_argument(
        "--mathlib4-path",
        type=Path,
        required=True,
        help="mathlib4 源码路径"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/index"),
        help="输出路径"
    )
    parser.add_argument(
        "--commit-hash",
        type=str,
        default=None,
        help="mathlib4 commit hash"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="验证已生成产物位级一致（不重新生成）"
    )
    
    args = parser.parse_args()
    
    if args.check:
        # 验证模式：重新生成并比对
        if not (args.output / "theorems.jsonl").exists():
            print("错误：--check 模式需要已存在的 theorems.jsonl")
            exit(1)
        
        # 读取现有产物
        with open(args.output / "theorems.jsonl", 'r', encoding='utf-8') as f:
            existing_lines = [json.loads(line) for line in f]
        
        # 重新生成
        new_manifest = build_index(args.mathlib4_path, args.output)
        
        # 读取新生成的产物
        with open(args.output / "theorems.jsonl", 'r', encoding='utf-8') as f:
            new_lines = [json.loads(line) for line in f]
        
        # 比对
        if existing_lines == new_lines:
            print("✅ 位级一致验证通过")
            exit(0)
        else:
            print("❌ 位级不一致！")
            exit(1)
    else:
        if args.commit_hash:
            manifest = build_index_with_commit(
                args.mathlib4_path,
                args.output,
                args.commit_hash
            )
        else:
            manifest = build_index(args.mathlib4_path, args.output)
        
        print(f"索引构建完成：{manifest['theorem_count']} 个定理")
        print(f"sha256: {manifest['sha256']}")
