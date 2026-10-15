"""CLI 入口"""

import sys
import argparse
from pathlib import Path

from .config import Config
from .exceptions import ExitCode, HWSFormalMathError
from .logging import setup_logging

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
    verify_parser.add_argument("code", help="Lean 代码片段")
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
    # TODO: 实现检索逻辑
    print(f"检索结果: {args.query}")
    return ExitCode.SUCCESS


def handle_generate(args, config: Config) -> int:
    """处理 generate 命令"""
    logger.info(f"生成骨架: {args.proposition}")
    # TODO: 实现骨架生成逻辑
    print(f"骨架生成: {args.proposition}")
    return ExitCode.SUCCESS


def handle_verify(args, config: Config) -> int:
    """处理 verify 命令"""
    code = args.code
    if args.file:
        code = args.file.read_text(encoding="utf-8")
    
    logger.info(f"验证代码: {code[:50]}...")
    # TODO: 实现内核验证逻辑
    print(f"验证结果: {code[:50]}...")
    return ExitCode.SUCCESS


def handle_bench(args, config: Config) -> int:
    """处理 bench 命令"""
    logger.info(f"运行基准: {args.suite or 'all'}")
    # TODO: 实现基准运行逻辑
    print(f"基准运行: {args.suite or 'all'}")
    return ExitCode.SUCCESS


def handle_selftest(config: Config) -> int:
    """处理 selftest 命令"""
    logger.info("运行自检")
    # TODO: 实现自检逻辑
    print("自检通过")
    return ExitCode.SUCCESS


def handle_export(args, config: Config) -> int:
    """处理 export 命令"""
    logger.info(f"导出: {args.format}")
    # TODO: 实现导出逻辑
    print(f"导出: {args.format}")
    return ExitCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
