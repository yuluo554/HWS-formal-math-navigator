"""CLI 入口"""

import sys
import argparse
from pathlib import Path

from .config import Config
from .exceptions import ExitCode, HWSFormalMathError, IndexNotFoundError
from .logging import setup_logging
from .core import Orchestrator, ReportGenerator, ReportConfig

logger = setup_logging()


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
        default=Path("data/index"),
        help="索引目录路径（默认: data/index）"
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
    export_parser.add_argument("--output", "-o", type=Path, help="输出路径")

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
    """处理 generate 命令"""
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

        return ExitCode.SUCCESS if status == "PASS_NO_SORRY" else ExitCode.FAILURE
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return ExitCode.FAILURE


def handle_bench(args, config: Config) -> int:
    """处理 bench 命令"""
    logger.info(f"运行基准: {args.suite or 'all'}")
    # 基准测试通过 pytest 运行
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    if args.suite:
        # 映射套件到测试文件
        suite_map = {
            "retrieval": "test_retriever.py",
            "skeleton": "test_skeleton_gen.py",
            "depgraph": "test_depgraph.py",
        }
        cmd.append(f"tests/{suite_map[args.suite]}")

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


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

        return ExitCode.SUCCESS
    except Exception as e:
        logger.error(f"自检失败: {e}")
        return ExitCode.FAILURE


def handle_export(args, config: Config) -> int:
    """处理 export 命令"""
    logger.info(f"导出: {args.format}")
    try:
        output_path = args.output or Path(f"report.{args.format}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        orchestrator = Orchestrator(config)
        report_gen = ReportGenerator()

        # 使用示例命题生成报告
        result = orchestrator.run("加法结合律")
        report_gen.generate(result, output_path.parent)

        print(f"✅ 报告已生成: {output_path}")
        return ExitCode.SUCCESS
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main())
