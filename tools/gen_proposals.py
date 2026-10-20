"""合成命题生成器

生成形式化数学命题集，用于测试检索和骨架生成。

遵循 K4（同输入同结果）口径：固定 seed，确定性输出。
"""

import hashlib
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional


# 固定 seed 确保确定性（K4）
SEED = 42

# 固定生成日期，确保确定性写盘
GENERATION_DATE = "2026-01-01"


def _sha256_of(data: bytes) -> str:
    """字节级 sha256（D4：manifest 必须登记，否则 EOL 漂移无人发现）"""
    return hashlib.sha256(data).hexdigest()


def _serialize_proposals(proposals: List[Dict[str, Any]]) -> bytes:
    """确定性序列化提案集（与历史产物逐字节一致：indent=2 + 末尾无换行 + LF）

    显式 `newline="\\n"`：本机 core.autocrlf=true 时文本模式写盘会写 CRLF，
    与仓库里的 LF 版本字节不同（D4 实测 11,270 → 11,776 B）。
    """
    payload = json.dumps(proposals, indent=2, ensure_ascii=False)
    return payload.encode("utf-8")


def _build_proposals(num_cases: int) -> tuple:
    """按固定 seed 生成命题集（**纯函数，不写盘**）

    拆出来是为了让 `--check` 只读：D5 实测过同类缺陷（先写盘再比对 =
    验证命令把被验证的证据"治好"，篡改痕迹消失）。
    """
    random.seed(SEED)

    proposals = []

    # 按难度分布：简单 40%，中等 40%，困难 20%
    easy_count = int(num_cases * 0.4)
    medium_count = int(num_cases * 0.4)
    hard_count = num_cases - easy_count - medium_count

    for i in range(easy_count):
        proposals.append(generate_easy_proposition(i))

    for i in range(medium_count):
        proposals.append(generate_medium_proposition(easy_count + i))

    for i in range(hard_count):
        proposals.append(generate_hard_proposition(easy_count + medium_count + i))

    # 按 ID 排序（K4 确定性）
    proposals.sort(key=lambda p: p["id"])
    return proposals, easy_count, medium_count, hard_count


def _build_manifest(proposals, easy_count, medium_count, hard_count, proposals_bytes) -> Dict[str, Any]:
    """构造 manifest（含 sha256；纯函数，不写盘）"""
    return {
        "version": "1.0",
        "seed": SEED,
        "generation_date": GENERATION_DATE,
        "proposal_count": len(proposals),
        "difficulty_distribution": {
            "easy": easy_count,
            "medium": medium_count,
            "hard": hard_count
        },
        "domains": sorted(list(set(p["domain"] for p in proposals))),
        # D4：以前 proposals 的 manifest 没有 sha256 字段，所以 CRLF 漂移无人发现
        "sha256": _sha256_of(proposals_bytes),
    }


def generate_proposals(output_path: Path, num_cases: int = 50) -> Dict[str, Any]:
    """
    生成合成命题集
    
    Args:
        output_path: 输出路径
        num_cases: 用例数量
        
    Returns:
        命题 manifest
    """
    output_path.mkdir(parents=True, exist_ok=True)

    proposals, easy_count, medium_count, hard_count = _build_proposals(num_cases)

    # 写入命题文件（确定性字节：LF，不受 core.autocrlf 影响）
    proposals_file = output_path / "proposals.json"
    proposals_bytes = _serialize_proposals(proposals)
    proposals_file.write_bytes(proposals_bytes)

    manifest = _build_manifest(
        proposals, easy_count, medium_count, hard_count, proposals_bytes
    )

    manifest_file = output_path / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def generate_easy_proposition(index: int) -> Dict[str, Any]:
    """
    生成简单命题
    
    简单命题：单步推理，基础定理
    """
    random.seed(SEED + index)  # 确保确定性
    
    # 简单命题模板
    templates = [
        {
            "template": "证明 {a} + {b} = {b} + {a}",
            "domain": "algebra",
            "ground_truth": ["add_comm"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {a} + 0 = {a}",
            "domain": "algebra",
            "ground_truth": ["add_zero"],
            "difficulty": "easy"
        },
        {
            "template": "证明 0 + {a} = {a}",
            "domain": "algebra",
            "ground_truth": ["zero_add"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {a} * 1 = {a}",
            "domain": "algebra",
            "ground_truth": ["mul_one"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {a} * 0 = 0",
            "domain": "algebra",
            "ground_truth": ["mul_zero"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {n} ^ 0 = 1",
            "domain": "number_theory",
            "ground_truth": ["pow_zero"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {n} ^ 1 = {n}",
            "domain": "number_theory",
            "ground_truth": ["pow_one"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {n} + 0 = {n}",
            "domain": "number_theory",
            "ground_truth": ["add_zero"],
            "difficulty": "easy"
        },
        {
            "template": "证明 0 + {n} = {n}",
            "domain": "number_theory",
            "ground_truth": ["zero_add"],
            "difficulty": "easy"
        },
        {
            "template": "证明 {n} * 1 = {n}",
            "domain": "number_theory",
            "ground_truth": ["mul_one"],
            "difficulty": "easy"
        },
    ]
    
    # 选择模板
    template = templates[index % len(templates)]
    
    # 生成具体值
    a = random.randint(1, 100)
    b = random.randint(1, 100)
    n = random.randint(1, 50)
    
    # 填充模板
    statement = template["template"].format(a=a, b=b, n=n)
    
    return {
        "id": f"prop_easy_{index:04d}",
        "statement": statement,
        "domain": template["domain"],
        "difficulty": template["difficulty"],
        "ground_truth": template["ground_truth"],
        "generated_at": GENERATION_DATE
    }


def generate_medium_proposition(index: int) -> Dict[str, Any]:
    """
    生成中等命题
    
    中等命题：多步推理，需要组合定理
    """
    random.seed(SEED + index)  # 确保确定性
    
    # 中等命题模板
    templates = [
        {
            "template": "证明 {a} + {b} + {c} = {a} + ({b} + {c})",
            "domain": "algebra",
            "ground_truth": ["add_assoc"],
            "difficulty": "medium"
        },
        {
            "template": "证明 ({a} + {b}) + {c} = {a} + ({b} + {c})",
            "domain": "algebra",
            "ground_truth": ["add_assoc"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {a} * ({b} + {c}) = {a} * {b} + {a} * {c}",
            "domain": "algebra",
            "ground_truth": ["left_distrib"],
            "difficulty": "medium"
        },
        {
            "template": "证明 ({a} + {b}) * {c} = {a} * {c} + {b} * {c}",
            "domain": "algebra",
            "ground_truth": ["right_distrib"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {a} * {b} = {b} * {a}",
            "domain": "algebra",
            "ground_truth": ["mul_comm"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {a} * {b} * {c} = {a} * ({b} * {c})",
            "domain": "algebra",
            "ground_truth": ["mul_assoc"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {n} ^ {m} >= {n} 当 {n} >= 2 且 {m} >= 1",
            "domain": "number_theory",
            "ground_truth": ["pow_le_self"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {n} * {n} >= {n} 当 {n} >= 1",
            "domain": "number_theory",
            "ground_truth": ["mul_le_self"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {n} ^ 2 >= {n} 当 {n} >= 1",
            "domain": "number_theory",
            "ground_truth": ["pow_two_le_self"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {n} 选 0 = 1",
            "domain": "combinatorics",
            "ground_truth": ["choose_zero"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {n} 选 {n} = 1",
            "domain": "combinatorics",
            "ground_truth": ["choose_self"],
            "difficulty": "medium"
        },
        {
            "template": "证明 {n} 选 1 = {n}",
            "domain": "combinatorics",
            "ground_truth": ["choose_one"],
            "difficulty": "medium"
        },
    ]
    
    # 选择模板
    template = templates[index % len(templates)]
    
    # 生成具体值
    a = random.randint(1, 100)
    b = random.randint(1, 100)
    c = random.randint(1, 100)
    n = random.randint(2, 50)
    m = random.randint(1, 10)
    
    # 填充模板
    statement = template["template"].format(a=a, b=b, c=c, n=n, m=m)
    
    return {
        "id": f"prop_medium_{index:04d}",
        "statement": statement,
        "domain": template["domain"],
        "difficulty": template["difficulty"],
        "ground_truth": template["ground_truth"],
        "generated_at": GENERATION_DATE
    }


def generate_hard_proposition(index: int) -> Dict[str, Any]:
    """
    生成困难命题
    
    困难命题：需要多步推理和组合多个定理
    """
    random.seed(SEED + index)  # 确保确定性
    
    # 困难命题模板
    templates = [
        {
            "template": "证明 {a} + {b} = {b} + {a} 且 {a} + 0 = {a}",
            "domain": "algebra",
            "ground_truth": ["add_comm", "add_zero"],
            "difficulty": "hard"
        },
        {
            "template": "证明 ({a} + {b}) + {c} = {a} + ({b} + {c}) 且 {a} + {b} = {b} + {a}",
            "domain": "algebra",
            "ground_truth": ["add_assoc", "add_comm"],
            "difficulty": "hard"
        },
        {
            "template": "证明 {a} * ({b} + {c}) = {a} * {b} + {a} * {c} 且 {a} * {b} = {b} * {a}",
            "domain": "algebra",
            "ground_truth": ["left_distrib", "mul_comm"],
            "difficulty": "hard"
        },
        {
            "template": "证明 {n} ^ ({m} + {k}) = {n} ^ {m} * {n} ^ {k}",
            "domain": "number_theory",
            "ground_truth": ["pow_succ"],
            "difficulty": "hard"
        },
        {
            "template": "证明 {n} 选 {k} + {n} 选 {k}plus1 = {n}plus1 选 {k}plus1",
            "domain": "combinatorics",
            "ground_truth": ["choose_succ_succ"],
            "difficulty": "hard"
        },
        {
            "template": "证明 {n} 选 {k} > 0 当 0 <= {k} <= {n}",
            "domain": "combinatorics",
            "ground_truth": ["factorial_pos"],
            "difficulty": "hard"
        },
    ]
    
    # 选择模板
    template = templates[index % len(templates)]
    
    # 生成具体值
    a = random.randint(1, 100)
    b = random.randint(1, 100)
    c = random.randint(1, 100)
    n = random.randint(2, 50)
    m = random.randint(1, 10)
    k = random.randint(0, 10)
    n_plus_1 = n + 1
    k_plus_1 = k + 1
    
    # 填充模板
    statement = template["template"].format(
        a=a, b=b, c=c, n=n, m=m, k=k,
        n_plus_1=n_plus_1, k_plus_1=k_plus_1
    )
    
    return {
        "id": f"prop_hard_{index:04d}",
        "statement": statement,
        "domain": template["domain"],
        "difficulty": template["difficulty"],
        "ground_truth": template["ground_truth"],
        "generated_at": GENERATION_DATE
    }


if __name__ == "__main__":
    import argparse
    from _encoding import ensure_utf8_stdio

    ensure_utf8_stdio()

    parser = argparse.ArgumentParser(description="生成合成命题集")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/proposals/v1"),
        help="输出路径"
    )
    parser.add_argument(
        "--num-cases",
        type=int,
        default=50,
        help="用例数量"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="验证已生成产物位级一致（不重新生成）"
    )
    
    args = parser.parse_args()

    if args.check:
        # 只读校验（D5 同类缺陷：以前这里先生成写盘再比对，篡改痕迹会被"治好"）
        existing_file = args.output / "proposals.json"
        if not existing_file.exists():
            print("错误：--check 模式需要已存在的 proposals.json")
            exit(1)

        proposals, easy_count, medium_count, hard_count = _build_proposals(args.num_cases)
        expected_bytes = _serialize_proposals(proposals)
        existing_bytes = existing_file.read_bytes()

        if existing_bytes == expected_bytes:
            expected_manifest = _build_manifest(
                proposals, easy_count, medium_count, hard_count, expected_bytes
            )
            print("✅ 位级一致验证通过")
            print(f"sha256: {expected_manifest['sha256']}")
            exit(0)

        print("❌ 位级不一致！（磁盘未被修改）")
        print(f"  现有 {len(existing_bytes)} 字节 / 期望 {len(expected_bytes)} 字节")
        exit(1)
    else:
        manifest = generate_proposals(args.output, args.num_cases)
        
        print(f"命题生成完成：{manifest['proposal_count']} 个命题")
        print(f"难度分布：{manifest['difficulty_distribution']}")
        print(f"领域：{manifest['domains']}")
