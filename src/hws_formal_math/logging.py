"""日志（UTF-8 守卫）"""

import logging
import sys


def _ensure_utf8_stdio():
    """确保 stdio 使用 UTF-8 编码"""
    for stream in (sys.stdout, sys.stderr):
        if stream.encoding != "utf-8":
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, OSError):
                pass


def setup_logging(level=logging.INFO):
    """配置日志"""
    _ensure_utf8_stdio()
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    return logging.getLogger("hws_formal_math")
