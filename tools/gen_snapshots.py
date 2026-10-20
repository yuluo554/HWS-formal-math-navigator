"""预置模型输出快照生成器

口径（plan/03-基准套件设计.md §一）：
- 基准用**预置快照**，不依赖当场跑模型 —— 使指标可复跑
- 快照 = 骨架生成阶段的输入（Lean 声明骨架）+ 领域/难度元数据
- 遵循 K4（同输入同结果）：固定 GENERATION_DATE，确定性写盘，无时间戳

设计说明：本工具在**无模型**环境下生成快照——按确定性规则把命题形式化为
Lean 声明骨架（证明体统一为 `by sorry` 占位，即"待证明"的骨架形态）。
这正是"模型在环"关闭时骨架生成器的产出形态：骨架 + 占位，真值由内核判定。
快照内**不含**任何观测结论（编译结果由基准运行时实算，不在快照里预置答案）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# 固定生成日期，确保确定性写盘（K11）
GENERATION_DATE = "2026-01-01"
SNAPSHOT_VERSION = "1.0"


def _formalize(case_id: str, proposition: str) -> str:
    """按确定性规则把命题形式化为 Lean 声明骨架

    规则（零模型、可复现）：
      - 命题已是 Lean 声明（theorem/lemma/def/example 开头）→ 原样返回
      - 否则 → 包装为 theorem，证明体用 `by sorry` 占位（骨架语义）

    Args:
        case_id: 用例 id（用作定理名，保证唯一且确定性）
        proposition: 命题文本

    Returns:
        Lean 声明骨架代码
    """
    stripped = proposition.strip()
    if stripped.startswith(("theorem ", "lemma ", "def ", "example ")):
        return stripped
    safe_name = case_id.replace("-", "_")
    return f"theorem {safe_name} : {stripped} := by sorry"


def _sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_snapshot_bytes(cases: List[Dict[str, Any]]) -> tuple:
    """构造快照字节与 manifest（**纯函数，不写盘**）

    拆出来是为了让 `--check` 真只读：D5 实测 --check 曾先 `generate_snapshots()`
    真写盘再比对 → 验证命令把被验证的证据"治好"，篡改痕迹消失。
    """
    entries: List[Dict[str, Any]] = []
    for case in sorted(cases, key=lambda c: c.get("id", "")):
        entries.append({
            "id": case["id"],
            "domain": case.get("domain", "other"),
            "difficulty": case.get("difficulty", "medium"),
            "proposition": case["proposition"],
            "code": _formalize(case["id"], case["proposition"]),
        })

    # 确定性序列化：sort_keys + 固定缩进 + LF
    payload = json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True)
    snapshot_bytes = (payload + "\n").encode("utf-8")

    manifest = {
        "version": SNAPSHOT_VERSION,
        "generation_date": GENERATION_DATE,
        "generation_config": model_config_default(),
        "case_count": len(entries),
        "domains": sorted({e["domain"] for e in entries}),
        "sha256": _sha256_of(snapshot_bytes),
    }
    return snapshot_bytes, manifest


def model_config_default() -> Dict[str, Any]:
    """默认生成参数（规则模式，未启用模型）"""
    return {
        "mode": "rule_based",
        "model": None,
        "note": "模型未启用，骨架按确定性规则生成（证明体为 by sorry 占位）",
    }


def generate_snapshots(
    output_path: Path,
    cases: List[Dict[str, Any]],
    model_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """生成预置模型输出快照

    Args:
        output_path: 输出目录（如 data/snapshots/v1）
        cases: 用例列表（来自 tests/fixtures/skeleton_cases.json）
        model_config: 生成参数（记入 manifest；默认表示"规则模式，未启用模型"）

    Returns:
        快照 manifest
    """
    output_path.mkdir(parents=True, exist_ok=True)

    snapshot_bytes, manifest = _build_snapshot_bytes(cases)
    if model_config is not None:
        manifest["generation_config"] = model_config

    snapshot_file = output_path / "snapshots.json"
    with open(snapshot_file, "wb") as f:
        f.write(snapshot_bytes)

    manifest_payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    with open(output_path / "manifest.json", "wb") as f:
        f.write((manifest_payload + "\n").encode("utf-8"))

    return manifest


def compute_sha256(file_path: Path) -> str:
    """计算文件 sha256"""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="生成预置模型输出快照")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/snapshots/v1"),
        help="输出路径",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/skeleton_cases.json"),
        help="用例来源（骨架用例 fixtures）",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="验证已生成产物位级一致（不重新生成）",
    )
    args = parser.parse_args()

    if not args.cases.exists():
        print(f"错误：用例文件不存在：{args.cases}")
        return 1

    with open(args.cases, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if args.check:
        # **只读**：只算不写（D5：以前这里先写盘再比对，篡改痕迹被抹掉）
        snapshot_file = args.output / "snapshots.json"
        if not snapshot_file.exists():
            print("错误：--check 模式需要已存在的 snapshots.json")
            return 1

        before = snapshot_file.read_bytes()
        expected_bytes, manifest = _build_snapshot_bytes(cases)

        if before == expected_bytes:
            print("✅ 位级一致验证通过")
            print(f"sha256: {manifest['sha256']}")
            return 0
        print("❌ 位级不一致！（磁盘未被修改）")
        print(f"  现有 {len(before)} 字节 / 期望 {len(expected_bytes)} 字节")
        print(f"  现有 sha256: {_sha256_of(before)}")
        print(f"  期望 sha256: {manifest['sha256']}")
        return 1

    manifest = generate_snapshots(args.output, cases)
    print(f"快照生成完成：{manifest['case_count']} 个用例")
    print(f"领域：{manifest['domains']}")
    print(f"sha256: {manifest['sha256']}")
    return 0


if __name__ == "__main__":
    import sys
    from _encoding import ensure_utf8_stdio

    ensure_utf8_stdio()
    sys.exit(main())
