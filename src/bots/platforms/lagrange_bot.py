"""
基于LagrangeClient的CantStop游戏机器人
使用WebSocket与Lagrange.OneBot通信
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from ...services.game_service import GameService
from ...services.message_processor import MessageProcessor, UserMessage
from ...core.event_system import emit_game_event, GameEventType
from ..adapters.qq_message_adapter import QQMessageAdapter, MessageStyle


@dataclass
class QQUserInfo:
    """QQ用户信息"""
    user_id: int
    nickname: str
    group_id: int = None
    card: str = None


class CantStopLagrangeBot:
    """CantStop游戏机器人 - 基于Lagrange WebSocket"""

    def __init__(self,
                 ws_url: str = "ws://127.0.0.1:8080/onebot/v11/ws",
                 allowed_groups: List[int] = None,
                 admin_users: List[int] = None):
        """
        初始化游戏机器人

        Args:
            ws_url: WebSocket连接地址
            allowed_groups: 允许的群号列表，None表示允许所有群
            admin_users: 管理员用户列表
        """
        self.ws_url = ws_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

        # 游戏服务
        self.game_service = GameService()
        self.message_processor = MessageProcessor()
        self.message_adapter = QQMessageAdapter()

        # 权限控制
        self.allowed_groups = set(allowed_groups) if allowed_groups else None
        self.admin_users = set(admin_users) if admin_users else set()

        # 用户管理
        self.user_info: Dict[int, QQUserInfo] = {}
        self.user_sessions: Dict[int, str] = {}  # user_id -> session_id

        # 状态管理
        self.running = False

        # 日志
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/lagrange_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def _extract_message_text(self, message_data) -> str:
        """
        从消息数据中提取文本内容 - 针对dict格式优化

        Args:
            message_data: 可能是字符串、字典或列表格式的消息数据

        Returns:
            提取的文本内容
        """
        try:
            if isinstance(message_data, dict):
                # 优先处理dict格式 - 单个CQ码或其他dict结构
                if message_data.get("type") == "text":
                    return message_data.get("data", {}).get("text", "").strip()
                else:
                    # 如果dict中没有type字段或不是text类型，可能是其他格式
                    # 尝试直接获取text字段或其他可能的文本字段
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
                        elif segment.get("type") == "at":
                            # @某人，可以忽略或保留
                            qq = segment.get("data", {}).get("qq", "")
                            if qq != "all":  # 忽略@全体成员
                                continue
                    elif isinstance(segment, str):
                        text_parts.append(segment)

                return " ".join(text_parts).strip()

            else:
                # 其他格式，尝试转换为字符串
                return str(message_data).strip()

        except Exception as e:
            self.logger.warning(f"⚠️ 解析消息格式失败: {e}, 原始数据: {message_data}")
            return str(message_data) if message_data else ""

    async def connect(self) -> None:
        """建立WebSocket连接"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            self.logger.info("✅ 已连接到 Lagrange.OneBot")
            self.running = True
        except Exception as e:
            self.logger.error(f"❌ 连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.logger.info("🔌 已断开连接")

    async def send_group_msg(self, group_id: int, message: str) -> Dict[str, Any]:
        """
        发送群消息

        Args:
            group_id: 群号
            message: 消息内容

        Returns:
            API响应结果
        """
        if not self.ws:
            raise ConnectionError("WebSocket未连接")

        payload = {
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": message
            }
        }

        try:
            await self.ws.send(json.dumps(payload))
            response = await self.ws.recv()
            result = json.loads(response)

            if result.get("status") == "ok":
                self.logger.debug(f"📤 发送群消息成功: {group_id}")
            else:
                self.logger.warning(f"⚠️ 发送消息可能失败: {result}")

            return result
        except Exception as e:
            self.logger.error(f"❌ 发送群消息失败: {e}")
            return {"status": "failed", "error": str(e)}

    async def send_private_msg(self, user_id: int, message: str) -> Dict[str, Any]:
        """
        发送私聊消息

        Args:
            user_id: 用户QQ号
            message: 消息内容

        Returns:
            API响应结果
        """
        if not self.ws:
            raise ConnectionError("WebSocket未连接")

        payload = {
            "action": "send_private_msg",
            "params": {
                "user_id": user_id,
                "message": message
            }
        }

        try:
            await self.ws.send(json.dumps(payload))
            response = await self.ws.recv()
            result = json.loads(response)

            if result.get("status") == "ok":
                self.logger.debug(f"📤 发送私聊消息成功: {user_id}")
            else:
                self.logger.warning(f"⚠️ 发送消息可能失败: {result}")

            return result
        except Exception as e:
            self.logger.error(f"❌ 发送私聊消息失败: {e}")
            return {"status": "failed", "error": str(e)}

    async def handle_group_message(self, data: Dict[str, Any]) -> None:
        """处理群消息"""
        group_id = data["group_id"]
        user_id = data["user_id"]
        message = self._extract_message_text(data["message"])
        sender = data.get("sender", {})

        # 检查群权限
        if self.allowed_groups and group_id not in self.allowed_groups:
            return

        # 忽略空消息
        if not message:
            return

        # 更新用户信息
        self.user_info[user_id] = QQUserInfo(
            user_id=user_id,
            nickname=sender.get("nickname", f"用户{user_id}"),
            group_id=group_id,
            card=sender.get("card", "")
        )

        self.logger.info(f"📩 群 {group_id} | {self.user_info[user_id].nickname}({user_id}): {message}")

        try:
            # 处理游戏指令
            await self.process_game_command(user_id, message, group_id)
        except Exception as e:
            self.logger.error(f"❌ 处理群消息失败: {e}")
            error_msg = f"[CQ:at,qq={user_id}] ❌ 处理指令时发生错误: {str(e)}"
            await self.send_group_msg(group_id, error_msg)

    async def handle_private_message(self, data: Dict[str, Any]) -> None:
        """处理私聊消息"""
        user_id = data["user_id"]
        message = self._extract_message_text(data["message"])
        sender = data.get("sender", {})

        # 忽略空消息
        if not message:
            return

        # 更新用户信息
        self.user_info[user_id] = QQUserInfo(
            user_id=user_id,
            nickname=sender.get("nickname", f"用户{user_id}")
        )

        self.logger.info(f"📩 私聊 | {self.user_info[user_id].nickname}({user_id}): {message}")

        try:
            # 处理游戏指令
            await self.process_game_command(user_id, message)
        except Exception as e:
            self.logger.error(f"❌ 处理私聊消息失败: {e}")
            await self.send_private_msg(user_id, f"❌ 处理指令时发生错误: {str(e)}")

    async def process_game_command(self, user_id: int, message: str, group_id: int = None) -> None:
        """处理游戏指令"""
        user_id_str = str(user_id)
        user_info = self.user_info.get(user_id)

        # 确保用户在游戏系统中存在
        is_new_user = await self.ensure_player_exists(user_id_str, user_info.nickname if user_info else f"用户{user_id}")

        # 新用户首次使用，显示阵营选择提示
        if is_new_user and not message.startswith("选择阵营"):
            welcome_msg = f"""🎮 欢迎来到 CantStop贪骰无厌！

👋 {user_info.nickname if user_info else f"用户{user_id}"}，您已自动注册为"收养人"阵营

🎯 您可以使用以下指令选择阵营：
• 选择阵营：收养人
• 选择阵营：Aonreth

ℹ️ 选择阵营后，输入"轮次开始"开始游戏
或输入"help"查看完整指令列表"""
            await self.send_response(user_id, welcome_msg, group_id)
            return

        # 处理特殊指令
        if message.lower() == "help" or message == "帮助":
            response = self.message_adapter.format_help_message()
            await self.send_response(user_id, response, group_id)
            return

        # 管理员指令
        if user_id in self.admin_users and message.startswith("admin_"):
            await self.handle_admin_command(user_id, message, group_id)
            return

        try:
            # 获取用户昵称
            username = user_info.nickname if user_info else f"用户{user_id}"

            # 创建UserMessage对象
            user_message = UserMessage(
                user_id=user_id_str,
                username=username,
                content=message,
                group_id=str(group_id) if group_id else None,
                timestamp=datetime.now().isoformat()
            )

            # 使用消息处理器处理游戏指令
            response = await self.message_processor.process_message_async(user_message)

            # 判断处理是否成功
            success = response is not None and response.content is not None

            if response and response.content:
                # 使用消息适配器格式化响应
                formatted_response = self.message_adapter.adapt_message(response.content, user_id_str, "game")
                await self.send_response(user_id, formatted_response, group_id)

            # 发布游戏事件
            event_type = GameEventType.DICE_ROLLED if '.r6d6' in message else GameEventType.TURN_STARTED
            emit_game_event(event_type, user_id_str, {
                "command": message,
                "success": success,
                "group_id": group_id
            })

        except Exception as e:
            self.logger.error(f"❌ 处理游戏指令失败: {e}")
            await self.send_response(user_id, f"❌ 处理指令失败: {str(e)}", group_id)

    async def handle_admin_command(self, user_id: int, message: str, group_id: int = None) -> None:
        """处理管理员指令"""
        command = message[6:]  # 移除 "admin_" 前缀

        if command == "status":
            status_msg = f"""🤖 机器人状态
在线用户: {len(self.user_info)}
允许群组: {len(self.allowed_groups) if self.allowed_groups else '无限制'}
管理员数: {len(self.admin_users)}
运行状态: {'正常' if self.running else '异常'}"""
            await self.send_response(user_id, status_msg, group_id)

        elif command == "users":
            users_list = []
            for uid, info in self.user_info.items():
                users_list.append(f"{info.nickname}({uid})")

            users_msg = f"📋 在线用户列表 ({len(users_list)}):\n" + "\n".join(users_list[:20])
            if len(users_list) > 20:
                users_msg += f"\n... 还有 {len(users_list) - 20} 个用户"

            await self.send_response(user_id, users_msg, group_id)

        elif command.startswith("broadcast "):
            broadcast_msg = command[10:]
            await self.broadcast_message(broadcast_msg)
            await self.send_response(user_id, "✅ 广播消息已发送", group_id)

        else:
            await self.send_response(user_id, "❌ 未知管理员指令", group_id)

    async def ensure_player_exists(self, user_id: str, nickname: str) -> bool:
        """确保玩家在游戏系统中存在，返回是否为新用户"""
        player = self.game_service.db.get_player(user_id)
        if not player:
            # 自动注册新玩家
            success, message = self.game_service.register_player(user_id, nickname, "收养人")
            if success:
                self.logger.info(f"✅ 自动注册新玩家: {nickname}({user_id})")
                return True  # 新用户
            else:
                self.logger.warning(f"⚠️ 自动注册玩家失败: {message}")
                return False
        return False  # 已存在的用户

    async def send_response(self, user_id: int, message: str, group_id: int = None) -> None:
        """发送响应消息"""
        if group_id:
            # 在群消息中添加@用户
            at_user = f"[CQ:at,qq={user_id}] "
            message_with_at = at_user + message
            await self.send_group_msg(group_id, message_with_at)
        else:
            # 私聊消息不需要@
            await self.send_private_msg(user_id, message)

    async def broadcast_message(self, message: str) -> None:
        """向所有活跃群广播消息"""
        if not self.allowed_groups:
            return

        for group_id in self.allowed_groups:
            try:
                await self.send_group_msg(group_id, f"📢 系统广播: {message}")
                await asyncio.sleep(0.5)  # 避免发送过快
            except Exception as e:
                self.logger.error(f"❌ 广播到群 {group_id} 失败: {e}")

    async def handle_group_notice(self, data: Dict[str, Any]) -> None:
        """处理群通知事件"""
        notice_type = data.get("notice_type")
        group_id = data.get("group_id")

        if notice_type == "group_increase":
            # 新成员加群
            user_id = data.get("user_id")
            if self.allowed_groups and group_id in self.allowed_groups:
                welcome_msg = self.message_adapter.format_welcome_message(f"用户{user_id}")
                at_user = f"[CQ:at,qq={user_id}] "
                welcome_msg_with_at = at_user + welcome_msg
                await self.send_group_msg(group_id, welcome_msg_with_at)

        elif notice_type == "group_decrease":
            # 成员离群
            user_id = data.get("user_id")
            if user_id in self.user_info:
                del self.user_info[user_id]
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

    async def listen_messages(self) -> None:
        """监听并处理消息"""
        if not self.ws:
            raise ConnectionError("WebSocket未连接")

        self.logger.info("🎧 开始监听消息...")

        try:
            async for message in self.ws:
                if not self.running:
                    break

                try:
                    data = json.loads(message)
                    post_type = data.get("post_type")

                    if post_type == "message":
                        message_type = data.get("message_type")

                        if message_type == "group":
                            await self.handle_group_message(data)
                        elif message_type == "private":
                            await self.handle_private_message(data)

                    elif post_type == "notice":
                        await self.handle_group_notice(data)

                    elif post_type == "meta_event":
                        # 处理元事件（心跳等）
                        meta_event_type = data.get("meta_event_type")
                        if meta_event_type == "heartbeat":
                            self.logger.debug("💓 收到心跳")

                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ 无法解析消息: {message}")
                except Exception as e:
                    self.logger.error(f"❌ 处理消息失败: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("🔌 WebSocket连接已关闭")
        except Exception as e:
            self.logger.error(f"❌ 监听消息失败: {e}")
        finally:
            self.running = False

    async def run(self) -> None:
        """运行机器人"""
        try:
            await self.connect()

            # 发送启动通知（如果有允许的群）
            if self.allowed_groups:
                startup_msg = "🤖 CantStop游戏机器人已启动！\n输入 'help' 查看游戏指令"
                for group_id in list(self.allowed_groups)[:3]:  # 最多通知3个群
                    try:
                        # await self.send_group_msg(group_id, startup_msg)
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.logger.warning(f"⚠️ 发送启动通知失败: {e}")

            # 开始监听
            await self.listen_messages()

        except KeyboardInterrupt:
            self.logger.info("⏹️ 用户中断，正在关闭...")
        except Exception as e:
            self.logger.error(f"❌ 运行错误: {e}")
        finally:
            await self.disconnect()

    def add_allowed_group(self, group_id: int) -> None:
        """添加允许的群"""
        if self.allowed_groups is None:
            self.allowed_groups = set()
        self.allowed_groups.add(group_id)

    def add_admin_user(self, user_id: int) -> None:
        """添加管理员用户"""
        self.admin_users.add(user_id)

    def get_user_count(self) -> int:
        """获取在线用户数"""
        return len(self.user_info)

    def get_group_count(self) -> int:
        """获取允许的群数量"""
        return len(self.allowed_groups) if self.allowed_groups else 0


async def main():
    """主函数 - 示例使用"""
    # 创建机器人实例
    bot = CantStopLagrangeBot(
        ws_url="ws://127.0.0.1:8080/onebot/v11/ws",
        allowed_groups=[541674420],  # 你的测试群号
        admin_users=[1234567890]     # 你的QQ号
    )

    # 运行机器人
    await bot.run()


if __name__ == "__main__":
    # 创建日志目录
    import os
    os.makedirs("logs", exist_ok=True)

    # 运行机器人
    asyncio.run(main())