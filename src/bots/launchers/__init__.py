"""
启动器模块

负责机器人的配置管理和启动
"""

from .config_manager import ConfigManager, BotConfig

# 延迟导入避免依赖问题
def get_bot_launcher():
    """获取机器人启动器"""
    from .bot_launcher import BotLauncher
    return BotLauncher

def get_unified_launcher():
    """获取统一启动器"""
    from .unified_launcher import UnifiedLauncher
    return UnifiedLauncher

__all__ = ['ConfigManager', 'BotConfig', 'get_bot_launcher', 'get_unified_launcher']