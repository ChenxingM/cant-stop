import asyncio
import json
import base64
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from websockets import connect, WebSocketClientProtocol
from websockets.exceptions import WebSocketException
from enum import Enum


class MessageSegmentType(Enum):
    """消息段类型枚举"""
    TEXT = "text"
    AT = "at"
    IMAGE = "image"
    FACE = "face"
    REPLY = "reply"
    RECORD = "record"


class MessageSegment:
    """消息段构建器"""

    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        """
        纯文本消息段

        Args:
            content: 文本内容

        Returns:
            消息段字典
        """
        return {
            "type": "text",
            "data": {"text": content}
        }

    @staticmethod
    def at(user_id: Union[int, str]) -> Dict[str, Any]:
        """
        at 用户消息段

        Args:
            user_id: QQ 号，传入 "all" 则 at 全体成员

        Returns:
            消息段字典
        """
        return {
            "type": "at",
            "data": {"qq": str(user_id)}
        }

    @staticmethod
    def image(
            file: Union[str, Path],
            image_type: str = "flash",
            use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        图片消息段

        Args:
            file: 图片路径、URL 或 base64
            image_type: 图片类型 (flash: 闪照, show: 秀图, normal: 普通)
            use_cache: 是否使用缓存

        Returns:
            消息段字典
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
        QQ 表情消息段

        Args:
            face_id: 表情 ID

        Returns:
            消息段字典
        """
        return {
            "type": "face",
            "data": {"id": str(face_id)}
        }

    @staticmethod
    def reply(message_id: int) -> Dict[str, Any]:
        """
        回复消息段

        Args:
            message_id: 要回复的消息 ID

        Returns:
            消息段字典
        """
        return {
            "type": "reply",
            "data": {"id": str(message_id)}
        }


class MessageBuilder:
    """消息构建器 - 链式调用"""

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


class LagrangeBot:
    """Lagrange OneBot 客户端"""

    def __init__(self, ws_url: str = "ws://127.0.0.1:8080") -> None:
        """
        初始化客户端

        Args:
            ws_url: WebSocket 地址
        """
        self.ws_url: str = ws_url
        self.ws: Optional[WebSocketClientProtocol] = None
        self.bot_qq: Optional[int] = None

    async def connect(self) -> None:
        """建立连接"""
        self.ws = await connect(self.ws_url, ping_interval=30)
        print(f"✅ 已连接到 {self.ws_url}")

        # 获取 Bot QQ 号
        login_info = await self._call_api("get_login_info", {})
        self.bot_qq = login_info.get("data", {}).get("user_id")
        print(f"🤖 Bot QQ: {self.bot_qq}")

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
        """
        if not self.ws:
            raise RuntimeError("未连接到 WebSocket")

        payload = {
            "action": action,
            "params": params
        }

        await self.ws.send(json.dumps(payload))
        response = await self.ws.recv()
        result: Dict[str, Any] = json.loads(response)

        if result.get("status") == "failed":
            error_msg = result.get("wording", "未知错误")
            print(f"⚠️ API 调用失败: {error_msg}")

        return result

    # ==================== 便捷发送方法 ====================

    async def send_text(
            self,
            group_id: int,
            text: str
    ) -> Dict[str, Any]:
        """
        发送纯文本消息

        Args:
            group_id: 群号
            text: 文本内容

        Returns:
            发送结果
        """
        return await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": [MessageSegment.text(text)]
        })

    async def send_at(
            self,
            group_id: int,
            user_id: Union[int, str]
    ) -> Dict[str, Any]:
        """
        发送 at 消息

        Args:
            group_id: 群号
            user_id: QQ 号或 "all"

        Returns:
            发送结果
        """
        return await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": [MessageSegment.at(user_id)]
        })

    async def send_at_text(
            self,
            group_id: int,
            user_id: Union[int, str],
            text: str
    ) -> Dict[str, Any]:
        """
        发送 at + 文本消息

        Args:
            group_id: 群号
            user_id: QQ 号或 "all"
            text: 文本内容

        Returns:
            发送结果
        """
        message = [
            MessageSegment.at(user_id),
            MessageSegment.text(f" {text}")
        ]

        return await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": message
        })

    async def send_at_text_image(
            self,
            group_id: int,
            user_id: Union[int, str],
            text: str,
            image: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        发送 at + 文本 + 图片消息

        Args:
            group_id: 群号
            user_id: QQ 号或 "all"
            text: 文本内容
            image: 图片路径或 URL

        Returns:
            发送结果
        """
        message = [
            MessageSegment.at(user_id),
            MessageSegment.text(f" {text}\n"),
            MessageSegment.image(image)
        ]

        return await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": message
        })

    async def send_message(
            self,
            group_id: int,
            message: Union[List[Dict[str, Any]], MessageBuilder]
    ) -> Dict[str, Any]:
        """
        发送自定义消息（支持 MessageBuilder）

        Args:
            group_id: 群号
            message: 消息段列表或 MessageBuilder 对象

        Returns:
            发送结果
        """
        if isinstance(message, MessageBuilder):
            message = message.build()

        return await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": message
        })

    # ==================== 消息处理 ====================

    async def listen(self) -> None:
        """监听消息"""
        try:
            async for message in self.ws:
                data: Dict[str, Any] = json.loads(message)

                if data.get("meta_event_type") == "heartbeat":
                    continue

                if (data.get("post_type") == "message"
                        and data.get("message_type") == "group"):
                    await self.handle_group_message(data)

        except WebSocketException as e:
            print(f"❌ WebSocket 异常: {e}")
        finally:
            if self.ws:
                await self.ws.close()

    async def handle_group_message(self, data: Dict[str, Any]) -> None:
        """
        处理群消息（可重写）

        Args:
            data: 消息数据
        """
        group_id: int = data["group_id"]
        user_id: int = data["user_id"]
        message: str = data.get("raw_message", "")

        print(f"📩 群 {group_id} | 用户 {user_id}: {message}")

        # 示例：响应 at 机器人的消息
        if f"[CQ:at,qq={self.bot_qq}]" in str(data.get("message", "")):
            if "你好" in message:
                await self.send_at_text(group_id, user_id, "你好呀！")
            elif "图片" in message:
                # 发送 at + 文本 + 图片
                await self.send_at_text_image(
                    group_id,
                    user_id,
                    "这是你要的图片：",
                    "https://picsum.photos/400/300"  # 示例图片
                )


# ==================== 使用示例 ====================

async def example_usage() -> None:
    """使用示例"""
    bot = LagrangeBot()
    await bot.connect()

    group_id = 123456789  # 替换为真实群号
    user_id = 987654321  # 替换为真实 QQ 号

    # 1. 发送纯文本
    await bot.send_text(group_id, "Hello, World!")

    # 2. 发送 at
    await bot.send_at(group_id, user_id)

    # 3. 发送 at + 文本
    await bot.send_at_text(group_id, user_id, "请查看这条消息")

    # 4. 发送 at + 文本 + 图片（URL）
    await bot.send_at_text_image(
        group_id,
        user_id,
        "今日天气预报",
        "https://example.com/weather.jpg"
    )

    # 5. 发送 at + 文本 + 图片（本地文件）
    await bot.send_at_text_image(
        group_id,
        user_id,
        "渲染完成！",
        Path("E:/renders/output.png")
    )

    # 6. 使用 MessageBuilder 构建复杂消息
    msg = (MessageBuilder()
           .at(user_id)
           .text(" 任务进度：\n")
           .text("✅ 建模完成\n")
           .text("✅ 贴图完成\n")
           .text("⏳ 渲染中...\n")
           .image("https://example.com/progress.png")
           .face(178)  # QQ 表情
           .build())

    await bot.send_message(group_id, msg)

    # 7. at 多人 + 文本 + 多图
    msg = (MessageBuilder()
           .at(111111)
           .at(222222)
           .at(333333)
           .text(" 会议通知：\n今天下午3点开会")
           .image("https://example.com/meeting1.jpg")
           .image("https://example.com/meeting2.jpg")
           .build())

    await bot.send_message(group_id, msg)

    # 8. at 全体成员
    await bot.send_at_text(group_id, "all", "紧急通知！")

    # 监听消息
    # await bot.listen()


async def main() -> None:
    """主函数"""
    try:
        await example_usage()
    except KeyboardInterrupt:
        print("\n👋 退出")
    except Exception as e:
        print(f"💥 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())