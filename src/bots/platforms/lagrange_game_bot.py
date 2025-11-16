"""
基于LagrangeBot API的CantStop游戏机器人
使用专业的API库实现消息监听、发送、@、图片等功能
"""

import asyncio
from typing import List, Optional
from datetime import datetime
import logging

from ..api.apis import LagrangeBot, GroupMessage, PrivateMessage, MessageBuilder
from ...services.game_service import GameService
from ...services.message_processor import MessageProcessor, UserMessage
from ...core.event_system import emit_game_event, GameEventType
from ..adapters.qq_message_adapter import QQMessageAdapter, MessageStyle


class CantStopGameBot:
    """CantStop游戏机器人 - 基于LagrangeBot API"""

    def __init__(
        self,
        ws_url: str = "ws://127.0.0.2:8081",
        access_token: Optional[str] = None,
        allowed_groups: Optional[List[int]] = None,
        admin_users: Optional[List[int]] = None,
        enable_log: bool = True
    ):
        """
        初始化游戏机器人

        Args:
            ws_url: WebSocket连接地址
            access_token: 访问令牌（可选）
            allowed_groups: 允许的群号列表，None表示允许所有群
            admin_users: 管理员用户列表
            enable_log: 是否启用日志
        """
        # 创建底层Bot实例
        self.bot = LagrangeBot(
            ws_url=ws_url,
            access_token=access_token,
            allowed_groups=allowed_groups,
            enable_log=enable_log
        )

        # 游戏服务
        self.game_service = GameService()
        self.message_processor = MessageProcessor()
        self.message_adapter = QQMessageAdapter()

        # 权限控制
        self.admin_users = set(admin_users) if admin_users else set()

        # 设置日志
        self.logger = logging.getLogger(__name__)
        if enable_log:
            self._setup_logging()

        # 注册消息处理器
        self._setup_handlers()

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )

    def _setup_handlers(self):
        """设置消息处理器"""
        # 注册群消息处理器
        @self.bot.on_group_message
        async def handle_group_message(msg: GroupMessage):
            await self._handle_group_message(msg)

        # 注册私聊消息处理器
        @self.bot.on_private_message
        async def handle_private_message(msg: PrivateMessage):
            await self._handle_private_message(msg)

    async def _handle_group_message(self, msg: GroupMessage):
        """处理群消息"""
        try:
            # 记录所有消息（用于完整监听）
            self.logger.info(f"[MSG] 群 {msg.group_id} | {msg.sender_nickname}({msg.user_id}): {msg.plain_text}")

            # 检查是否包含@信息
            if hasattr(msg, 'at_users') and msg.at_users:
                # 构建@用户详细信息
                at_details = []
                for at_user in msg.at_users:
                    if isinstance(at_user, dict):
                        # 如果at_user是字典，包含昵称和ID信息
                        nickname = at_user.get('nickname', 'Unknown')
                        user_id = at_user.get('user_id', at_user.get('qq', 'Unknown'))
                        at_details.append(f"{nickname}({user_id})")
                    else:
                        # 如果只是ID
                        at_details.append(str(at_user))

                at_info = f"[@{', '.join(at_details)}]"
                self.logger.info(f"[AT] 群 {msg.group_id} | {msg.sender_nickname}({msg.user_id}) {at_info}: {msg.plain_text}")

            # 检查是否包含图片（已禁用）
            # if self._has_image(msg):
            #     self.logger.info(f"[IMG] 群 {msg.group_id} | {msg.sender_nickname}({msg.user_id}) 发送了图片: {msg.plain_text}")

            # 检查是否需要响应
            should_respond = self._should_respond_to_group_message(msg)
            if not should_respond:
                self.logger.info(f"[SKIP] 群 {msg.group_id} | {msg.sender_nickname}({msg.user_id}): 消息不需要响应")
                return

            # 处理图片消息（已禁用）
            # if self._has_image(msg) and not msg.plain_text.strip():
            #     # 纯图片消息，提示奖励选择
            #     response_text = (
            #         "收到您的图片！\n\n"
            #         "请使用以下指令领取对应奖励：\n"
            #         "• 领取草图奖励 - 草图作品(+20积分)\n"
            #         "• 领取精致小图奖励 - 精致小图(+80积分)\n"
            #         "• 领取精致大图奖励 - 精致大图(+150积分)"
            #     )
            #     await self._send_group_response(msg, response_text)
            #     return

            # 处理游戏指令
            self.logger.info(f"[GAME] 群 {msg.group_id} | {msg.sender_nickname}({msg.user_id}): 开始处理游戏指令: {msg.plain_text}")
            await self._process_game_command(msg.user_id, msg.plain_text, msg.group_id)

        except Exception as e:
            self.logger.error(f"[ERROR] 处理群消息失败: {e}")
            # 只有在@机器人时才回复错误（图片处理已禁用）
            if msg.is_at_bot:  # 移除了 or self._has_image(msg)
                await self._send_group_response(msg, f"[ERROR] 处理指令时发生错误: {str(e)}")

    async def _handle_private_message(self, msg: PrivateMessage):
        """处理私聊消息"""
        try:
            # 记录私聊消息
            self.logger.info(f"[PRIVATE] {msg.sender_nickname}({msg.user_id}): {msg.plain_text}")

            # 私聊消息默认都会响应
            await self._process_game_command(msg.user_id, msg.plain_text, None)
        except Exception as e:
            self.logger.error(f"[ERROR] 处理私聊消息失败: {e}")
            await self.bot.send_private_msg(msg.user_id, f"[ERROR] 处理指令时发生错误: {str(e)}")

    def _should_respond_to_group_message(self, msg: GroupMessage) -> bool:
        """判断是否应该响应群消息"""
        # 1. @机器人
        if msg.is_at_bot:
            return True

        # 2. 包含图片（已禁用）
        # if self._has_image(msg):
        #     return True

        # 3. 看起来像游戏指令的消息
        game_keywords = [
            "轮次开始", "r6d6", "选择数值", "替换永久", "继续", "打卡完毕",
            "查看当前进度", "help", "帮助", "选择阵营", "领取", "排行榜",
            "选择", "数值", "骰子", "重投", "登顶", "我超级满意",  # 添加登顶和满意关键词
            "道具商店", "查看库存", "我的道具", "背包", "查看背包",  # 库存相关
            "购买", "捏捏", "使用", "查看成就", "恢复游戏"  # 道具和其他指令
        ]

        # 检查是否包含数字组合（优先级更高）
        import re
        if re.match(r'^\s*\d+\s*(,\s*\d+)?\s*$', msg.plain_text.strip()):
            return True

        # 检查登顶确认模式：数列X登顶
        if re.match(r'^数列\d+登顶$', msg.plain_text.strip()):
            return True

        # 检查是否是编号选项格式（如 "1. 好呀好呀"）
        if re.match(r'^\s*\d+\.\s*.+', msg.plain_text.strip()):
            return True

        # 检查是否包含常见的遭遇/道具选择关键词
        choice_keywords = [
            # 同意/拒绝类
            "好呀", "还是算了", "好啊", "好", "不了", "谢谢", "参加", "不参加",
            # 动作类
            "继续", "休息", "靠近", "逃跑", "帮忙", "不帮", "观看", "绕过",
            "看看", "过去", "未来", "听故事", "不听", "借书", "不借", "加入",
            "戴上", "不戴", "走了", "走开", "前进", "仔细",
            # 触摸/互动类
            "摸摸", "敲敲", "浇水", "数羊", "吐槽", "夸赞", "尝试", "修复",
            # 选择类
            "红色", "蓝色", "甜的", "辣的", "吓死", "申请", "想要",
            # 特殊选项
            "321", "啊啊", "仔细观赏", "静静", "快速", "慢慢", "深度"
        ]

        # 先检查游戏关键词
        if any(keyword in msg.plain_text for keyword in game_keywords):
            return True

        # 如果消息很短（可能是选项回复），检查选择关键词
        if len(msg.plain_text.strip()) <= 20:
            return any(keyword in msg.plain_text for keyword in choice_keywords)

        return False

    def _has_image(self, msg: GroupMessage) -> bool:
        """检查消息是否包含图片"""
        return any(
            segment.get("type") == "image"
            for segment in msg.message_array
        )

    async def _process_game_command(self, user_id: int, message: str, group_id: Optional[int] = None):
        """处理游戏指令"""
        user_id_str = str(user_id)

        # 确保用户在游戏系统中存在
        is_new_user = await self._ensure_player_exists(user_id_str, f"用户{user_id}")

        # 新用户首次使用，显示阵营选择提示
        if is_new_user and not message.startswith("选择阵营"):
            welcome_msg = (
                f"欢迎来到 CantStop贪骰无厌！\n\n"
                f"用户{user_id}，您已自动注册为\"收养人\"阵营\n\n"
                f"您可以使用以下指令选择阵营：\n"
                f"• 选择阵营：收养人\n"
                f"• 选择阵营：Aeonreth\n\n"
                f"选择阵营后，输入\"轮次开始\"开始游戏\n"
                f"或输入\"help\"查看完整指令列表"
            )
            if group_id:
                await self._send_group_at_response(user_id, welcome_msg, group_id)
            else:
                await self.bot.send_private_msg(user_id, welcome_msg)
            return

        # 处理特殊指令
        if message.lower() == "help" or message == "帮助":
            response = self.message_adapter.format_help_message()
            if group_id:
                await self._send_group_at_response(user_id, response, group_id)
            else:
                await self.bot.send_private_msg(user_id, response)
            return

        # 管理员指令
        if user_id in self.admin_users and message.startswith("admin_"):
            await self._handle_admin_command(user_id, message, group_id)
            return

        try:
            # 创建UserMessage对象
            user_message = UserMessage(
                user_id=user_id_str,
                username=f"用户{user_id}",
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
                formatted_response = self.message_adapter.adapt_message(
                    response.content, user_id_str, "game"
                )

                if group_id:
                    await self._send_group_at_response(user_id, formatted_response, group_id)
                else:
                    await self.bot.send_private_msg(user_id, formatted_response)

            # 发布游戏事件
            event_type = GameEventType.DICE_ROLLED if '.r6d6' in message else GameEventType.TURN_STARTED
            emit_game_event(event_type, user_id_str, {
                "command": message,
                "success": success,
                "group_id": group_id
            })

        except Exception as e:
            self.logger.error(f"[ERROR] 处理游戏指令失败: {e}")
            error_msg = f"[ERROR] 处理指令失败: {str(e)}"
            if group_id:
                await self._send_group_at_response(user_id, error_msg, group_id)
            else:
                await self.bot.send_private_msg(user_id, error_msg)

    async def _handle_admin_command(self, user_id: int, message: str, group_id: Optional[int] = None):
        """处理管理员指令"""
        command = message[6:]  # 移除 "admin_" 前缀

        if command == "status":
            status_msg = (
                f"机器人状态\n"
                f"Bot QQ: {self.bot.bot_qq}\n"
                f"允许群组: {len(self.bot.allowed_groups) if self.bot.allowed_groups else '无限制'}\n"
                f"管理员数: {len(self.admin_users)}\n"
                f"运行状态: {'正常' if self.bot.is_connected() else '异常'}"
            )
            if group_id:
                await self._send_group_at_response(user_id, status_msg, group_id)
            else:
                await self.bot.send_private_msg(user_id, status_msg)

        elif command.startswith("broadcast "):
            broadcast_msg = command[10:]
            await self._broadcast_message(broadcast_msg)
            response_msg = "[OK] 广播消息已发送"
            if group_id:
                await self._send_group_at_response(user_id, response_msg, group_id)
            else:
                await self.bot.send_private_msg(user_id, response_msg)

        else:
            error_msg = "[ERROR] 未知管理员指令"
            if group_id:
                await self._send_group_at_response(user_id, error_msg, group_id)
            else:
                await self.bot.send_private_msg(user_id, error_msg)

    async def _ensure_player_exists(self, user_id: str, nickname: str) -> bool:
        """确保玩家在游戏系统中存在，返回是否为新用户"""
        player = self.game_service.db.get_player(user_id)
        if not player:
            # 自动注册新玩家
            success, message = self.game_service.register_player(user_id, nickname, "收养人")
            if success:
                self.logger.info(f"[INFO] 自动注册新玩家: {nickname}({user_id})")
                return True  # 新用户
            else:
                self.logger.warning(f"[WARNING] 自动注册玩家失败: {message}")
                return False
        return False  # 已存在的用户

    async def _send_group_response(self, msg: GroupMessage, text: str):
        """发送群响应消息"""
        await self.bot.send_group_msg(msg.group_id, text)

    async def _send_group_at_response(self, user_id: int, text: str, group_id: int):
        """发送@用户的群响应消息"""
        message = MessageBuilder().at(user_id).text(f" {text}")
        await self.bot.send_group_msg(group_id, message)

    async def _broadcast_message(self, message: str):
        """向所有允许的群广播消息"""
        if not self.bot.allowed_groups:
            return

        for group_id in self.bot.allowed_groups:
            try:
                await self.bot.send_group_msg(group_id, f"[BROADCAST] 系统广播: {message}")
                await asyncio.sleep(0.5)  # 避免发送过快
            except Exception as e:
                self.logger.error(f"[ERROR] 广播到群 {group_id} 失败: {e}")

    # ==================== 外部接口 ====================

    async def connect(self):
        """连接到WebSocket"""
        await self.bot.connect()

    async def disconnect(self):
        """断开连接"""
        await self.bot.disconnect()

    async def start(self):
        """启动机器人（连接并开始监听）"""
        await self.bot.start()

    async def stop(self):
        """停止机器人"""
        await self.bot.stop()

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.bot.is_connected()

    def add_allowed_group(self, group_id: int):
        """添加允许的群"""
        if self.bot.allowed_groups is None:
            self.bot.allowed_groups = []
        self.bot.allowed_groups.append(group_id)

    def add_admin_user(self, user_id: int):
        """添加管理员用户"""
        self.admin_users.add(user_id)

    @property
    def bot_qq(self) -> Optional[int]:
        """获取机器人QQ号"""
        return self.bot.bot_qq


async def main():
    """主函数 - 示例使用"""
    import os
    os.makedirs("logs", exist_ok=True)

    # 创建机器人实例
    bot = CantStopGameBot(
        ws_url="ws://127.0.0.1:8080",

        admin_users=[1234567890],    # 你的QQ号
        enable_log=True
    )

    try:
        # 启动机器人
        await bot.start()
    except KeyboardInterrupt:
        print("\n👋 正在停止机器人...")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())