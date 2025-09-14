"""
配置管理系统
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///cant_stop.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class GameConfig:
    """游戏配置"""
    dice_cost: int = 10
    max_temporary_markers: int = 3
    win_condition_columns: int = 3
    score_rewards: Dict[str, int] = None
    items: Dict[str, Any] = None

    def __post_init__(self):
        if self.score_rewards is None:
            self.score_rewards = {
                "草图": 20,
                "精致小图": 80,
                "精草大图": 100,
                "精致大图": 150,
                "超常发挥": 30,
            }
        if self.items is None:
            self.items = {}


@dataclass
class BotConfig:
    """机器人配置"""
    name: str = "Can't Stop 贪骰无厌"
    admin_users: list = None
    allowed_groups: list = None
    response_delay: float = 0.5
    max_message_length: int = 2000
    enable_mentions: bool = True
    command_prefixes: list = None

    def __post_init__(self):
        if self.admin_users is None:
            self.admin_users = []
        if self.allowed_groups is None:
            self.allowed_groups = []
        if self.command_prefixes is None:
            self.command_prefixes = ["!", "/", ""]


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/cant_stop.log"
    max_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    loggers: Dict[str, str] = None

    def __post_init__(self):
        if self.loggers is None:
            self.loggers = {}


@dataclass
class SecurityConfig:
    """安全配置"""
    max_sessions_per_user: int = 3
    session_timeout_hours: int = 24
    rate_limiting: Dict[str, Any] = None
    backup: Dict[str, Any] = None

    def __post_init__(self):
        if self.rate_limiting is None:
            self.rate_limiting = {
                "enabled": True,
                "max_requests_per_minute": 30
            }
        if self.backup is None:
            self.backup = {
                "enabled": True,
                "interval_hours": 6,
                "max_backups": 10
            }


@dataclass
class PerformanceConfig:
    """性能配置"""
    cache: Dict[str, Any] = None
    database_cleanup: Dict[str, Any] = None

    def __post_init__(self):
        if self.cache is None:
            self.cache = {
                "enabled": True,
                "ttl_seconds": 300,
                "max_entries": 1000
            }
        if self.database_cleanup is None:
            self.database_cleanup = {
                "enabled": True,
                "cleanup_interval_hours": 24,
                "keep_completed_sessions_days": 7,
                "keep_failed_sessions_days": 3
            }


@dataclass
class DevelopmentConfig:
    """开发模式配置"""
    debug: bool = False
    mock_dice: bool = False
    test_mode: bool = False
    auto_checkin: bool = False


class Config:
    """主配置类"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config_data = self._load_config()

        # 初始化配置对象
        self.database = self._init_database_config()
        self.game = self._init_game_config()
        self.bot = self._init_bot_config()
        self.logging = self._init_logging_config()
        self.security = self._init_security_config()
        self.performance = self._init_performance_config()
        self.development = self._init_development_config()

    def _find_config_file(self) -> str:
        """查找配置文件"""
        # 查找顺序：当前目录 -> config目录 -> 默认配置
        possible_paths = [
            "config.yaml",
            "config/config.yaml",
            "config/default_config.yaml",
            os.path.join(os.path.dirname(__file__), "..", "..", "config", "default_config.yaml")
        ]

        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                logger.info(f"使用配置文件: {abs_path}")
                return abs_path

        # 如果没有找到配置文件，使用默认配置
        logger.warning("未找到配置文件，使用默认配置")
        return ""

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path or not os.path.exists(self.config_path):
            logger.warning("配置文件不存在，使用默认配置")
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                logger.info(f"成功加载配置文件: {self.config_path}")
                return config_data or {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _init_database_config(self) -> DatabaseConfig:
        """初始化数据库配置"""
        db_config = self.config_data.get('database', {})
        return DatabaseConfig(
            url=db_config.get('url', 'sqlite:///cant_stop.db'),
            echo=db_config.get('echo', False),
            pool_size=db_config.get('pool_size', 10),
            max_overflow=db_config.get('max_overflow', 20)
        )

    def _init_game_config(self) -> GameConfig:
        """初始化游戏配置"""
        game_config = self.config_data.get('game', {})
        return GameConfig(
            dice_cost=game_config.get('dice_cost', 10),
            max_temporary_markers=game_config.get('max_temporary_markers', 3),
            win_condition_columns=game_config.get('win_condition_columns', 3),
            score_rewards=game_config.get('score_rewards', {}),
            items=game_config.get('items', {})
        )

    def _init_bot_config(self) -> BotConfig:
        """初始化机器人配置"""
        bot_config = self.config_data.get('bot', {})
        return BotConfig(
            name=bot_config.get('name', 'Can\'t Stop 贪骰无厌'),
            admin_users=bot_config.get('admin_users', []),
            allowed_groups=bot_config.get('allowed_groups', []),
            response_delay=bot_config.get('response_delay', 0.5),
            max_message_length=bot_config.get('max_message_length', 2000),
            enable_mentions=bot_config.get('enable_mentions', True),
            command_prefixes=bot_config.get('command_prefixes', ["!", "/", ""])
        )

    def _init_logging_config(self) -> LoggingConfig:
        """初始化日志配置"""
        logging_config = self.config_data.get('logging', {})
        return LoggingConfig(
            level=logging_config.get('level', 'INFO'),
            file=logging_config.get('file', 'logs/cant_stop.log'),
            max_size=logging_config.get('max_size', '10MB'),
            backup_count=logging_config.get('backup_count', 5),
            format=logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            loggers=logging_config.get('loggers', {})
        )

    def _init_security_config(self) -> SecurityConfig:
        """初始化安全配置"""
        security_config = self.config_data.get('security', {})
        return SecurityConfig(
            max_sessions_per_user=security_config.get('max_sessions_per_user', 3),
            session_timeout_hours=security_config.get('session_timeout_hours', 24),
            rate_limiting=security_config.get('rate_limiting', {}),
            backup=security_config.get('backup', {})
        )

    def _init_performance_config(self) -> PerformanceConfig:
        """初始化性能配置"""
        performance_config = self.config_data.get('performance', {})
        return PerformanceConfig(
            cache=performance_config.get('cache', {}),
            database_cleanup=performance_config.get('database_cleanup', {})
        )

    def _init_development_config(self) -> DevelopmentConfig:
        """初始化开发配置"""
        dev_config = self.config_data.get('development', {})
        return DevelopmentConfig(
            debug=dev_config.get('debug', False),
            mock_dice=dev_config.get('mock_dice', False),
            test_mode=dev_config.get('test_mode', False),
            auto_checkin=dev_config.get('auto_checkin', False)
        )

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置值（运行时）"""
        keys = key.split('.')
        config = self.config_data

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None):
        """保存配置到文件"""
        save_path = path or self.config_path
        if not save_path:
            save_path = "config.yaml"

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def reload(self):
        """重新加载配置"""
        self.config_data = self._load_config()
        self.__init__(self.config_path)
        logger.info("配置已重新加载")


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reload_config():
    """重新加载全局配置"""
    global _config
    if _config:
        _config.reload()
    else:
        _config = Config()


# 便捷函数
def get_database_url() -> str:
    """获取数据库URL"""
    return get_config().database.url


def get_dice_cost() -> int:
    """获取掷骰消耗"""
    return get_config().game.dice_cost


def get_score_reward(reward_type: str) -> int:
    """获取积分奖励"""
    return get_config().game.score_rewards.get(reward_type, 0)


def is_debug_mode() -> bool:
    """是否调试模式"""
    return get_config().development.debug


def is_test_mode() -> bool:
    """是否测试模式"""
    return get_config().development.test_mode