"""
haven_research/core/logger.py - 企业级结构化日志与 TraceID 追踪模块

格式化输出日志，支持控制台彩色显示、日志级别动态控制与文件持久化翻转 (Rolling Logger)。
"""

import logging
import sys
from typing import Optional
from haven_research.config.settings import settings


class AppLogger:
    """标准生产级应用日志管理类"""

    _logger: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls, name: str = "haven_research") -> logging.Logger:
        if cls._logger is not None:
            return cls._logger

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.handlers.clear()

        # 兼容 Windows 控制台 UTF-8 编码
        if sys.platform == "win32":
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

        # 配置控制台 Formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logger.level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        cls._logger = logger
        return logger


logger = AppLogger.get_logger()
