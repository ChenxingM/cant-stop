"""
日志管理系统
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import traceback
from datetime import datetime

from .config import get_config


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # 颜色定义
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }

    def format(self, record):
        # 添加颜色
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


class GameLogFilter(logging.Filter):
    """游戏日志过滤器"""

    def __init__(self, game_events_only: bool = False):
        super().__init__()
        self.game_events_only = game_events_only

    def filter(self, record):
        # 只记录游戏相关事件
        if self.game_events_only:
            return hasattr(record, 'game_event') and record.game_event
        return True


class LogManager:
    """日志管理器"""

    def __init__(self):
        self.config = get_config().logging
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        # 确保日志目录存在
        log_file = self.config.file
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper(), logging.INFO))

        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 文件处理器
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self._parse_size(self.config.max_size),
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(self.config.format))
            file_handler.addFilter(GameLogFilter())
            root_logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        if sys.stdout.isatty():  # 只在终端中使用彩色输出
            console_handler.setFormatter(ColoredFormatter(self.config.format))
        else:
            console_handler.setFormatter(logging.Formatter(self.config.format))
        root_logger.addHandler(console_handler)

        # 设置特定模块的日志级别
        for module_name, level in self.config.loggers.items():
            module_logger = logging.getLogger(module_name)
            module_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]

    def log_game_event(self, logger_name: str, level: str, message: str,
                      player_id: Optional[str] = None, session_id: Optional[str] = None,
                      extra_data: Optional[Dict[str, Any]] = None):
        """记录游戏事件"""
        logger = self.get_logger(logger_name)
        log_level = getattr(logging, level.upper(), logging.INFO)

        # 创建日志记录
        record = logging.LogRecord(
            name=logger_name,
            level=log_level,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )

        # 添加游戏相关信息
        record.game_event = True
        record.player_id = player_id
        record.session_id = session_id
        record.timestamp = datetime.now()

        if extra_data:
            for key, value in extra_data.items():
                setattr(record, key, value)

        logger.handle(record)

    def log_error_with_context(self, logger_name: str, error: Exception,
                              context: Optional[Dict[str, Any]] = None):
        """记录带上下文的错误"""
        logger = self.get_logger(logger_name)

        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }

        logger.error(
            f"错误发生: {error_info['error_type']} - {error_info['error_message']}",
            extra=error_info
        )


# 全局日志管理器
_log_manager: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """获取全局日志管理器"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return get_log_manager().get_logger(name)


def log_game_event(message: str, level: str = "INFO", player_id: Optional[str] = None,
                   session_id: Optional[str] = None, **kwargs):
    """记录游戏事件的便捷函数"""
    get_log_manager().log_game_event(
        "game_events", level, message, player_id, session_id, kwargs
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """记录错误的便捷函数"""
    get_log_manager().log_error_with_context("errors", error, context)