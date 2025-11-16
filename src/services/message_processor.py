"""
消息处理框架 - 用于QQ机器人集成
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

from .game_service import GameService


class MessageType(Enum):
    """消息类型"""
    COMMAND = "command"
    GAME_ACTION = "game_action"
    SCORE_REWARD = "score_reward"
    QUERY = "query"
    UNKNOWN = "unknown"


@dataclass
class UserMessage:
    """用户消息数据结构"""
    user_id: str
    username: str
    content: str
    group_id: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class BotResponse:
    """机器人响应数据结构"""
    content: str
    message_type: MessageType = MessageType.UNKNOWN
    should_mention: bool = False
    additional_data: Optional[Dict] = None


class MessageProcessor:
    """消息处理器"""

    def __init__(self):
        self.game_service = GameService()
        self.command_handlers: Dict[str, Callable] = {}
        self.pattern_handlers: List[Tuple[str, Callable]] = []
        self.logger = logging.getLogger(__name__)
        self._init_handlers()

    def _init_handlers(self):
        """初始化消息处理器"""
        # 注册命令处理器
        self.command_handlers.update({
            # 阵营选择
            "选择阵营": self._handle_faction_selection,

            # 游戏流程
            "轮次开始": self._handle_start_turn,
            "掷骰": self._handle_roll_dice,
            ".r6d6": self._handle_roll_dice,
            "重投": self._handle_reroll_dice,
            "替换永久棋子": self._handle_end_turn,
            "查看当前进度": self._handle_get_status,
            "打卡完毕": self._handle_complete_checkin,

            # 积分奖励（图片奖励已禁用）
            # "领取草图奖励": lambda msg: self._handle_add_score(msg, "草图"),
            # "领取精致小图奖励": lambda msg: self._handle_add_score(msg, "精致小图"),
            # "领取精草大图奖励": lambda msg: self._handle_add_score(msg, "精草大图"),
            # "领取精致大图奖励": lambda msg: self._handle_add_score(msg, "精致大图"),

            # 商店系统
            "道具商店": self._handle_shop,
            "查看库存": self._handle_inventory,
            "我的道具": self._handle_inventory,
            "背包": self._handle_inventory,
            "查看背包": self._handle_inventory,  # 新增：查看背包命令
            "购买丑喵玩偶": self._handle_buy_item,
            "捏捏丑喵玩偶": self._handle_use_item,

            # 陷阱选择 - 河..土地神
            "都是我掉的": self._handle_trap_choice,
            "金骰子": self._handle_trap_choice,
            "银骰子": self._handle_trap_choice,
            "普通d6骰子": self._handle_trap_choice,
            "我没掉": self._handle_trap_choice,

            # 花言巧语陷阱相关
            "玩家列表": self._handle_player_list,
            "投掷抵消": self._handle_penalty_resistance,

            # 玩家切换
            "切换玩家": self._handle_switch_player_prompt,

            # 查询功能
            "排行榜": self._handle_leaderboard,
            "帮助": self._handle_help,
            "help": self._handle_help,
            "成就一览": self._handle_achievements,
            "我的成就": self._handle_achievements,

            # 失败处理
            "进度回退": self._handle_progress_retreat,

            # 遭遇事件选项 - 根据encounters.json的所有选项
            "吓死我了": self._handle_encounter_choice,
            "摸摸猫": self._handle_encounter_choice,
            "静静看它走过去": self._handle_encounter_choice,
            "绕过去": self._handle_encounter_choice,
            "直接过去": self._handle_encounter_choice,
            "靠近小花": self._handle_encounter_choice,
            "浇水": self._handle_encounter_choice,
            "我没兴趣": self._handle_encounter_choice,
            "晃得头晕，走了": self._handle_encounter_choice,
            "靠近查看": self._handle_encounter_choice,
            "我要申请更多骰子": self._handle_encounter_choice,
            "仔细观察塞过来的骰子": self._handle_encounter_choice,
            "好呀好呀": self._handle_encounter_choice,
            "还是算了": self._handle_encounter_choice,
            "啊啊啊啊啊": self._handle_encounter_choice,
            "小钱钱！赶快捡钱！": self._handle_encounter_choice,
            "先不管钱了！靠近丝塔茜！": self._handle_encounter_choice,
            "321跳": self._handle_encounter_choice,
            "过去": self._handle_encounter_choice,
            "未来": self._handle_encounter_choice,
            # 神奇小药丸
            "红色": self._handle_encounter_choice,
            "蓝色": self._handle_encounter_choice,
            "我想要黑色的": self._handle_encounter_choice,
            "不用了，谢谢": self._handle_encounter_choice,
            # 积木
            "好": self._handle_encounter_choice,
            "不了": self._handle_encounter_choice,
            # 自助问答
            "敲敲头": self._handle_encounter_choice,
            "摸摸肚子": self._handle_encounter_choice,
            # 人才市场
            "好啊": self._handle_encounter_choice,
            "薪资太少了，我不干": self._handle_encounter_choice,
            # 房产中介
            "看看": self._handle_encounter_choice,
            "太贵了": self._handle_encounter_choice,
            # 奇异的菜肴
            "甜的": self._handle_encounter_choice,
            "辣的": self._handle_encounter_choice,
            "不用了": self._handle_encounter_choice,
            # 钓鱼大赛
            "参加": self._handle_encounter_choice,
            "不参加": self._handle_encounter_choice,
            # 广场舞
            "加入他们": self._handle_encounter_choice,
            "观看": self._handle_encounter_choice,
            # 面具
            "戴上": self._handle_encounter_choice,
            "不戴": self._handle_encounter_choice,
            # 清理大师
            "帮忙": self._handle_encounter_choice,
            "不帮": self._handle_encounter_choice,
            # 饥寒交迫 & 循环往复
            "继续前进": self._handle_encounter_choice,
            "休息一会": self._handle_encounter_choice,
            # 谁要走
            "我要走": self._handle_encounter_choice,
            "我不走": self._handle_encounter_choice,
            # 我吗
            "靠近": self._handle_encounter_choice,
            "逃跑": self._handle_encounter_choice,
            # 薯片邀请
            "不了，谢谢": self._handle_encounter_choice,
            # AeAe少女
            "积分": self._handle_encounter_choice,
            "道具": self._handle_encounter_choice,
            "什么都不要": self._handle_encounter_choice,
            # 魔女的藏书室
            "借书": self._handle_encounter_choice,
            "不借": self._handle_encounter_choice,
            # 一千零一
            "听故事": self._handle_encounter_choice,
            "不听": self._handle_encounter_choice,
            # 循环往复
            "原地休息": self._handle_encounter_choice,
            # 回廊
            "快速通过": self._handle_encounter_choice,
            "慢慢走": self._handle_encounter_choice,
            # 天下无程序员
            "帮他debug": self._handle_encounter_choice,
            "默默走开": self._handle_encounter_choice,
            # 美术馆系列
            "仔细欣赏": self._handle_encounter_choice,
            "继续参观": self._handle_encounter_choice,
            "数羊": self._handle_encounter_choice,
            "静静凝视": self._handle_encounter_choice,
            "深度欣赏": self._handle_encounter_choice,
            "吐槽后期": self._handle_encounter_choice,
            "夸赞后期": self._handle_encounter_choice,
            "走进画中": self._handle_encounter_choice,
            "尝试修复": self._handle_encounter_choice,
            # Follow-up响应
            "谢谢财神": self._handle_encounter_follow_up,
        })

        # 注册模式处理器
        self.pattern_handlers.extend([
            # 登顶确认（必须在数字组合之前匹配）
            (r"^数列(\d+)登顶$", self._handle_summit_confirmation),

            # 阵营选择：xxx
            (r"选择阵营：(.+)", self._handle_faction_selection_with_param),

            # 数值组合 (8,13 或 单个数字) - 允许前后有空格
            (r"^\s*(\d+)\s*,\s*(\d+)\s*$", self._handle_move_two_markers),
            (r"^\s*(\d+)\s*$", self._handle_move_one_marker),

            # 超常发挥奖励（支持倍数）
            (r"我超级满意这张图(\d+)", self._handle_super_satisfied),

            # 领取奖励
            (r"领取(.+)奖励(\d+)\*2", self._handle_reward_doubled),
            (r"领取(.+)奖励(\d+)", self._handle_reward_with_number),

            # 道具操作
            (r"购买(.+)", self._handle_buy_specific_item),
            (r"使用(.+)", self._handle_use_specific_item),
            (r"添加(.+)到道具商店", self._handle_add_item_to_shop),

            # 花言巧语玩家选择
            (r"^选择玩家(\d+)$", self._handle_select_player_for_penalty),

            # 玩家切换
            (r"^切换到(.+)$", self._handle_switch_to_player),

            # 带点号的陷阱选择模式（如 "1. 都是我掉的"、"5. 我没掉"）
            (r"^([1-5])\.\s*(.+)$", self._handle_numbered_trap_choice),
        ])

    def process_message(self, user_id: str, message: str) -> Tuple[bool, Optional[str]]:
        """同步处理消息的包装器"""
        import asyncio
        try:
            # 创建 UserMessage 对象
            user_message = UserMessage(user_id=user_id, username="", content=message)

            # 在事件循环中运行异步方法
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            response = loop.run_until_complete(self.process_message_async(user_message))

            # 如果返回None，表示不做任何反应
            if response is None:
                return True, None

            return True, response.content
        except Exception as e:
            return False, f"处理消息时发生错误: {str(e)}"

    async def process_message_async(self, message: UserMessage) -> Optional[BotResponse]:
        """异步处理消息"""
        try:
            content = message.content.strip()

            # 定义不需要游戏状态的命令（任何人都可以执行）
            public_commands = {
                "选择阵营", "help", "排行榜", "查看成就一览",
                "道具商店", "查看库存", "我的道具", "背包", "查看背包"
            }

            # 定义需要玩家注册但不需要活跃游戏会话的命令
            registered_commands = public_commands | {
                "轮次开始", "开始新轮次", "恢复游戏"
            }

            # 检查是否是公共命令或匹配公共命令模式
            is_public_command = content in public_commands
            is_registered_command = content in registered_commands

            # 如果不是公共命令，检查玩家是否已注册
            if not is_public_command:
                player = self.game_service.db.get_player(message.user_id)
                if not player:
                    return BotResponse(
                        content="请先使用 \"选择阵营：收养人\" 或 \"选择阵营：Aeonreth\" 注册玩家",
                        message_type=MessageType.COMMAND,
                        should_mention=True
                    )

                # 如果不是仅需注册的命令，检查是否有活跃游戏会话
                if not is_registered_command:
                    session = self.game_service.db.get_player_active_session(message.user_id)
                    if not session:
                        return BotResponse(
                            content="你当前没有进行中的游戏，请先使用 \"轮次开始\" 命令开始游戏",
                            message_type=MessageType.COMMAND,
                            should_mention=True
                        )

            # 尝试命令匹配
            if content in self.command_handlers:
                return await self._execute_handler(self.command_handlers[content], message)

            # 尝试模式匹配
            for pattern, handler in self.pattern_handlers:
                match = re.match(pattern, content)
                if match:
                    return await self._execute_handler(handler, message, match)

            # 未匹配的消息 - 不做任何反应
            return None

        except Exception as e:
            return BotResponse(
                content=f"处理消息时发生错误：{str(e)}",
                message_type=MessageType.UNKNOWN
            )

    async def _execute_handler(self, handler: Callable, message: UserMessage, match: Optional[re.Match] = None) -> BotResponse:
        """执行处理器"""
        try:
            if asyncio.iscoroutinefunction(handler):
                if match:
                    return await handler(message, match)
                else:
                    return await handler(message)
            else:
                if match:
                    return handler(message, match)
                else:
                    return handler(message)
        except Exception as e:
            return BotResponse(
                content=f"执行操作失败：{str(e)}",
                message_type=MessageType.UNKNOWN
            )

    # 游戏流程处理器
    def _handle_faction_selection(self, message: UserMessage) -> BotResponse:
        """处理阵营选择（无参数）"""
        return BotResponse(
            content="请使用格式：选择阵营：收养人 或 选择阵营：Aeonreth",
            message_type=MessageType.COMMAND
        )

    def _handle_faction_selection_with_param(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理阵营选择（带参数）"""
        faction = match.group(1).strip()
        success, msg = self.game_service.register_player(
            message.user_id, message.username, faction
        )

        return BotResponse(
            content=msg,
            message_type=MessageType.COMMAND,
            should_mention=True
        )

    def _handle_start_turn(self, message: UserMessage) -> BotResponse:
        """处理开始轮次"""
        success, msg = self.game_service.start_new_game(message.user_id)
        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_roll_dice(self, message: UserMessage) -> BotResponse:
        """处理掷骰"""
        success, msg, combinations = self.game_service.roll_dice(message.user_id)

        if success and combinations:
            combo_text = "、".join([f"{c[0]},{c[1]}" for c in combinations])
            msg += f"\n可选组合：{combo_text}"

        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True,
            additional_data={"combinations": combinations} if success else None
        )

    def _handle_reroll_dice(self, message: UserMessage) -> BotResponse:
        """处理重投骰子（使用银骰子祝福）"""
        # 检查玩家是否拥有银骰子祝福
        player = self.game_service.db.get_player(message.user_id)
        if not player:
            return BotResponse(
                content="无法找到玩家信息！",
                message_type=MessageType.GAME_ACTION
            )

        if "银骰子祝福" not in player.inventory:
            return BotResponse(
                content="你没有银骰子祝福！只有获得银骰子祝福后才能重投。",
                message_type=MessageType.GAME_ACTION
            )

        # 消耗银骰子祝福
        player.inventory.remove("银骰子祝福")
        self.game_service.db.update_player(player)

        # 重新掷骰（不扣积分）
        success, msg, combinations = self.game_service.roll_dice(message.user_id, free_roll=True)

        if success and combinations:
            combo_text = "、".join([f"{c[0]},{c[1]}" for c in combinations])
            msg = f"🌟 使用银骰子祝福重投！\n{msg}\n可选组合：{combo_text}"
        else:
            msg = f"🌟 使用银骰子祝福重投！\n{msg}"

        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True,
            additional_data={"combinations": combinations} if success else None
        )

    def _handle_move_two_markers(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理移动两个标记"""
        col1 = int(match.group(1))
        col2 = int(match.group(2))
        success, msg = self.game_service.move_markers(message.user_id, [col1, col2])

        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_move_one_marker(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理移动一个标记"""
        col = int(match.group(1))

        # 如果是1-5的数字，先检查是否是陷阱选择
        if 1 <= col <= 5:
            # 检查玩家是否处于陷阱选择状态
            # TODO: 需要游戏状态系统来跟踪玩家是否遇到了河神陷阱
            # 现在暂时当作正常移动处理，如果列号无效会被下面的检查捕获
            pass

        # 对于特殊情况的数字（可能是列号也可能是选择）
        if col in [3, 4, 5]:  # 这些数字既是有效列号又可能是陷阱选择
            # 先尝试移动，如果失败再尝试其他选项
            success, msg = self.game_service.move_markers(message.user_id, [col])
            if success:
                return BotResponse(
                    content=msg,
                    message_type=MessageType.GAME_ACTION,
                    should_mention=True
                )

            # 移动失败，尝试陷阱选择
            if 1 <= col <= 5:
                choice_map = {
                    1: "都是我掉的",
                    2: "金骰子",
                    3: "银骰子",
                    4: "普通d6骰子",
                    5: "我没掉"
                }
                return self._process_trap_choice(message, choice_map[col])

        # 检查是否是有效的列号
        if not (3 <= col <= 18):
            # 如果是1-2且不是有效列号，先尝试作为陷阱选择，再作为玩家选择
            if col in [1, 2]:
                choice_map = {
                    1: "都是我掉的",
                    2: "金骰子"
                }
                return self._process_trap_choice(message, choice_map[col])

            # 如果是6-10，尝试作为玩家选择
            elif 6 <= col <= 10:
                success, result_msg = self.game_service.select_player_for_penalty(
                    message.user_id, str(col)
                )
                if success:
                    return BotResponse(
                        content=result_msg,
                        message_type=MessageType.GAME_ACTION,
                        should_mention=True
                    )

                return BotResponse(
                    content=f"无效的选择：{col}，请检查当前游戏状态",
                    message_type=MessageType.GAME_ACTION
                )
            else:
                return BotResponse(
                    content=f"无效的列号：{col}，有效范围是3-18",
                    message_type=MessageType.GAME_ACTION
                )

        success, msg = self.game_service.move_markers(message.user_id, [col])

        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_end_turn(self, message: UserMessage) -> BotResponse:
        """处理结束回合"""
        success, msg = self.game_service.end_turn(message.user_id)
        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_complete_checkin(self, message: UserMessage) -> BotResponse:
        """处理完成打卡"""
        success, msg = self.game_service.complete_checkin(message.user_id)
        return BotResponse(
            content=msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_get_status(self, message: UserMessage) -> BotResponse:
        """处理查看状态"""
        success, msg = self.game_service.get_game_status(message.user_id)
        return BotResponse(
            content=msg,
            message_type=MessageType.QUERY,
            should_mention=True
        )

    # 积分奖励处理器
    def _handle_add_score(self, message: UserMessage, score_type: str) -> BotResponse:
        """处理添加积分"""
        success, msg = self.game_service.add_score(message.user_id, 0, score_type)
        return BotResponse(
            content=msg,
            message_type=MessageType.SCORE_REWARD,
            should_mention=True
        )

    def _handle_reward_with_number(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理带编号的奖励"""
        reward_type = match.group(1)
        number = match.group(2)

        # 转换奖励类型
        type_map = {
            "草图": "草图",
            "精致小图": "精致小图",
            "精草大图": "精草大图",
            "精致大图": "精致大图"
        }

        actual_type = type_map.get(reward_type, reward_type)
        success, msg = self.game_service.add_score(message.user_id, 0, actual_type)

        return BotResponse(
            content=msg,
            message_type=MessageType.SCORE_REWARD,
            should_mention=True
        )

    def _handle_super_satisfied(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理超常发挥奖励（支持倍数）"""
        try:
            multiplier = int(match.group(1))
            if multiplier <= 0:
                return BotResponse(
                    content="❌ 倍数必须为正整数",
                    message_type=MessageType.ERROR,
                    should_mention=True
                )

            # 基础积分30，乘以倍数
            base_score = 30
            final_score = base_score * multiplier

            success, msg = self.game_service.add_score(message.user_id, final_score, f"超常发挥×{multiplier}")

            return BotResponse(
                content=msg,
                message_type=MessageType.SCORE_REWARD,
                should_mention=True
            )
        except ValueError:
            return BotResponse(
                content="❌ 倍数必须为有效数字",
                message_type=MessageType.ERROR,
                should_mention=True
            )

    # 商店系统处理器
    def _handle_shop(self, message: UserMessage) -> BotResponse:
        """处理道具商店查看"""
        success, shop_content = self.game_service.get_shop_items(message.user_id)

        return BotResponse(
            content=shop_content,
            message_type=MessageType.QUERY,
            should_mention=True
        )

    def _handle_inventory(self, message: UserMessage) -> BotResponse:
        """处理查看库存"""
        success, inventory_content = self.game_service.view_inventory(message.user_id)

        return BotResponse(
            content=inventory_content,
            message_type=MessageType.QUERY,
            should_mention=True
        )

    def _handle_buy_item(self, message: UserMessage) -> BotResponse:
        """处理购买丑喵玩偶（向后兼容）"""
        return self._handle_buy_specific_item(message, type('Match', (), {'group': lambda self, n: "丑喵玩偶"})())

    def _handle_use_item(self, message: UserMessage) -> BotResponse:
        """处理使用丑喵玩偶（向后兼容）"""
        return self._handle_use_specific_item(message, type('Match', (), {'group': lambda self, n: "丑喵玩偶"})())

    def _handle_buy_specific_item(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理购买特定道具"""
        item_name = match.group(1)
        success, result_message = self.game_service.purchase_item(message.user_id, item_name)

        return BotResponse(
            content=result_message,
            message_type=MessageType.COMMAND if success else MessageType.ERROR,
            should_mention=True
        )

    def _handle_use_specific_item(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理使用特定道具"""
        # 解析道具名和选项
        full_match = match.group(1)
        parts = full_match.split(maxsplit=1)
        item_name = parts[0]
        choice = parts[1] if len(parts) > 1 else None

        success, result_message, extra_data = self.game_service.use_item(message.user_id, item_name, choice)

        # 如果需要选择，提示用户
        if not success and extra_data.get("needs_choice"):
            message_type = MessageType.QUERY
        else:
            message_type = MessageType.GAME_ACTION if success else MessageType.ERROR

        return BotResponse(
            content=result_message,
            message_type=message_type,
            should_mention=True
        )

    def _handle_add_item_to_shop(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理添加道具到商店（GM功能）"""
        item_name = match.group(1)

        # GM功能：直接给玩家添加道具
        success = self.game_service.db.add_item_to_inventory(
            message.user_id,
            item_name,
            "consumable",
            1
        )

        if success:
            content = f"✅ 已获得道具：{item_name}"
        else:
            content = f"❌ 添加道具失败：{item_name}"

        return BotResponse(
            content=content,
            message_type=MessageType.COMMAND,
            should_mention=True
        )

    # 查询功能处理器
    def _handle_leaderboard(self, message: UserMessage) -> BotResponse:
        """处理排行榜查询"""
        success, msg = self.game_service.get_leaderboard()
        return BotResponse(
            content=msg,
            message_type=MessageType.QUERY
        )

    def _handle_help(self, message: UserMessage) -> BotResponse:
        """处理帮助"""
        help_content = """
🎯 Can't Stop 游戏指令帮助
========================

🏁 游戏开始
-----------
选择阵营：收养人/Aeonreth - 选择游戏阵营
轮次开始 - 开始新轮次

🎲 游戏操作
-----------
掷骰/.r6d6 - 掷骰子（消耗10积分）
8,13 - 记录双数值，移动两个标记
8 - 记录单数值，移动一个标记
替换永久棋子 - 主动结束轮次
查看当前进度 - 查看游戏状态
打卡完毕 - 恢复游戏功能

💰 积分奖励
-----------
我超级满意这张图X - 获得积分奖励(基础30×倍数X)
  例: 我超级满意这张图5 = 30×5 = 150积分

🛒 道具商店
-----------
道具商店 - 查看商店
购买丑喵玩偶 - 购买玩偶(150积分)
捏捏丑喵玩偶 - 使用玩偶(每天3次)

🕳️ 陷阱选择
-----------
当触发"河..土地神"陷阱时：
1/都是我掉的 - 贪心选择
2/金骰子 - 获得祝福效果
3/银骰子 - 获得重骰机会
4/普通d6骰子 - 获得积分奖励
5/我没掉 - 诚实选择

当触发"花言巧语"陷阱时：
选择玩家1 - 选择1号玩家承受惩罚
投掷抵消 - 被选中的玩家投掷1d6尝试抵消

🔄 玩家管理
-----------
玩家列表 - 查看所有活跃玩家
切换玩家 - 显示可切换的玩家
切换到[用户名] - 切换到指定玩家

📊 查询功能
-----------
排行榜 - 查看玩家排行榜

🎯 游戏目标：在任意3列登顶即可获胜！
        """
        return BotResponse(
            content=help_content.strip(),
            message_type=MessageType.QUERY
        )

    def _handle_trap_choice(self, message: UserMessage) -> BotResponse:
        """处理陷阱选择（文字选项）"""
        choice = message.content.strip()
        return self._process_trap_choice(message, choice)


    def _process_trap_choice(self, message: UserMessage, choice: str) -> BotResponse:
        """处理陷阱选择的具体逻辑"""
        choice_responses = {
            "都是我掉的": "土地神：「贪心的人类啊！」你失去了所有临时标记！",
            "金骰子": "土地神：「很好，诚实的孩子。」你获得了金骰子的祝福！下次掷骰结果+1！",
            "银骰子": "土地神：「银子也不错。」你获得了银骰子的祝福！下次掷骰可重骰一次！",
            "普通d6骰子": "土地神：「平凡也是一种智慧。」你获得了10积分奖励！",
            "我没掉": "土地神：「诚实的孩子！」你没有掉任何东西，继续前进吧！"
        }

        response_text = choice_responses.get(choice, f"你选择了：{choice}")

        # 处理陷阱选择的具体效果
        if choice == "普通d6骰子":
            # 给予10积分奖励
            success, score_msg = self.game_service.add_score(message.user_id, 10, "河神陷阱奖励")
            if success:
                # 获取玩家当前积分
                player = self.game_service.db.get_player(message.user_id)
                current_score = player.current_score if player else 0
                response_text += f"\n当前积分：{current_score}"
            else:
                response_text += f"\n积分添加失败：{score_msg}"

        elif choice == "都是我掉的":
            # 失去所有临时标记
            from ..core.item_system import get_buff_manager

            # 获取玩家当前会话
            player = self.game_service.db.get_player(message.user_id)
            if player:
                session = self.game_service.engine.get_player_active_session(message.user_id)
                if session:
                    # 清除所有临时标记
                    columns_to_clear = list(session.temporary_markers.keys())
                    for column in columns_to_clear:
                        session.remove_temporary_marker(column)

                    # 保存会话
                    self.game_service.db.save_game_session(session)

                    if columns_to_clear:
                        response_text += f"\n失去了 {len(columns_to_clear)} 个临时标记（列：{', '.join(map(str, columns_to_clear))}）"
                    else:
                        response_text += "\n（你当前没有临时标记）"
                else:
                    response_text += "\n无法找到当前游戏会话"
            else:
                response_text += "\n无法找到玩家信息"

        elif choice == "金骰子":
            # 下次掷骰结果+1的祝福效果
            from ..core.item_system import get_buff_manager, PlayerBuff, BuffType

            buff_manager = get_buff_manager()
            buff = PlayerBuff(
                buff_type=BuffType.DICE_MODIFIER,
                value=1,
                duration=1,
                source="河神金骰子"
            )
            buff_manager.add_buff(message.user_id, buff)
            response_text += "\n金骰子的祝福已生效！下次掷骰所有结果+1！"

        elif choice == "银骰子":
            # 给予银骰子祝福 - 下次掷骰可重骰一次
            player = self.game_service.db.get_player(message.user_id)
            if player:
                # 在库存中添加银骰子祝福标记
                if "银骰子祝福" not in player.inventory:
                    player.inventory.append("银骰子祝福")
                    self.game_service.db.update_player(player)
                    response_text += f"\n银骰子祝福已生效！下次掷骰时输入'重投'可重新掷骰。"
                else:
                    response_text += f"\n你已经拥有银骰子祝福了！"
            else:
                response_text += f"\n无法找到玩家信息！"

        return BotResponse(
            content=response_text,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    # 遭遇事件处理器
    def _handle_encounter_choice(self, message: UserMessage) -> BotResponse:
        """处理遭遇事件选择"""
        choice_name = message.content.strip()

        # 调试：检查pending encounters
        from ..core.encounter_system import get_encounter_manager
        encounter_mgr = get_encounter_manager()
        has_pending = message.user_id in encounter_mgr.pending_encounters
        print(f"[DEBUG] 玩家 {message.user_id} 尝试选择: {choice_name}, 有pending遭遇: {has_pending}")

        success, result_msg = self.game_service.process_encounter_choice(
            message.user_id, choice_name
        )

        print(f"[DEBUG] 处理结果: success={success}, msg={result_msg[:50] if result_msg else 'None'}")

        return BotResponse(
            content=result_msg,
            message_type=MessageType.GAME_ACTION if success else MessageType.ERROR,
            should_mention=True
        )

    def _handle_encounter_follow_up(self, message: UserMessage) -> BotResponse:
        """处理遭遇follow_up响应"""
        response = message.content.strip()
        success, result_msg = self.game_service.process_encounter_follow_up(
            message.user_id, response
        )

        if success and result_msg:
            return BotResponse(
                content=result_msg,
                message_type=MessageType.GAME_ACTION,
                should_mention=True
            )

        # 如果不是follow_up，返回None让其他处理器处理
        return None

    def _handle_player_list(self, message: UserMessage) -> BotResponse:
        """显示所有玩家列表"""
        success, players = self.game_service.get_all_players()

        if not success or not players:
            return BotResponse(
                content="没有找到活跃玩家",
                message_type=MessageType.QUERY
            )

        player_list = "📋 当前活跃玩家列表：\n" + "-" * 30 + "\n"
        for player_info in players:
            player_list += f"{player_info['id']}. {player_info['username']} ({player_info['faction']})\n"

        return BotResponse(
            content=player_list,
            message_type=MessageType.QUERY
        )

    def _handle_select_player_for_penalty(self, message: UserMessage, match) -> BotResponse:
        """处理选择玩家承受惩罚"""
        target_number = match.group(1)
        success, result_msg = self.game_service.select_player_for_penalty(
            message.user_id, target_number
        )

        return BotResponse(
            content=result_msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_penalty_resistance(self, message: UserMessage) -> BotResponse:
        """处理投掷抵消惩罚"""
        success, result_msg = self.game_service.attempt_penalty_resistance(message.user_id)

        return BotResponse(
            content=result_msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_switch_player_prompt(self, message: UserMessage) -> BotResponse:
        """显示可切换的玩家列表"""
        success, players = self.game_service.get_all_players()

        if not success or not players:
            return BotResponse(
                content="没有找到其他玩家",
                message_type=MessageType.QUERY
            )

        switch_prompt = "🔄 选择要切换到的玩家：\n" + "-" * 30 + "\n"
        for player_info in players:
            if player_info["player_id"] != message.user_id:
                switch_prompt += f"💡 输入：切换到{player_info['username']}\n"

        return BotResponse(
            content=switch_prompt,
            message_type=MessageType.QUERY
        )

    def _handle_switch_to_player(self, message: UserMessage, match) -> BotResponse:
        """处理切换到指定玩家"""
        target_username = match.group(1).strip()

        # 通过用户名找到玩家ID
        success, players = self.game_service.get_all_players()
        if not success:
            return BotResponse(
                content="获取玩家列表失败",
                message_type=MessageType.GAME_ACTION
            )

        target_player_id = None
        for player_info in players:
            if player_info["username"] == target_username:
                target_player_id = player_info["player_id"]
                break

        if not target_player_id:
            return BotResponse(
                content=f"未找到玩家：{target_username}",
                message_type=MessageType.GAME_ACTION
            )

        success, result_msg = self.game_service.switch_to_player(
            message.user_id, target_player_id
        )

        return BotResponse(
            content=result_msg,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_numbered_trap_choice(self, message: UserMessage, match) -> BotResponse:
        """处理带数字的陷阱选择（如 "5. 我没掉"）"""
        number = match.group(1)
        text = match.group(2).strip()

        # 映射数字到选择
        choice_map = {
            "1": "都是我掉的",
            "2": "金骰子",
            "3": "银骰子",
            "4": "普通d6骰子",
            "5": "我没掉"
        }

        if number in choice_map:
            expected_choice = choice_map[number]
            # 验证文字是否匹配
            if text in expected_choice or expected_choice in text:
                return self._process_trap_choice(message, expected_choice)
            else:
                return BotResponse(
                    content=f"数字{number}对应的选项是'{expected_choice}'，但你输入的是'{text}'，请确认选择。",
                    message_type=MessageType.GAME_ACTION
                )

        return BotResponse(
            content="请输入1-5之间的数字选择陷阱选项。",
            message_type=MessageType.GAME_ACTION
        )

    def _handle_summit_confirmation(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理登顶确认：数列{x}登顶"""
        column = int(match.group(1))

        # 调用游戏服务确认登顶
        success, result_message = self.game_service.confirm_summit(message.user_id, column)

        return BotResponse(
            content=result_message,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_achievements(self, message: UserMessage) -> BotResponse:
        """处理成就一览"""
        try:
            from ..core.achievement_manager import AchievementManager

            manager = AchievementManager()

            # 获取所有可见成就（排除未解锁的隐藏成就）
            system = manager.system
            if hasattr(system, 'get_visible_achievements'):
                achievements = system.get_visible_achievements()
            else:
                achievements = manager.get_all_achievements()

            # 按分类统计
            unlocked_count = sum(1 for a in achievements if a.is_unlocked)
            total_count = len(achievements)

            # 构建消息
            response = "🏆 成就一览 🏆\n"
            response += f"━━━━━━━━━━━━━━━━\n"
            response += f"已解锁：{unlocked_count}/{total_count}\n"
            response += f"完成度：{unlocked_count / total_count * 100:.1f}%\n"
            response += f"━━━━━━━━━━━━━━━━\n\n"

            # 按分类显示
            from ..core.achievement_system import AchievementCategory

            for category in AchievementCategory:
                cat_achievements = [a for a in achievements if a.category == category]
                if cat_achievements:
                    response += f"【{category.value}】\n"
                    for ach in cat_achievements:
                        status = "✅" if ach.is_unlocked else "❌"
                        response += f"{status} {ach.name}\n"
                        if ach.is_unlocked:
                            response += f"   {ach.reward_description}\n"
                        else:
                            response += f"   {ach.unlock_condition}\n"
                    response += "\n"

            return BotResponse(
                content=response,
                message_type=MessageType.QUERY
            )
        except Exception as e:
            return BotResponse(
                content=f"查询成就失败：{str(e)}",
                message_type=MessageType.QUERY
            )

    def _handle_progress_retreat(self, message: UserMessage) -> BotResponse:
        """处理进度回退（玩家主动失败）"""
        success, result_message = self.game_service.force_fail_turn(message.user_id)

        return BotResponse(
            content=result_message,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_reward_doubled(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理翻倍奖励：领取（类型）奖励n*2"""
        reward_type = match.group(1).strip()
        multiplier = int(match.group(2))

        # 调用游戏服务领取奖励（翻倍）
        success, result_message = self.game_service.claim_reward(
            message.user_id,
            reward_type,
            multiplier,
            doubled=True
        )

        return BotResponse(
            content=result_message,
            message_type=MessageType.SCORE_REWARD,
            should_mention=True
        )


class QQBotAdapter:
    """QQ机器人适配器"""

    def __init__(self):
        self.message_processor = MessageProcessor()

    async def handle_group_message(self, user_id: str, username: str, group_id: str, message: str) -> str:
        """处理群消息"""
        user_message = UserMessage(
            user_id=user_id,
            username=username,
            content=message,
            group_id=group_id
        )

        response = await self.message_processor.process_message_async(user_message)
        return response.content if response else None

    async def handle_private_message(self, user_id: str, username: str, message: str) -> str:
        """处理私聊消息"""
        user_message = UserMessage(
            user_id=user_id,
            username=username,
            content=message
        )

        response = await self.message_processor.process_message_async(user_message)
        return response.content if response else None

    def get_bot_response_with_mention(self, response: BotResponse, username: str) -> str:
        """获取带@的回复"""
        if response.should_mention:
            return f"@{username} {response.content}"
        return response.content