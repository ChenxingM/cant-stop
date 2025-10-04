"""
CantStop 机器人模块

提供多平台机器人集成支持
"""

from .adapters.qq_message_adapter import QQMessageAdapter
from .launchers import ConfigManager, BotConfig

# 延迟导入机器人类避免依赖问题
def get_lagrange_bot():
    """获取Lagrange机器人类"""
    from .platforms.lagrange_bot import CantStopLagrangeBot
    return CantStopLagrangeBot

def get_qq_bot():
    """获取QQ机器人类"""
    from .platforms.qq_bot import QQBot
    return QQBot

__all__ = [
    'QQMessageAdapter',
    'ConfigManager',
    'BotConfig',
    'get_lagrange_bot',
    'get_qq_bot'
]