"""
消息适配器模块

处理不同平台的消息格式转换和适配
"""

from .qq_message_adapter import QQMessageAdapter, MessageStyle

__all__ = ['QQMessageAdapter', 'MessageStyle']