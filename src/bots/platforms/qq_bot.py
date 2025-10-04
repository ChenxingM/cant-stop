"""
QQ机器人 - 基于Lagrange.OneBot的QQ群机器人
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from aiohttp import web

from ...services.game_service import GameService
from ...services.message_processor import MessageProcessor
from ...core.event_system import emit_game_event, GameEventType
from ..adapters.qq_message_adapter import QQMessageAdapter, MessageStyle


@dataclass
class QQUser:
    """QQ用户信息"""
    user_id: str
    nickname: str
    group_id: str = None
    is_admin: bool = False
    card: str = None  # 群名片


@dataclass
class QQMessage:
    """QQ消息数据"""
    message_id: int
    user_id: str
    group_id: str
    message: str
    message_type: str  # group, private
    sub_type: str
    time: int
    raw_message: str
    sender: Dict[str, Any]


class QQBot:
    """QQ机器人主类"""

    def __init__(self,
                 onebot_url: str = "http://127.0.0.1:8080",
                 listen_host: str = "127.0.0.1",
                 listen_port: int = 8080):
        self.onebot_url = onebot_url.rstrip('/')
        self.listen_host = listen_host
        self.listen_port = listen_port

        # 游戏相关服务
        self.game_service = GameService()
        self.message_processor = MessageProcessor()

        # 消息适配器
        self.message_adapter = QQMessageAdapter()

        # 用户会话管理
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.user_info: Dict[str, QQUser] = {}   # user_id -> QQUser

        # HTTP会话
        self.http_session: Optional[aiohttp.ClientSession] = None

        # 配置
        self.allowed_groups: List[str] = []  # 允许的群号列表，空表示允许所有
        self.admin_users: List[str] = []     # 管理员用户列表

        # 日志
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """启动机器人"""
        self.logger.info("启动QQ机器人...")

        # 创建HTTP会话
        self.http_session = aiohttp.ClientSession()

        # 创建Web服务器接收OneBot回调
        app = web.Application()
        app.router.add_post('/', self.handle_onebot_event)
        app.router.add_post('/onebot', self.handle_onebot_event)

        # 启动Web服务器
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.listen_host, self.listen_port)
        await site.start()

        self.logger.info(f"机器人已启动，监听 {self.listen_host}:{self.listen_port}")
        self.logger.info(f"OneBot地址: {self.onebot_url}")

    async def stop(self):
        """停止机器人"""
        if self.http_session:
            await self.http_session.close()
        self.logger.info("QQ机器人已停止")

    async def handle_onebot_event(self, request):
        """处理OneBot事件"""
        try:
            # 获取事件数据
            data = await request.json()

            # 记录接收到的事件
            self.logger.debug(f"收到OneBot事件: {data}")

            # 处理不同类型的事件
            post_type = data.get('post_type')

            if post_type == 'message':
                await self.handle_message_event(data)
            elif post_type == 'notice':
                await self.handle_notice_event(data)
            elif post_type == 'request':
                await self.handle_request_event(data)
            elif post_type == 'meta_event':
                await self.handle_meta_event(data)

            return web.Response(text='OK')

        except Exception as e:
            self.logger.error(f"处理OneBot事件失败: {e}")
            return web.Response(text='ERROR', status=500)

    async def handle_message_event(self, data: Dict):
        """处理消息事件"""
        try:
            # 解析消息数据
            message_data = QQMessage(
                message_id=data.get('message_id'),
                user_id=str(data.get('user_id')),
                group_id=str(data.get('group_id', '')),
                message=data.get('message', ''),
                message_type=data.get('message_type'),
                sub_type=data.get('sub_type', ''),
                time=data.get('time'),
                raw_message=data.get('raw_message', ''),
                sender=data.get('sender', {})
            )

            # 检查是否是允许的群
            if message_data.message_type == 'group':
                if self.allowed_groups and message_data.group_id not in self.allowed_groups:
                    return

            # 更新用户信息
            await self.update_user_info(message_data)

            # 处理游戏消息
            await self.process_game_message(message_data)

        except Exception as e:
            self.logger.error(f"处理消息事件失败: {e}")

    async def update_user_info(self, message_data: QQMessage):
        """更新用户信息"""
        user_id = message_data.user_id
        sender = message_data.sender

        # 创建或更新用户信息
        self.user_info[user_id] = QQUser(
            user_id=user_id,
            nickname=sender.get('nickname', ''),
            group_id=message_data.group_id,
            is_admin=user_id in self.admin_users,
            card=sender.get('card', '')
        )

    async def process_game_message(self, message_data: QQMessage):
        """处理游戏消息"""
        user_id = message_data.user_id
        message = message_data.message.strip()

        # 忽略空消息
        if not message:
            return

        # 获取用户信息
        user_info = self.user_info.get(user_id)
        if not user_info:
            return

        self.logger.info(f"用户 {user_info.nickname}({user_id}) 发送消息: {message}")

        try:
            # 确保用户在游戏系统中存在
            await self.ensure_player_exists(user_id, user_info.nickname)

            # 处理游戏指令
            success, response = await self.process_game_command(user_id, message)

            # 发送响应（只有当response不为None时才发送）
            if response:
                # 使用消息适配器格式化响应
                formatted_response = self.message_adapter.adapt_message(
                    response, user_id, "game"
                )
                await self.send_message(message_data, formatted_response)

            # 记录游戏事件
            emit_game_event(GameEventType.DICE_ROLLED if 'r6d6' in message else GameEventType.TURN_STARTED,
                          user_id, {"command": message, "success": success})

        except Exception as e:
            self.logger.error(f"处理游戏消息失败: {e}")
            error_msg = f"❌ 处理指令时发生错误: {str(e)}"
            await self.send_message(message_data, error_msg)

    async def ensure_player_exists(self, user_id: str, nickname: str):
        """确保玩家在游戏系统中存在"""
        player = self.game_service.db.get_player(user_id)
        if not player:
            # 自动注册新玩家
            success, message = self.game_service.register_player(user_id, nickname, "收养人")
            if not success:
                self.logger.warning(f"自动注册玩家失败: {message}")

    async def process_game_command(self, user_id: str, message: str) -> tuple[bool, str]:
        """处理游戏指令"""
        try:
            # 使用消息处理器处理指令
            success, response = self.message_processor.process_message(user_id, message)

            # 格式化响应消息
            if response:
                formatted_response = self.format_response_for_qq(response)
                return success, formatted_response
            else:
                return success, None

        except Exception as e:
            self.logger.error(f"处理游戏指令失败: {e}")
            return False, f"❌ 指令处理失败: {str(e)}"

    def format_response_for_qq(self, response: str) -> str:
        """格式化QQ消息响应"""
        # QQ群消息格式优化
        formatted = response

        # 替换一些特殊字符，确保在QQ中正确显示
        replacements = {
            '✅': '[✓]',
            '❌': '[✗]',
            '🎲': '[骰子]',
            '🎉': '[庆祝]',
            '⚠️': '[警告]',
        }

        for emoji, text in replacements.items():
            formatted = formatted.replace(emoji, text)

        # 限制消息长度，避免被QQ截断
        if len(formatted) > 1000:
            formatted = formatted[:997] + "..."

        return formatted

    async def send_message(self, original_message: QQMessage, content: str):
        """发送消息"""
        try:
            # 构建发送消息的API请求
            if original_message.message_type == 'group':
                # 在群消息中添加@用户
                at_user = f"[CQ:at,qq={original_message.user_id}] "
                message_with_at = at_user + content

                api_url = f"{self.onebot_url}/send_group_msg"
                params = {
                    "group_id": int(original_message.group_id),
                    "message": message_with_at
                }
            else:
                # 私聊消息不需要@
                api_url = f"{self.onebot_url}/send_private_msg"
                params = {
                    "user_id": int(original_message.user_id),
                    "message": content
                }

            # 发送HTTP请求
            async with self.http_session.post(api_url, json=params) as response:
                if response.status == 200:
                    self.logger.debug(f"消息发送成功: {content[:50]}...")
                else:
                    self.logger.error(f"消息发送失败: {response.status}")

        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")

    async def handle_notice_event(self, data: Dict):
        """处理通知事件（群员变动等）"""
        notice_type = data.get('notice_type')

        if notice_type == 'group_increase':
            # 新成员加群
            user_id = str(data.get('user_id'))
            group_id = str(data.get('group_id'))

            # 发送欢迎消息（包含@新成员）
            at_user = f"[CQ:at,qq={user_id}] "
            welcome_msg = f"{at_user}欢迎新成员！输入 'help' 查看CantStop游戏帮助～"
            await self.send_group_message(group_id, welcome_msg)

        elif notice_type == 'group_decrease':
            # 成员离群
            user_id = str(data.get('user_id'))
            # 可以在这里清理用户会话
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

    async def handle_request_event(self, data: Dict):
        """处理请求事件（加好友、加群等）"""
        # 可以实现自动同意加群等逻辑
        pass

    async def handle_meta_event(self, data: Dict):
        """处理元事件（心跳等）"""
        meta_event_type = data.get('meta_event_type')
        if meta_event_type == 'heartbeat':
            # 心跳事件，可以用来检查连接状态
            self.logger.debug("收到OneBot心跳")

    async def send_group_message(self, group_id: str, message: str):
        """发送群消息"""
        try:
            api_url = f"{self.onebot_url}/send_group_msg"
            params = {
                "group_id": int(group_id),
                "message": message
            }

            async with self.http_session.post(api_url, json=params) as response:
                if response.status != 200:
                    self.logger.error(f"发送群消息失败: {response.status}")

        except Exception as e:
            self.logger.error(f"发送群消息失败: {e}")

    async def send_private_message(self, user_id: str, message: str):
        """发送私聊消息"""
        try:
            api_url = f"{self.onebot_url}/send_private_msg"
            params = {
                "user_id": int(user_id),
                "message": message
            }

            async with self.http_session.post(api_url, json=params) as response:
                if response.status != 200:
                    self.logger.error(f"发送私聊消息失败: {response.status}")

        except Exception as e:
            self.logger.error(f"发送私聊消息失败: {e}")

    def set_allowed_groups(self, group_ids: List[str]):
        """设置允许的群列表"""
        self.allowed_groups = group_ids

    def set_admin_users(self, user_ids: List[str]):
        """设置管理员用户列表"""
        self.admin_users = user_ids

    def get_user_info(self, user_id: str) -> Optional[QQUser]:
        """获取用户信息"""
        return self.user_info.get(user_id)

    def get_online_users(self) -> List[QQUser]:
        """获取在线用户列表"""
        return list(self.user_info.values())