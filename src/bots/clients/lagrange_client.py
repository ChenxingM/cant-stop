"""
Lagrange.OneBot WebSocket 客户端
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LagrangeClient:
    """Lagrange.OneBot WebSocket客户端"""

    def __init__(self, ws_url: str = "ws://127.0.0.2:8081/onebot/v11/ws", access_token: Optional[str] = None) -> None:
        """
        初始化 Lagrange OneBot 客户端

        Args:
            ws_url: WebSocket 连接地址
            access_token: 访问令牌（可选）
        """
        self.ws_url: str = ws_url
        self.access_token: Optional[str] = access_token
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    def _extract_message_text(self, message_data) -> str:
        """
        从消息数据中提取文本内容 - 处理OneBot协议的各种格式

        Args:
            message_data: 可能是字符串、字典或列表格式的消息数据

        Returns:
            提取的文本内容
        """
        try:
            if isinstance(message_data, dict):
                # 优先处理dict格式
                if message_data.get("type") == "text":
                    return message_data.get("data", {}).get("text", "").strip()
                else:
                    # 尝试直接获取文本字段
                    text_candidates = ["text", "message", "content", "data"]
                    for key in text_candidates:
                        if key in message_data:
                            value = message_data[key]
                            if isinstance(value, str):
                                return value.strip()
                            elif isinstance(value, dict) and "text" in value:
                                return value["text"].strip()
                    return ""

            elif isinstance(message_data, str):
                # 直接是字符串
                return message_data.strip()

            elif isinstance(message_data, list):
                # CQ码数组格式
                text_parts = []
                for segment in message_data:
                    if isinstance(segment, dict):
                        if segment.get("type") == "text":
                            text_parts.append(segment.get("data", {}).get("text", ""))
                    elif isinstance(segment, str):
                        text_parts.append(segment)
                return " ".join(text_parts).strip()

            else:
                # 其他格式，尝试转换为字符串
                return str(message_data).strip()

        except Exception as e:
            logger.warning(f"解析消息格式失败: {e}, 原始数据: {message_data}")
            return str(message_data) if message_data else ""

    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        extra_headers = {}
        if self.access_token:
            extra_headers["Authorization"] = f"Bearer {self.access_token}"
            logger.info("🔑 使用 Access Token 连接")

        self.ws = await websockets.connect(self.ws_url, extra_headers=extra_headers)
        logger.info("✅ 已连接到 Lagrange.OneBot")

    async def disconnect(self) -> None:
        """断开连接"""
        if self.ws:
            await self.ws.close()
            logger.info("🔌 已断开 Lagrange.OneBot 连接")

    async def send_group_msg(self, group_id: int, message: str) -> Dict[str, Any]:
        """
        发送群消息

        Args:
            group_id: 群号
            message: 消息内容

        Returns:
            API 响应结果
        """
        if not self.ws:
            raise RuntimeError("WebSocket 连接未建立")

        payload: Dict[str, Any] = {
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": message
            }
        }

        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        return json.loads(response)

    async def send_private_msg(self, user_id: int, message: str) -> Dict[str, Any]:
        """
        发送私聊消息

        Args:
            user_id: 用户ID
            message: 消息内容

        Returns:
            API 响应结果
        """
        if not self.ws:
            raise RuntimeError("WebSocket 连接未建立")

        payload: Dict[str, Any] = {
            "action": "send_private_msg",
            "params": {
                "user_id": user_id,
                "message": message
            }
        }

        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        return json.loads(response)

    async def listen_messages(self, message_handler=None):
        """
        监听消息

        Args:
            message_handler: 消息处理函数，接收 (event_type, data) 参数
        """
        if not self.ws:
            raise RuntimeError("WebSocket 连接未建立")

        async for message in self.ws:
            try:
                data: Dict[str, Any] = json.loads(message)

                # 处理不同类型的事件
                if message_handler:
                    await message_handler(data)
                else:
                    # 默认处理逻辑
                    await self._default_message_handler(data)

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
            except Exception as e:
                logger.error(f"处理消息失败: {e}")

    async def _default_message_handler(self, data: Dict[str, Any]):
        """默认消息处理器（用于演示）"""
        post_type = data.get("post_type")

        if post_type == "message":
            message_type = data.get("message_type")
            if message_type == "group":
                group_id = data["group_id"]
                user_id = data["user_id"]
                msg = self._extract_message_text(data["message"])
                logger.info(f"接收到群 {group_id} |用户 {user_id} 的消息: {msg}")

                # 简单的回复逻辑
                if msg == "ping":
                    await self.send_group_msg(group_id, "pong!")
                elif msg == "hello":
                    await self.send_group_msg(group_id, "Hello from LagrangeClient!")

            elif message_type == "private":
                user_id = data["user_id"]
                msg = self._extract_message_text(data["message"])
                logger.info(f"💬 私聊 {user_id}: {msg}")

        elif post_type == "meta_event":
            meta_event_type = data.get("meta_event_type")
            if meta_event_type == "heartbeat":
                logger.debug("💓 心跳事件")