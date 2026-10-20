"""CLI 入口"""

import json
import shutil
import sys
import argparse
import tempfile
from pathlib import Path
from typing import Optional

from . import __version__
from .config import Config, default_fixtures_dir
from .exceptions import (
    ExitCode,
    HWSFormalMathError,
    IndexNotFoundError,
    ModelDisabledError,
    ModelConfigError,
)
from .logging import setup_logging
from .core import Orchestrator, ReportGenerator, ReportConfig

logger = setup_logging()

# export 未指定 --proposition 时使用的示例命题（D9：以前是写死的隐式行为）
EXAMPLE_PROPOSITION = "加法结合律"


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="hws-formal-math",
        description="形式化数学库导航与证明骨架生成器"
    )

    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="配置文件路径"
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=None,
        help="索引目录路径（默认: 随包 data/index）"
    )
    # D7c：README/常识都期望有 --version（此前 unrecognized arguments exit 2）
    parser.add_argument(
        "--version",
        action="version",
        version=f"hws-formal-math {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # search 命令
    search_parser = subparsers.add_parser("search", help="检索定理")
    search_parser.add_argument("query", help="查询关键词")
    search_parser.add_argument("--top-k", "-k", type=int, default=10, help="返回结果数")

    # generate 命令
    generate_parser = subparsers.add_parser("generate", help="生成证明骨架")
    generate_parser.add_argument("proposition", help="数学命题")
    generate_parser.add_argument("--no-model", action="store_true", help="关闭模型生成")

    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="验证 Lean 代码")
    verify_parser.add_argument("code", nargs="?", help="Lean 代码片段")
    verify_parser.add_argument("--file", "-f", type=Path, help="从文件读取代码")

    # bench 命令
    bench_parser = subparsers.add_parser("bench", help="运行基准测试")
    bench_parser.add_argument("--suite", choices=["retrieval", "skeleton", "depgraph"], help="指定套件")
    bench_parser.add_argument("--report", action="store_true", help="生成报告")

    # selftest 命令
    subparsers.add_parser("selftest", help="自检")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出产物")
    export_parser.add_argument("--format", choices=["html", "json"], default="html")
    export_parser.add_argument("--output", "-o", type=Path, help="输出文件路径")
    export_parser.add_argument(
        "--proposition", "-p",
        default=None,
        help="要导出报告的命题（默认：内置示例命题「加法结合律」）"
    )

    return parser


def main(argv=None) -> int:
    """CLI 主入口"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return ExitCode.USAGE_ERROR

    try:
        # 加载配置
        config = Config.load(args.config)
        if args.index_path:
            config.index_path = args.index_path

        # 路由到对应命令
        if args.command == "search":
            return handle_search(args, config)
        elif args.command == "generate":
            return handle_generate(args, config)
        elif args.command == "verify":
            return handle_verify(args, config)
        elif args.command == "bench":
            return handle_bench(args, config)
        elif args.command == "selftest":
            return handle_selftest(config)
        elif args.command == "export":
            return handle_export(args, config)
        else:
            parser.print_help()
            return ExitCode.USAGE_ERROR

    except ModelConfigError as e:
        # D7a：README 的退出码表写了 4=配置错误，但此前 CONFIG_ERROR 只有定义、无任何 return。
        # 模型端点缺失/配置非法是唯一明确的"配置错误"来源（见 ModelGateway.generate_skeleton）。
        logger.error(f"配置错误: {e}")
        return ExitCode.CONFIG_ERROR
    except IndexNotFoundError as e:
        logger.error(f"索引未找到: {e}")
        return ExitCode.FAILURE
    except HWSFormalMathError as e:
        logger.error(f"错误: {e}")
        return ExitCode.FAILURE
    except KeyboardInterrupt:
        logger.info("被用户中断")
        return ExitCode.SUCCESS
    except Exception as e:
        logger.exception(f"未预期错误: {e}")
        return ExitCode.FAILURE


def handle_search(args, config: Config) -> int:
    """处理 search 命令"""
    logger.info(f"检索: {args.query}")
    try:
        orchestrator = Orchestrator(config)
        results = orchestrator.search(args.query, top_k=args.top_k)

        if not results:
            print(f"未找到与 '{args.query}' 相关的定理")
            return ExitCode.FAILURE

        print(f"找到 {len(results)} 个结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['theorem']} ({r['module']}) - 分数: {r['score']:.4f}")
            print(f"     签名: {r['signature']}")

        return ExitCode.SUCCESS
    except Exception as e:
        logger.error(f"检索失败: {e}")
        return ExitCode.FAILURE


def handle_generate(args, config: Config) -> int:
    """处理 generate 命令

    退出码语义（plan/04-测试与验收.md §2.2）：
      0 = 骨架生成成功；1 = 生成失败；2 = 参数错误；3 = 模型未配置
    """
    logger.info(f"生成骨架: {args.proposition}")
    try:
        orchestrator = Orchestrator(config)
        skeleton = orchestrator.generate_skeleton(
            args.proposition,
            use_model=not args.no_model
        )

        print("=== 证明骨架 ===")
        print(skeleton)
        return ExitCode.SUCCESS
    except ModelConfigError:
        # 配置类错误向外冒泡 → main() 统一映射到退出码 4（D7a）
        raise
    except ModelDisabledError as e:
        logger.error(f"骨架生成失败: {e}")
        return ExitCode.DEPENDENCY_MISSING
    except NotImplementedError as e:
        logger.error(f"骨架生成失败: {e}（模型端点尚未实现，见 README「模型端点」披露）")
        return ExitCode.FAILURE
    except Exception as e:
        logger.error(f"骨架生成失败: {e}")
        return ExitCode.FAILURE


def handle_verify(args, config: Config) -> int:
    """处理 verify 命令"""
    code = args.code
    if args.file:
        code = args.file.read_text(encoding="utf-8")

    if not code:
        logger.error("未提供代码")
        return ExitCode.USAGE_ERROR

    logger.info(f"验证代码: {code[:50]}...")
    try:
        orchestrator = Orchestrator(config)
        result = orchestrator.verify(code)

        status = result["status"]
        print(f"状态: {status}")
        if result["has_sorry"]:
            print(f"sorry 数量: {result['sorry_count']}")
        if result["errors"]:
            print("错误:")
            for e in result["errors"]:
                print(f"  - {e}")
        if result["warnings"]:
            print("警告:")
            for w in result["warnings"]:
                print(f"  - {w}")

        # 退出码语义（plan/04-测试与验收.md §2.2）：
        #   0 = 验证通过（PASS_NO_SORRY）
        #   1 = 验证失败（FAIL / 含 sorry 未证明）
        #   3 = 依赖缺失（Lean 未安装 → SKIPPED，非"验证失败"）
        if status == "PASS_NO_SORRY":
            return ExitCode.SUCCESS
        if status == "SKIPPED":
            return ExitCode.DEPENDENCY_MISSING
        return ExitCode.FAILURE
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return ExitCode.FAILURE


def handle_bench(args, config: Config) -> int:
    """处理 bench 命令

    退出码语义（plan/04-测试与验收.md §二）：
      0 = 基准达标；1 = 基准未达标；2 = 用法错误（套件名/用例文件缺失）
    """
    from . import benchmark

    fixtures_dir = _find_fixtures_dir()
    if fixtures_dir is None:
        logger.error("未找到基准用例目录 tests/fixtures（请从仓库根运行）")
        return ExitCode.USAGE_ERROR

    suites = [args.suite] if args.suite else None
    logger.info(f"运行基准: {args.suite or 'all'}")

    try:
        results = benchmark.run_all(
            fixtures_dir, config.index_path, config=config, suites=suites
        )
    except benchmark.BenchError as e:
        logger.error(f"基准运行失败: {e}")
        return ExitCode.USAGE_ERROR

    selected = suites or list(benchmark.ALL_SUITES)
    for name in selected:
        _print_suite_result(results[name])

    _print_coverage(results.get("coverage"))

    if args.report:
        report_path = Path("bench-report.json")
        with open(report_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        print(f"报告已写入: {report_path}")

    return ExitCode.SUCCESS if results["all_passed"] else ExitCode.FAILURE


def _find_fixtures_dir() -> Optional[Path]:
    """定位基准用例目录（源码态在仓库根，冻结态在 exe 同级，装态在 share/）

    D1 实测：pip 装完 bench --suite retrieval 报"未找到基准用例目录 tests/fixtures"
    exit 2 —— 因为候选里只有仓库布局。装态回落见 config.default_fixtures_dir()。
    """
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures",
        Path(getattr(sys, "_MEIPASS", Path.cwd())) / "tests" / "fixtures",
        Path.cwd() / "tests" / "fixtures",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return default_fixtures_dir()


def _print_suite_result(result: dict) -> None:
    """打印单个套件结果"""
    suite = result["suite"]

    if result.get("not_enabled", False):
        reason = result.get("not_enabled_reason", "unknown")
        print(f"[{suite}] 未启用（{reason}）")
        print(f"  {result.get('notes', '')}")
        return

    status = "达标" if result["passed"] else "未达标"
    print(f"[{suite}] {status}")

    if suite == "retrieval":
        print(f"  用例数: {result['total_cases']}")
        print(f"  Recall@10: {result['recall_at_10']} (阈值 {result['thresholds']['recall_at_10_min']})")
        print(f"  MRR: {result['mrr']} (阈值 {result['thresholds']['mrr_min']})")
    elif suite == "skeleton":
        print(f"  用例数: {result['total_cases']}")
        print(f"  PASS_NO_SORRY: {result['pass_no_sorry_rate']} (阈值 {result['thresholds']['pass_no_sorry_min']})")
        print(f"  PASS_WITH_SORRY: {result['pass_with_sorry_rate']} (阈值 {result['thresholds']['pass_with_sorry_min']})")
    elif suite == "depgraph":
        print(f"  用例数: {result['total_cases']}")
        print(f"  完整率: {result['completeness']} (阈值 {result['thresholds']['completeness_min']})")
        print(f"  断链检出率: {result['broken_ref_detection_rate']}")
        print(f"  index_gap 区分率: {result['index_gap_discrimination_rate']}")



def _verify_data_manifests(data_dir: Path) -> list:
    """数据自证：校验 manifest 登记的 sha256 ↔ 磁盘实算（D4）

    返回不一致项的描述列表（空列表 = 通过）。只校验**登记了** sha256 的条目；
    缺登记不算失败（严格模式在 tools/check_data_integrity.py --strict）。
    """
    import hashlib

    checks = (
        ("index/manifest.json", "index/theorems.jsonl"),
        ("snapshots/manifest.json", "snapshots/v1/snapshots.json"),
        ("snapshots/v1/manifest.json", "snapshots/v1/snapshots.json"),
        ("proposals/v1/manifest.json", "proposals/v1/proposals.json"),
    )
    drift = []
    for manifest_rel, target_rel in checks:
        manifest_path = data_dir / manifest_rel
        target_path = data_dir / target_rel
        if not manifest_path.is_file() or not target_path.is_file():
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                expected = json.load(f).get("sha256")
        except (OSError, ValueError):
            continue
        if not expected:
            continue
        actual = hashlib.sha256(target_path.read_bytes()).hexdigest()
        if expected != actual:
            drift.append(f"{target_rel}（期望 {expected[:16]}… 实际 {actual[:16]}…）")
    return drift


def _print_coverage(coverage: Optional[dict]) -> None:
    """打印领域覆盖度（D8）

    以前 compute_domain_coverage 的结果只进 `--report` 的 JSON，人读输出里完全看不到，
    于是 analysis 4/5、number_theory 0/5 判 insufficient 也没人知道。

    口径：**只打印，不改判**。原因是随包索引是 35 条 curated-sample，
    两条 insufficient 的根因是"领域分类靠 `domain in module`，而随包模块名是
    Mathlib.Data.*" —— 把它接进 all_passed 会让基准恒红，把它静默降级成 verified
    则是开后门。所以：如实打印，门禁判定权交给用户/后续批次（见 plan/RELEASE-M8.md）。
    """
    if not coverage:
        return

    domains = coverage.get("domains", {})
    if not domains:
        return

    print("[coverage] 领域覆盖度（最低项 vs 索引实际，**不参与 all_passed 判定**）")
    for name, item in sorted(domains.items()):
        status = item.get("status", "?")
        mark = "✅" if status == "verified" else "⚠️ "
        print(f"  {mark} {name}: {item.get('actual', 0)}/{item.get('min_theorems', 0)}（{status}）")

    if not coverage.get("all_verified", False):
        insufficient = [
            n for n, i in sorted(domains.items()) if i.get("status") != "verified"
        ]
        print(f"  → 未达标领域: {', '.join(insufficient)}"
              f"（随包索引为 curated-sample 35 条，非全量；覆盖度不代表 mathlib4 全库）")


def handle_selftest(config: Config) -> int:
    """处理 selftest 命令"""
    logger.info("运行自检")
    try:
        # 检查索引是否存在
        if not config.index_path.exists():
            logger.error(f"索引目录不存在: {config.index_path}")
            return ExitCode.FAILURE

        index_file = config.index_path / "theorems.jsonl"
        if not index_file.exists():
            logger.error(f"索引文件不存在: {index_file}")
            return ExitCode.FAILURE

        # 检查索引是否可读
        with open(index_file, "r", encoding="utf-8") as f:
            count = sum(1 for line in f if line.strip())

        print(f"✅ 索引文件可读: {index_file}")
        print(f"✅ 索引条目数: {count}")

        # 数据自证（D4）：manifest 登记的 sha256 ↔ 磁盘实算。
        # 只校验"登记了的"，缺登记时告警不判失败 —— 缺登记本身是数据缺陷，
        # 但不该让 selftest 在旧数据树上变红（严格判定在 tools/check_data_integrity.py --strict）。
        drift = _verify_data_manifests(config.index_path.parent)
        if drift:
            for item in drift:
                logger.error(f"数据字节与 manifest 不一致: {item}")
            print("❌ 数据自证失败（manifest.sha256 与磁盘不符）")
            return ExitCode.FAILURE
        print("✅ 数据自证通过（manifest.sha256 与磁盘一致）")

        # 检查引擎模块
        orchestrator = Orchestrator(config)
        print(f"✅ 编排器初始化成功")

        # 检查 Lean 可用性
        if orchestrator.kernel.is_available():
            print(f"✅ Lean 工具链可用")
        else:
            print(f"⚠️ Lean 工具链不可用（内核验证将跳过）")

        # 检查模型配置
        if config.model.enabled:
            print(f"✅ 模型已启用: {config.model.model}")
        else:
            print(f"⚠️ 模型未启用（骨架生成将使用规则模式）")

        # 冻结态：断言数据目录落在产物内（"数据随包走"的产物级核验）
        from .config import is_frozen
        if is_frozen():
            data_root = Path(sys._MEIPASS).resolve()
            index_path = config.index_path.resolve()
            if index_path == data_root or index_path.is_relative_to(data_root):
                print(f"✅ 冻结态数据目录随包: {config.index_path}")
            else:
                print(f"❌ 冻结态数据目录不在产物内: {config.index_path}")
                return ExitCode.FAILURE

        return ExitCode.SUCCESS
    except Exception as e:
        logger.error(f"自检失败: {e}")
        return ExitCode.FAILURE


def handle_export(args, config: Config) -> int:
    """处理 export 命令

    D9：旧实现只用 `output_path.parent`，report.py 固定写 report.html/report.json
    → `-o out/custom.json` 打印"✅ 报告已生成: out\\custom.json"但 custom.json 不存在。
    现在 `-o` 决定**文件名**（按 --format 只产一份）；不给 `-o` 时仍产 report.<fmt>。
    """
    logger.info(f"导出: {args.format}")
    try:
        extension = ".json" if args.format == "json" else ".html"
        output_path = args.output or Path(f"report{extension}")
        if output_path.suffix.lower() != extension:
            # 显式给了 -o 但扩展名与 --format 不符 → 按 --format 纠正并如实提示
            output_path = output_path.with_suffix(extension)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        orchestrator = Orchestrator(config)
        report_config = ReportConfig(
            human_readable=(args.format == "html"),
            machine_readable=(args.format == "json"),
        )
        report_gen = ReportGenerator(report_config)

        proposition = getattr(args, "proposition", None)
        if proposition:
            result = orchestrator.run(proposition)
        else:
            print("（未指定 --proposition，使用内置示例命题「加法结合律」）")
            result = orchestrator.run(EXAMPLE_PROPOSITION)

        # 先生成到临时目录，再改名到 -o 指定的文件名
        with tempfile.TemporaryDirectory() as tmpdir:
            generated = report_gen.generate(result, Path(tmpdir))
            produced = generated.get("html") or generated.get("json")
            if produced is None:
                logger.error("报告生成器未产出任何文件")
                return ExitCode.FAILURE
            shutil.move(str(produced), str(output_path))

        print(f"✅ 报告已生成: {output_path}")
        return ExitCode.SUCCESS
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main())
