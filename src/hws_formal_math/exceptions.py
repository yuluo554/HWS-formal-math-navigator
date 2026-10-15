"""异常体系（退出码语义）"""

from enum import IntEnum


class ExitCode(IntEnum):
    """退出码语义"""
    SUCCESS = 0
    FAILURE = 1  # 检查未通过
    USAGE_ERROR = 2  # 参数错误
    DEPENDENCY_MISSING = 3  # 依赖缺失
    CONFIG_ERROR = 4  # 配置错误


class HWSFormalMathError(Exception):
    """基础异常"""
    pass


class ModelDisabledError(HWSFormalMathError):
    """模型已关闭"""
    pass


class ModelConfigError(HWSFormalMathError):
    """模型配置错误"""
    pass


class LeanNotAvailableError(HWSFormalMathError):
    """Lean 工具链不可用"""
    pass


class IndexNotFoundError(HWSFormalMathError):
    """索引未找到"""
    pass


class SyntaxError(HWSFormalMathError):
    """语法校验失败"""
    pass
