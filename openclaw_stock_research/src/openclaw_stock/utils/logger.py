"""
日志配置模块

提供统一的中文日志配置和格式化
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ChineseFormatter(logging.Formatter):
    """中文日志格式化器"""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # 添加时间戳
        record.asctime = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 确保消息为字符串
        if not isinstance(record.msg, str):
            record.msg = str(record.msg)

        return super().format(record)


class ColoredFormatter(ChineseFormatter):
    """带颜色的中文日志格式化器（用于控制台）"""

    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",      # 青色
        "INFO": "\033[32m",       # 绿色
        "WARNING": "\033[33m",    # 黄色
        "ERROR": "\033[31m",      # 红色
        "CRITICAL": "\033[35m",    # 紫色
        "RESET": "\033[0m",       # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        return super().format(record)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取配置好的日志记录器

    参数:
        name: 日志记录器名称，默认为"openclaw_stock"

    返回:
        配置好的Logger实例
    """
    logger = logging.getLogger(name or "openclaw_stock")

    # 如果已经有处理器，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    console_format = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 文件处理器（如果配置了日志路径）
    log_path = os.environ.get("LOG_PATH")
    if log_path:
        log_dir = Path(log_path)
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / f"openclaw_stock_{datetime.now():%Y%m%d}.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)

        # 文件日志不使用颜色
        file_format = ChineseFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# 延迟导入os模块（避免循环导入）
import os  # noqa: E402
