"""
消息格式调试工具 - 帮助查看Lagrange.OneBot发送的实际消息格式
"""

import asyncio
import websockets
import json
from typing import Dict, Any


class MessageDebugger:
    """消息格式调试器"""

    def __init__(self, ws_url: str = "ws://127.0.0.1:8080/onebot/v11/ws"):
        self.ws_url = ws_url

    async def connect_and_debug(self):
        """连接并调试消息格式"""
        print("🔍 启动消息格式调试器...")
        print(f"连接到: {self.ws_url}")
        print("=" * 60)

        try:
            async with websockets.connect(self.ws_url) as ws:
                print("✅ 已连接到 Lagrange.OneBot")
                print("⏳ 等待消息... (请在QQ群中发送一些测试消息)")
                print("=" * 60)

                async for message in ws:
                    try:
                        data = json.loads(message)
                        await self._debug_message(data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析失败: {e}")
                        print(f"原始消息: {message}")
                    except Exception as e:
                        print(f"❌ 处理失败: {e}")

        except Exception as e:
            print(f"❌ 连接失败: {e}")

    async def _debug_message(self, data: Dict[str, Any]):
        """调试单个消息"""
        post_type = data.get("post_type")

        if post_type == "message":
            message_type = data.get("message_type")
            print(f"\n📩 收到消息事件 ({message_type})")
            print("-" * 40)

            # 基本信息
            if message_type == "group":
                print(f"群号: {data.get('group_id')}")
            print(f"用户ID: {data.get('user_id')}")
            print(f"消息ID: {data.get('message_id')}")

            # 关键：分析消息格式
            message_field = data.get("message")
            print(f"\n🔍 消息字段分析:")
            print(f"类型: {type(message_field)}")
            print(f"原始内容: {repr(message_field)}")

            if isinstance(message_field, list):
                print("📋 CQ码数组内容:")
                for i, segment in enumerate(message_field):
                    print(f"  [{i}] {type(segment)}: {repr(segment)}")

                    if isinstance(segment, dict):
                        print(f"      类型: {segment.get('type')}")
                        print(f"      数据: {segment.get('data')}")

            # 提取文本
            extracted_text = self._extract_text_safe(message_field)
            print(f"\n📝 提取的文本: '{extracted_text}'")

            # 其他字段
            raw_message = data.get("raw_message")
            if raw_message != message_field:
                print(f"原始消息字段: {repr(raw_message)}")

            sender = data.get("sender", {})
            if sender:
                print(f"发送者: {sender.get('nickname', 'N/A')} (QQ:{sender.get('user_id', 'N/A')})")

        elif post_type == "meta_event":
            meta_event_type = data.get("meta_event_type")
            if meta_event_type == "heartbeat":
                print("💓 心跳事件")
            else:
                print(f"🔔 元事件: {meta_event_type}")

        elif post_type == "notice":
            notice_type = data.get("notice_type")
            print(f"📢 通知事件: {notice_type}")

        else:
            print(f"❓ 未知事件类型: {post_type}")
            print(f"完整数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

        print("=" * 60)

    def _extract_text_safe(self, message_data) -> str:
        """安全地提取文本内容"""
        try:
            if isinstance(message_data, str):
                return message_data.strip()

            elif isinstance(message_data, list):
                text_parts = []
                for segment in message_data:
                    if isinstance(segment, dict) and segment.get("type") == "text":
                        text_parts.append(segment.get("data", {}).get("text", ""))
                    elif isinstance(segment, str):
                        text_parts.append(segment)
                return " ".join(text_parts).strip()

            elif isinstance(message_data, dict) and message_data.get("type") == "text":
                return message_data.get("data", {}).get("text", "").strip()

            else:
                return str(message_data).strip()

        except Exception as e:
            return f"[提取失败: {e}]"


async def main():
    """主函数"""
    debugger = MessageDebugger()
    await debugger.connect_and_debug()


if __name__ == "__main__":
    print("🐛 Lagrange.OneBot 消息格式调试工具")
    print("用于分析消息数据结构，解决 'list' object has no attribute 'strip' 错误")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断调试")
    except Exception as e:
        print(f"\n❌ 调试工具运行失败: {e}")