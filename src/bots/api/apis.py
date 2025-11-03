"""
Lagrange OneBot 客户端类库
用于 QQ 机器人开发，支持消息监听、发送、at、图片等功能
"""

import asyncio
import json
import re
import base64
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from pathlib import Path
from dataclasses import dataclass

try:
    from websockets.asyncio.client import connect, ClientConnection
    WebSocketProtocol = ClientConnection
except ImportError:
    from websockets import connect
    from websockets.legacy.client import WebSocketClientProtocol
    WebSocketProtocol = WebSocketClientProtocol

from websockets.exceptions import WebSocketException

# ==================== 数据类 ====================

@dataclass
class AtUser:
    """被 at 的用户信息"""
    qq: int
    nickname: str

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.nickname}({self.qq})" if self.nickname else str(self.qq)

@dataclass
class GroupMessage:
    """
    群消息数据类

    Attributes:
        message_id: 消息 ID
        group_id: 群号
        user_id: 发送者 QQ 号
        sender_nickname: 发送者昵称
        raw_message: 原始消息文本
        message_array: 消息段数组
        plain_text: 纯文本内容（去除 CQ 码）
        at_list: 被 at 的 QQ 号列表
        at_users: 被 at 的用户列表（包含昵称）
        is_at_bot: 是否 at 了机器人
        time: 消息时间戳
    """
    message_id: int
    group_id: int
    user_id: int
    sender_nickname: str
    raw_message: str
    message_array: List[Dict[str, Any]]
    plain_text: str
    at_list: List[int]
    at_users: List[AtUser]
    is_at_bot: bool
    time: int


@dataclass
class PrivateMessage:
    """
    私聊消息数据类
    
    Attributes:
        message_id: 消息 ID
        user_id: 发送者 QQ 号
        sender_nickname: 发送者昵称
        raw_message: 原始消息文本
        plain_text: 纯文本内容
        time: 消息时间戳
    """
    message_id: int
    user_id: int
    sender_nickname: str
    raw_message: str
    plain_text: str
    time: int


# ==================== 消息构建器 ====================

class MessageSegment:
    """消息段构建器 - 用于构建复杂消息"""
    
    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        """
        创建文本消息段
        
        Args:
            content: 文本内容
            
        Returns:
            文本消息段
        """
        return {
            "type": "text",
            "data": {"text": content}
        }
    
    @staticmethod
    def at(user_id: Union[int, str]) -> Dict[str, Any]:
        """
        创建 at 消息段
        
        Args:
            user_id: QQ 号，传入 "all" 则 at 全体成员
            
        Returns:
            at 消息段
        """
        return {
            "type": "at",
            "data": {"qq": str(user_id)}
        }
    
    @staticmethod
    def image(
        file: Union[str, Path],
        image_type: str = "normal",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        创建图片消息段
        
        Args:
            file: 图片路径、URL 或 base64
            image_type: 图片类型 (flash: 闪照, show: 秀图, normal: 普通)
            use_cache: 是否使用缓存
            
        Returns:
            图片消息段
        """
        file_str = str(file)
        
        # 判断是否为本地文件
        if Path(file_str).exists():
            # 本地文件转 base64
            with open(file_str, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                file_str = f"base64://{image_data}"
        
        return {
            "type": "image",
            "data": {
                "file": file_str,
                "type": image_type,
                "cache": 1 if use_cache else 0
            }
        }
    
    @staticmethod
    def face(face_id: int) -> Dict[str, Any]:
        """
        创建 QQ 表情消息段
        
        Args:
            face_id: 表情 ID
            
        Returns:
            表情消息段
        """
        return {
            "type": "face",
            "data": {"id": str(face_id)}
        }
    
    @staticmethod
    def reply(message_id: int) -> Dict[str, Any]:
        """
        创建回复消息段
        
        Args:
            message_id: 要回复的消息 ID
            
        Returns:
            回复消息段
        """
        return {
            "type": "reply",
            "data": {"id": str(message_id)}
        }
    
    @staticmethod
    def record(file: Union[str, Path]) -> Dict[str, Any]:
        """
        创建语音消息段
        
        Args:
            file: 语音文件路径或 URL
            
        Returns:
            语音消息段
        """
        file_str = str(file)
        
        if Path(file_str).exists():
            with open(file_str, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode()
                file_str = f"base64://{audio_data}"
        
        return {
            "type": "record",
            "data": {"file": file_str}
        }


class MessageBuilder:
    """
    消息构建器 - 支持链式调用
    
    Example:
         msg = (MessageBuilder()
        ...        .at(123456)
        ...        .text(" 你好")
        ...        .image("https://example.com/img.jpg")
        ...        .build())
    """
    
    def __init__(self) -> None:
        """初始化消息构建器"""
        self.segments: List[Dict[str, Any]] = []
    
    def text(self, content: str) -> 'MessageBuilder':
        """
        添加文本
        
        Args:
            content: 文本内容
            
        Returns:
            self，支持链式调用
        """
        self.segments.append(MessageSegment.text(content))
        return self
    
    def at(self, user_id: Union[int, str]) -> 'MessageBuilder':
        """
        添加 at
        
        Args:
            user_id: QQ 号或 "all"
            
        Returns:
            self，支持链式调用
        """
        self.segments.append(MessageSegment.at(user_id))
        return self
    
    def at_all(self) -> 'MessageBuilder':
        """
        at 全体成员
        
        Returns:
            self，支持链式调用
        """
        return self.at("all")
    
    def image(
        self, 
        file: Union[str, Path],
        image_type: str = "normal",
        use_cache: bool = True
    ) -> 'MessageBuilder':
        """
        添加图片
        
        Args:
            file: 图片路径或 URL
            image_type: 图片类型
            use_cache: 是否使用缓存
            
        Returns:
            self，支持链式调用
        """
        self.segments.append(MessageSegment.image(file, image_type, use_cache))
        return self
    
    def face(self, face_id: int) -> 'MessageBuilder':
        """
        添加 QQ 表情
        
        Args:
            face_id: 表情 ID
            
        Returns:
            self，支持链式调用
        """
        self.segments.append(MessageSegment.face(face_id))
        return self
    
    def reply(self, message_id: int) -> 'MessageBuilder':
        """
        添加回复引用
        
        Args:
            message_id: 消息 ID
            
        Returns:
            self，支持链式调用
        """
        self.segments.append(MessageSegment.reply(message_id))
        return self
    
    def record(self, file: Union[str, Path]) -> 'MessageBuilder':
        """
        添加语音
        
        Args:
            file: 语音文件路径或 URL
            
        Returns:
            self，支持链式调用
        """
        self.segments.append(MessageSegment.record(file))
        return self
    
    def build(self) -> List[Dict[str, Any]]:
        """
        构建消息数组
        
        Returns:
            消息段列表
        """
        return self.segments
    
    def clear(self) -> 'MessageBuilder':
        """
        清空消息段
        
        Returns:
            self，支持链式调用
        """
        self.segments.clear()
        return self


# ==================== 主类 ====================

class LagrangeBot:
    """
    Lagrange OneBot 客户端
    
    用于连接 Lagrange.OneBot，实现 QQ 机器人功能
    
    Example:
         bot = LagrangeBot()
         await bot.connect()
         await bot.send_group_msg(123456789, "Hello!")
         await bot.listen()
    """
    
    def __init__(
        self,
        ws_url: str = "ws://127.0.0.1:8080",
        access_token: Optional[str] = None,
        allowed_groups: Optional[List[int]] = None,
        blocked_groups: Optional[List[int]] = None,
        enable_log: bool = True
    ) -> None:
        """
        初始化客户端

        Args:
            ws_url: WebSocket 地址
            access_token: 访问令牌（可选）
            allowed_groups: 白名单群号列表，None 表示监听所有群
            blocked_groups: 黑名单群号列表
            enable_log: 是否启用日志输出
        """
        self.ws_url: str = ws_url
        self.access_token: Optional[str] = access_token
        self.ws: Optional[WebSocketProtocol] = None
        self.bot_qq: Optional[int] = None
        self.allowed_groups: Optional[List[int]] = allowed_groups
        self.blocked_groups: Optional[List[int]] = blocked_groups
        self.enable_log: bool = enable_log
        
        # 消息处理器
        self.group_msg_handlers: List[Callable[[GroupMessage], Awaitable[None]]] = []
        self.private_msg_handlers: List[Callable[[PrivateMessage], Awaitable[None]]] = []
        self.keyword_handlers: Dict[str, Callable[[GroupMessage], Awaitable[None]]] = {}
        self.command_handlers: Dict[str, Callable[[GroupMessage, List[str]], Awaitable[None]]] = {}
        
        # 运行状态
        self._running: bool = False
    
    def _log(self, message: str) -> None:
        """
        内部日志方法
        
        Args:
            message: 日志内容
        """
        if self.enable_log:
            print(message)
    
    # ==================== 连接管理 ====================
    
    async def connect(self, retry: int = 3, delay: int = 2) -> None:
        """
        建立 WebSocket 连接

        Args:
            retry: 重试次数
            delay: 重试间隔（秒）

        Raises:
            ConnectionError: 连接失败
        """
        for attempt in range(retry):
            try:
                # 准备连接参数
                connect_kwargs = {
                    "ping_interval": 30,
                    "ping_timeout": 10
                }

                # 如果有 access_token，添加到请求头
                if self.access_token:
                    connect_kwargs["additional_headers"] = {
                        "Authorization": f"Bearer {self.access_token}"
                    }
                    self._log("🔑 使用 Access Token 连接")

                self.ws = await connect(self.ws_url, **connect_kwargs)
                self._log(f"[INFO] 已连接到 {self.ws_url}")

                # 获取 Bot QQ 号
                login_info = await self._call_api("get_login_info", {})
                self.bot_qq = login_info.get("data", {}).get("user_id")
                self._log(f"🤖 Bot QQ: {self.bot_qq}")

                return
            except ConnectionRefusedError:
                self._log(f"[ERROR] 连接被拒绝 (尝试 {attempt + 1}/{retry})")
                if attempt < retry - 1:
                    self._log(f"[INFO] {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    raise ConnectionError(
                        "无法连接到 Lagrange.OneBot，请检查服务是否启动"
                    )
            except Exception as e:
                self._log(f"[ERROR] 连接失败: {e}")
                raise
    
    async def disconnect(self) -> None:
        """关闭 WebSocket 连接"""
        self._running = False
        if self.ws:
            await self.ws.close()
            self._log("🔌 连接已关闭")
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            是否已连接
        """
        return self.ws is not None and not self.ws.closed
    
    # ==================== API 调用 ====================
    
    async def _call_api(
        self, 
        action: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 OneBot API
        
        Args:
            action: API 动作
            params: 参数
            
        Returns:
            API 响应
            
        Raises:
            RuntimeError: 未连接到 WebSocket
        """
        if not self.ws:
            raise RuntimeError("未连接到 WebSocket，请先调用 connect()")
        
        payload = {
            "action": action,
            "params": params
        }
        
        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        result: Dict[str, Any] = json.loads(response)
        
        if result.get("status") == "failed":
            error_msg = result.get("wording", "未知错误")
            self._log(f"⚠️ API 调用失败: {error_msg}")
        
        return result
    
    # ==================== 消息发送 ====================
    
    async def send_group_msg(
        self,
        group_id: int,
        message: Union[str, List[Dict[str, Any]], MessageBuilder]
    ) -> Dict[str, Any]:
        """
        发送群消息
        
        Args:
            group_id: 群号
            message: 消息内容（字符串、消息段数组或 MessageBuilder）
            
        Returns:
            发送结果，包含 message_id
            
        Example:
             # 发送文本
             await bot.send_group_msg(123456, "Hello")
             
             # 发送消息段数组
             msg = [
            ...     {"type": "at", "data": {"qq": "123"}},
            ...     {"type": "text", "data": {"text": " Hi"}}
            ... ]
             await bot.send_group_msg(123456, msg)
             
             # 使用 MessageBuilder
             msg = MessageBuilder().at(123).text(" Hi").build()
             await bot.send_group_msg(123456, msg)
        """
        if isinstance(message, MessageBuilder):
            message = message.build()
        
        return await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": message
        })
    
    async def send_private_msg(
        self,
        user_id: int,
        message: Union[str, List[Dict[str, Any]], MessageBuilder]
    ) -> Dict[str, Any]:
        """
        发送私聊消息
        
        Args:
            user_id: QQ 号
            message: 消息内容
            
        Returns:
            发送结果
        """
        if isinstance(message, MessageBuilder):
            message = message.build()
        
        return await self._call_api("send_private_msg", {
            "user_id": user_id,
            "message": message
        })
    
    async def send_group_text(
        self,
        group_id: int,
        text: str
    ) -> Dict[str, Any]:
        """
        发送群文本消息（便捷方法）
        
        Args:
            group_id: 群号
            text: 文本内容
            
        Returns:
            发送结果
        """
        return await self.send_group_msg(group_id, text)
    
    async def send_group_at(
        self,
        group_id: int,
        user_id: int,
        text: str = ""
    ) -> Dict[str, Any]:
        """
        发送群 at 消息（便捷方法）
        
        Args:
            group_id: 群号
            user_id: 要 at 的 QQ 号
            text: 附加文本
            
        Returns:
            发送结果
        """
        msg = MessageBuilder().at(user_id)
        if text:
            msg.text(f" {text}")
        return await self.send_group_msg(group_id, msg)
    
    async def send_group_at_text_image(
        self,
        group_id: int,
        user_id: int,
        text: str,
        image: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        发送 at + 文本 + 图片消息（便捷方法）
        
        Args:
            group_id: 群号
            user_id: 要 at 的 QQ 号
            text: 文本内容
            image: 图片路径或 URL
            
        Returns:
            发送结果
        """
        msg = (MessageBuilder()
               .at(user_id)
               .text(f" {text}\n")
               .image(image))
        return await self.send_group_msg(group_id, msg)
    
    async def delete_msg(self, message_id: int) -> Dict[str, Any]:
        """
        撤回消息
        
        Args:
            message_id: 消息 ID
            
        Returns:
            撤回结果
        """
        return await self._call_api("delete_msg", {
            "message_id": message_id
        })
    
    # ==================== 群管理 ====================
    
    async def get_group_list(self) -> List[Dict[str, Any]]:
        """
        获取群列表
        
        Returns:
            群列表，每个元素包含 group_id, group_name, member_count 等
        """
        result = await self._call_api("get_group_list", {})
        return result.get("data", [])
    
    async def get_group_info(self, group_id: int) -> Dict[str, Any]:
        """
        获取群信息
        
        Args:
            group_id: 群号
            
        Returns:
            群信息
        """
        result = await self._call_api("get_group_info", {
            "group_id": group_id
        })
        return result.get("data", {})
    
    async def get_group_member_list(self, group_id: int) -> List[Dict[str, Any]]:
        """
        获取群成员列表
        
        Args:
            group_id: 群号
            
        Returns:
            成员列表
        """
        result = await self._call_api("get_group_member_list", {
            "group_id": group_id
        })
        return result.get("data", [])
    
    async def get_group_member_info(
        self,
        group_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取群成员信息
        
        Args:
            group_id: 群号
            user_id: QQ 号
            
        Returns:
            成员信息
        """
        result = await self._call_api("get_group_member_info", {
            "group_id": group_id,
            "user_id": user_id
        })
        return result.get("data", {})
    
    async def set_group_ban(
        self,
        group_id: int,
        user_id: int,
        duration: int = 600
    ) -> Dict[str, Any]:
        """
        禁言群成员
        
        Args:
            group_id: 群号
            user_id: QQ 号
            duration: 禁言时长（秒），0 表示解除禁言
            
        Returns:
            操作结果
        """
        return await self._call_api("set_group_ban", {
            "group_id": group_id,
            "user_id": user_id,
            "duration": duration
        })
    
    async def set_group_kick(
        self,
        group_id: int,
        user_id: int,
        reject_add_request: bool = False
    ) -> Dict[str, Any]:
        """
        踢出群成员
        
        Args:
            group_id: 群号
            user_id: QQ 号
            reject_add_request: 是否拒绝再次申请
            
        Returns:
            操作结果
        """
        return await self._call_api("set_group_kick", {
            "group_id": group_id,
            "user_id": user_id,
            "reject_add_request": reject_add_request
        })
    
    # ==================== 消息解析 ====================

    @staticmethod
    def parse_message_array(
            message: Union[str, List[Dict[str, Any]]]
    ) -> tuple[str, List[int], List[AtUser]]:
        """
        解析消息数组，提取纯文本、at 列表和 at 用户信息

        Args:
            message: 消息数组或字符串

        Returns:
            (纯文本, at列表, at用户列表)
        """
        plain_text = ""
        at_list = []
        at_users = []  # 新增

        # 处理 None 或空值
        if not message:
            return "", [], []

        # 字符串格式（CQ 码）- 无法获取昵称
        if isinstance(message, str):
            # 提取 at
            at_pattern = r'\[CQ:at,qq=(\d+)\]'
            at_matches = re.findall(at_pattern, message)
            at_list = [int(qq) for qq in at_matches if qq.isdigit()]

            # CQ 码格式无法获取昵称，创建空昵称的 AtUser
            at_users = [AtUser(qq=qq, nickname="") for qq in at_list]

            # 提取纯文本（移除所有 CQ 码）
            plain_text = re.sub(r'\[CQ:.*?\]', '', message).strip()

            return plain_text, at_list, at_users

        # 消息段数组格式
        if isinstance(message, list):
            for segment in message:
                if not isinstance(segment, dict):
                    continue

                seg_type = segment.get("type", "")
                seg_data = segment.get("data", {})

                if seg_type == "text":
                    text_content = seg_data.get("text", "")
                    plain_text += str(text_content)

                elif seg_type == "at":
                    qq = seg_data.get("qq", "")
                    # 处理各种可能的格式
                    if qq and qq != "all":
                        # 确保是数字
                        qq_str = str(qq).strip()
                        if qq_str.isdigit():
                            qq_int = int(qq_str)
                            at_list.append(qq_int)

                            nickname = seg_data.get("name", "")  # Lagrange 会在 data 中提供 name
                            at_users.append(AtUser(qq=qq_int, nickname=nickname))

        return plain_text.strip(), at_list, at_users
    
    def is_at_bot_in_array(
        self,
        message: Union[str, List[Dict[str, Any]]]
    ) -> bool:
        """
        判断消息是否 at 了机器人
        
        Args:
            message: 消息数组或字符串
            
        Returns:
            是否 at 了机器人
        """
        if not self.bot_qq:
            return False
        
        # 处理 None 或空值
        if not message:
            return False
        
        bot_qq_str = str(self.bot_qq)
        
        # 字符串格式
        if isinstance(message, str):
            return f"[CQ:at,qq={bot_qq_str}]" in message
        
        # 消息段数组格式
        if isinstance(message, list):
            for segment in message:
                if not isinstance(segment, dict):
                    continue
                
                if segment.get("type") == "at":
                    qq = segment.get("data", {}).get("qq", "")
                    if str(qq) == bot_qq_str:
                        return True
        
        return False

    async def _parse_group_message(self, data: Dict[str, Any]) -> GroupMessage:
        """
        解析群消息数据（带昵称查询）

        Args:
            data: 原始消息数据

        Returns:
            GroupMessage 对象
        """
        message = data.get("message", [])
        raw_message = data.get("raw_message", "")
        sender = data.get("sender", {})
        group_id = data["group_id"]

        # 解析消息
        plain_text, at_list, at_users = self.parse_message_array(message)
        is_at_bot = self.is_at_bot_in_array(message)

        # 如果 at_users 中有昵称为空的，尝试查询
        for at_user in at_users:
            if not at_user.nickname:
                try:
                    # 查询群成员信息
                    member_info = await self.get_group_member_info(group_id, at_user.qq)
                    at_user.nickname = member_info.get("nickname", f"用户{at_user.qq}")
                except Exception as e:
                    # 查询失败，使用默认昵称
                    at_user.nickname = f"用户{at_user.qq}"

        return GroupMessage(
            message_id=data["message_id"],
            group_id=group_id,
            user_id=data["user_id"],
            sender_nickname=sender.get("nickname", "未知"),
            raw_message=raw_message,
            message_array=message if isinstance(message, list) else [],
            plain_text=plain_text,
            at_list=at_list,
            at_users=at_users,
            is_at_bot=is_at_bot,
            time=data["time"]
        )
    
    async def _parse_private_message(self, data: Dict[str, Any]) -> PrivateMessage:
        """
        解析私聊消息数据
        
        Args:
            data: 原始消息数据
            
        Returns:
            PrivateMessage 对象
        """
        message = data.get("message", [])
        raw_message = data.get("raw_message", "")
        sender = data.get("sender", {})
        
        plain_text, _ = self.parse_message_array(message)
        
        return PrivateMessage(
            message_id=data["message_id"],
            user_id=data["user_id"],
            sender_nickname=sender.get("nickname", "未知"),
            raw_message=raw_message,
            plain_text=plain_text,
            time=data["time"]
        )
    
    # ==================== 装饰器：注册处理器 ====================
    
    def on_group_message(
        self, 
        func: Callable[[GroupMessage], Awaitable[None]]
    ) -> Callable[[GroupMessage], Awaitable[None]]:
        """
        装饰器：注册群消息处理器
        
        Args:
            func: 处理函数
            
        Returns:
            原函数
            
        Example:
             @bot.on_group_message
             async def handler(msg: GroupMessage) -> None:
            ...     print(f"收到消息: {msg.plain_text}")
        """
        self.group_msg_handlers.append(func)
        return func
    
    def on_private_message(
        self,
        func: Callable[[PrivateMessage], Awaitable[None]]
    ) -> Callable[[PrivateMessage], Awaitable[None]]:
        """
        装饰器：注册私聊消息处理器
        
        Args:
            func: 处理函数
            
        Returns:
            原函数
        """
        self.private_msg_handlers.append(func)
        return func
    
    def on_keyword(
        self,
        keyword: str
    ) -> Callable[[Callable[[GroupMessage], Awaitable[None]]], Callable[[GroupMessage], Awaitable[None]]]:
        """
        装饰器：注册关键词处理器
        
        Args:
            keyword: 关键词
            
        Returns:
            装饰器函数
            
        Example:
             @bot.on_keyword("你好")
             async def handler(msg: GroupMessage) -> None:
            ...     await bot.send_group_at(msg.group_id, msg.user_id, "你好！")
        """
        def decorator(
            func: Callable[[GroupMessage], Awaitable[None]]
        ) -> Callable[[GroupMessage], Awaitable[None]]:
            self.keyword_handlers[keyword] = func
            return func
        return decorator
    
    def on_command(
        self,
        command: str
    ) -> Callable[[Callable[[GroupMessage, List[str]], Awaitable[None]]], Callable[[GroupMessage, List[str]], Awaitable[None]]]:
        """
        装饰器：注册命令处理器（以 / 开头）
        
        Args:
            command: 命令名（不含 /）
            
        Returns:
            装饰器函数
            
        Example:
             @bot.on_command("help")
             async def handler(msg: GroupMessage, args: List[str]) -> None:
            ...     await bot.send_group_msg(msg.group_id, "帮助信息...")
        """
        def decorator(
            func: Callable[[GroupMessage, List[str]], Awaitable[None]]
        ) -> Callable[[GroupMessage, List[str]], Awaitable[None]]:
            self.command_handlers[command] = func
            return func
        return decorator
    
    # ==================== 消息监听与处理 ====================
    
    async def _handle_group_message(self, data: Dict[str, Any]) -> None:
        """
        处理群消息（内部方法）
        
        Args:
            data: 原始消息数据
        """
        group_id = data["group_id"]
        
        # 白名单过滤
        if self.allowed_groups is not None and group_id not in self.allowed_groups:
            return
        
        # 黑名单过滤
        if self.blocked_groups is not None and group_id in self.blocked_groups:
            return
        
        msg = await self._parse_group_message(data)
        
        # 日志
        if self.enable_log:
            self._log(f"📩 群 {msg.group_id} | {msg.sender_nickname}({msg.user_id}): {msg.plain_text}")
        
        # 执行所有群消息处理器
        for handler in self.group_msg_handlers:
            try:
                await handler(msg)
            except Exception as e:
                self._log(f"[ERROR] 处理器错误: {e}")
        
        # 检查关键词
        for keyword, handler in self.keyword_handlers.items():
            if keyword in msg.plain_text:
                try:
                    await handler(msg)
                except Exception as e:
                    self._log(f"[ERROR] 关键词处理器错误: {e}")
        
        # 检查命令
        if msg.plain_text.startswith("/"):
            parts = msg.plain_text[1:].split()
            if parts:
                command = parts[0]
                args = parts[1:]
                
                if command in self.command_handlers:
                    try:
                        await self.command_handlers[command](msg, args)
                    except Exception as e:
                        self._log(f"[ERROR] 命令处理器错误: {e}")
    
    async def _handle_private_message(self, data: Dict[str, Any]) -> None:
        """
        处理私聊消息（内部方法）
        
        Args:
            data: 原始消息数据
        """
        msg = await self._parse_private_message(data)
        
        # 日志
        if self.enable_log:
            self._log(f"💬 私聊 | {msg.sender_nickname}({msg.user_id}): {msg.plain_text}")
        
        # 执行所有私聊消息处理器
        for handler in self.private_msg_handlers:
            try:
                await handler(msg)
            except Exception as e:
                self._log(f"[ERROR] 处理器错误: {e}")
    
    async def listen(self) -> None:
        """
        监听消息（阻塞运行）
        
        持续监听来自 Lagrange 的消息，并触发相应的处理器
        
        Example:
             bot = LagrangeBot()
             await bot.connect()
             await bot.listen()  # 开始监听，阻塞运行
        """
        if not self.ws:
            raise RuntimeError("未连接到 WebSocket，请先调用 connect()")
        
        self._log("👂 开始监听消息...\n")
        self._running = True
        
        try:
            while self._running:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=60)
                    data: Dict[str, Any] = json.loads(message)
                    
                    # 忽略心跳
                    if data.get("meta_event_type") == "heartbeat":
                        continue
                    
                    # 群消息
                    if (data.get("post_type") == "message" 
                        and data.get("message_type") == "group"):
                        await self._handle_group_message(data)
                    
                    # 私聊消息
                    elif (data.get("post_type") == "message" 
                          and data.get("message_type") == "private"):
                        await self._handle_private_message(data)
                
                except asyncio.TimeoutError:
                    # 超时，继续下一次循环
                    continue
        
        except WebSocketException as e:
            self._log(f"[ERROR] WebSocket 异常: {e}")
        except KeyboardInterrupt:
            self._log("\n👋 停止监听")
        finally:
            await self.disconnect()
    
    async def start(self) -> None:
        """
        启动 Bot（自动连接并监听）
        
        Example:
             bot = LagrangeBot()
             await bot.start()
        """
        await self.connect()
        await self.listen()
    
    async def stop(self) -> None:
        """停止 Bot"""
        await self.disconnect()


# ==================== 导出 ====================

__all__ = [
    'LagrangeBot',
    'MessageBuilder',
    'MessageSegment',
    'GroupMessage',
    'PrivateMessage',
]