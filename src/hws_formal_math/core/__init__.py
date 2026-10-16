"""核心层初始化（惰性导入，避免 core ↔ engine 导入环）

架构口径（plan/06 §一）：分层单向依赖 展示层 → 编排层 → 引擎层。
但 `engine/skeleton_gen.py` 需要 `core.model_gateway`（模型网关），
若本文件在导入期就急切加载 orchestrator（而 orchestrator 又 import engine），
则 `import hws_formal_math.engine.<x>` 这类独立导入会因"部分初始化的 engine 包"而失败
（ImportError: cannot import name 'SkeletonGenerator' from partially initialized module）。
故此处用 PEP 562 惰性属性，对外 API 保持不变。
"""

__all__ = [
    "Orchestrator",
    "OrchestrationResult",
    "ReportGenerator",
    "ReportConfig",
]


def __getattr__(name):
    if name in ("Orchestrator", "OrchestrationResult"):
        from .orchestrator import Orchestrator, OrchestrationResult
        return {
            "Orchestrator": Orchestrator,
            "OrchestrationResult": OrchestrationResult,
        }[name]
    if name in ("ReportGenerator", "ReportConfig"):
        from .report import ReportGenerator, ReportConfig
        return {
            "ReportGenerator": ReportGenerator,
            "ReportConfig": ReportConfig,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
