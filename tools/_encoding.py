"""工具脚本的 UTF-8 编码守卫

背景（本机环境坑）：Windows 控制台默认 cp936/cp1252，脚本 `print` 中文会
`UnicodeEncodeError`。CI 管道亦可能为 cp1252。本项目主 CLI 的守卫在
`src/hws_formal_math/logging.py:_ensure_utf8_stdio()`；tools/ 下的独立脚本
（不经主 CLI 入口）需要各自守卫——"编码守卫要覆盖所有会打印的可执行入口"。

按 `stream.encoding` 探针决定是否 reconfigure（中文控制台 cp936 保持不动）。
"""

from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    """确保 stdio 使用 UTF-8 编码（幂等）"""
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", None)
        if encoding is None:
            continue
        if encoding.lower().replace("-", "") != "utf8":
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, OSError):
                pass
