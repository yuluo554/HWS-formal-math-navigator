"""合成命题生成器

生成形式化数学命题集，用于测试检索和骨架生成。

遵循 K4（同输入同结果）口径：固定 seed，确定性输出。
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional


# 固定 seed 确保确定性（K4）
SEED = 42

# 固定生成日期，确保确定性写盘
GENERATION_DATE = "2026-01-01"


def generate_proposals(output_path: Path, num_cases: int = 50) -> Dict[str, Any]:
    """
    生成合成命题集
    
    Args:
        output_path: 输出路径
        num_cases: 用例数量
        
    Returns:
        命题 manifest
    """
    random.seed(SEED)
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 生成命题
    proposals = []
    
    # 按难度分布：简单 40%，中等 40%，困难 20%
    easy_count = int(num_cases * 0.4)
    medium_count = int(num_cases * 0.4)
    hard_count = num_cases - easy_count - medium_count
    
    # 生成简单命题
    for i in range(easy_count):
        proposal = generate_easy_proposition(i)
        proposals.append(proposal)
    
    # 生成中等命题
    for i in range(medium_count):
        proposal = generate_medium_proposition(easy_count + i)
        proposals.append(proposal)
    
    # 生成困难命题
    for i in range(hard_count):
        proposal = generate_hard_proposition(easy_count + medium_count + i)
        proposals.append(proposal)
    
    # 按 ID 排序（K4 确定性）
    proposals.sort(key=lambda p: p["id"])
    
    # 写入命题文件
    proposals_file = output_path / "proposals.json"
    with open(proposals_file, 'w', encoding='utf-8') as f:
        json.dump(proposals, f, indent=2, ensure_ascii=False)
    
    # 生成 manifest
    manifest = {
        "version": "1.0",
        "seed": SEED,
        "generation_date": GENERATION_DATE,
        "proposal_count": len(proposals),
        "difficulty_distribution": {
            "easy": easy_count,
            "medium": medium_count,
            "hard": hard_count
        },
        "domains": sorted(list(set(p["domain"] for p in proposals)))
    }
    
    manifest_file = output_path / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
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
        # 验证模式：重新生成并比对
        if not (args.output / "proposals.json").exists():
            print("错误：--check 模式需要已存在的 proposals.json")
            exit(1)
        
        # 读取现有产物
        with open(args.output / "proposals.json", 'r', encoding='utf-8') as f:
            existing_proposals = json.load(f)
        
        # 重新生成
        new_manifest = generate_proposals(args.output, args.num_cases)
        
        # 读取新生成的产物
        with open(args.output / "proposals.json", 'r', encoding='utf-8') as f:
            new_proposals = json.load(f)
        
        # 比对（排除 generated_at 字段）
        existing_clean = [
            {k: v for k, v in p.items() if k != "generated_at"}
            for p in existing_proposals
        ]
        new_clean = [
            {k: v for k, v in p.items() if k != "generated_at"}
            for p in new_proposals
        ]
        
        if existing_clean == new_clean:
            print("✅ 位级一致验证通过")
            exit(0)
        else:
            print("❌ 位级不一致！")
            exit(1)
    else:
        manifest = generate_proposals(args.output, args.num_cases)
        
        print(f"命题生成完成：{manifest['proposal_count']} 个命题")
        print(f"难度分布：{manifest['difficulty_distribution']}")
        print(f"领域：{manifest['domains']}")
