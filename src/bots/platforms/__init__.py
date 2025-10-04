"""
平台机器人模块

包含针对不同平台的机器人实现
"""

# 延迟导入避免依赖问题
__all__ = ['CantStopLagrangeBot', 'QQBot']

def get_lagrange_bot():
    """获取Lagrange机器人类"""
    from .lagrange_bot import CantStopLagrangeBot
    return CantStopLagrangeBot

def get_qq_bot():
    """获取QQ机器人类"""
    from .qq_bot import QQBot
    return QQBot