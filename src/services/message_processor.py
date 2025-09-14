"""
消息处理框架 - 用于QQ机器人集成
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio

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
            "替换永久棋子": self._handle_end_turn,
            "查看当前进度": self._handle_get_status,
            "打卡完毕": self._handle_complete_checkin,

            # 积分奖励
            "领取草图奖励": lambda msg: self._handle_add_score(msg, "草图"),
            "领取精致小图奖励": lambda msg: self._handle_add_score(msg, "精致小图"),
            "领取精草大图奖励": lambda msg: self._handle_add_score(msg, "精草大图"),
            "领取精致大图奖励": lambda msg: self._handle_add_score(msg, "精致大图"),

            # 商店系统
            "道具商店": self._handle_shop,
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
        })

        # 注册模式处理器
        self.pattern_handlers.extend([
            # 阵营选择：xxx
            (r"选择阵营：(.+)", self._handle_faction_selection_with_param),

            # 数值组合 (8,13 或 单个数字)
            (r"^(\d+),(\d+)$", self._handle_move_two_markers),
            (r"^(\d+)$", self._handle_move_one_marker),

            # 领取奖励
            (r"领取(.+)奖励(\d+)", self._handle_reward_with_number),
            (r"我超级满意这张图(\d+)", self._handle_super_satisfied),

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

    async def process_message(self, message: UserMessage) -> BotResponse:
        """处理消息"""
        try:
            content = message.content.strip()

            # 尝试命令匹配
            if content in self.command_handlers:
                return await self._execute_handler(self.command_handlers[content], message)

            # 尝试模式匹配
            for pattern, handler in self.pattern_handlers:
                match = re.match(pattern, content)
                if match:
                    return await self._execute_handler(handler, message, match)

            # 未匹配的消息
            return BotResponse(
                content="未识别的指令，输入 '帮助' 查看可用指令",
                message_type=MessageType.UNKNOWN
            )

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
            content="请使用格式：选择阵营：收养人 或 选择阵营：Aonreth",
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
        """处理超常发挥奖励"""
        number = match.group(1)
        success, msg = self.game_service.add_score(message.user_id, 0, "超常发挥")

        return BotResponse(
            content=msg,
            message_type=MessageType.SCORE_REWARD,
            should_mention=True
        )

    # 商店系统处理器
    def _handle_shop(self, message: UserMessage) -> BotResponse:
        """处理道具商店查看"""
        shop_content = """
🛒 道具商店
===========
常驻道具：
• 丑喵玩偶 - 150积分
  每天限3次使用，随机获得奖励

暂无其他道具上架
使用 '购买<道具名>' 购买道具
        """
        return BotResponse(
            content=shop_content.strip(),
            message_type=MessageType.QUERY,
            should_mention=True
        )

    def _handle_buy_item(self, message: UserMessage) -> BotResponse:
        """处理购买丑喵玩偶"""
        # 这里可以实现具体的购买逻辑
        return BotResponse(
            content="购买功能待实现，敬请期待！",
            message_type=MessageType.COMMAND,
            should_mention=True
        )

    def _handle_use_item(self, message: UserMessage) -> BotResponse:
        """处理使用丑喵玩偶"""
        import random

        # 模拟玩偶使用
        outcomes = [
            ("玩偶发出了吱吱的响声，并从你手中滑了出去", 0),
            ("玩偶发出了呼噜呼噜的响声，似乎很高兴", random.randint(3, 18))
        ]

        outcome, bonus = random.choice(outcomes)

        if bonus > 0:
            self.game_service.add_score(message.user_id, bonus, "丑喵玩偶奖励")
            content = f"{outcome}，你获得了{bonus}积分！"
        else:
            content = outcome

        return BotResponse(
            content=content,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

    def _handle_buy_specific_item(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理购买特定道具"""
        item_name = match.group(1)
        return BotResponse(
            content=f"购买 {item_name} 功能待实现",
            message_type=MessageType.COMMAND,
            should_mention=True
        )

    def _handle_use_specific_item(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理使用特定道具"""
        item_name = match.group(1)
        return BotResponse(
            content=f"使用 {item_name} 功能待实现",
            message_type=MessageType.COMMAND,
            should_mention=True
        )

    def _handle_add_item_to_shop(self, message: UserMessage, match: re.Match) -> BotResponse:
        """处理添加道具到商店"""
        item_name = match.group(1)
        return BotResponse(
            content=f"道具 {item_name} 已添加到商店（功能待实现）",
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
选择阵营：收养人/Aonreth - 选择游戏阵营
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
领取草图奖励1 - 草图作品奖励(+20积分)
领取精致小图奖励1 - 精致小图奖励(+80积分)
领取精草大图奖励1 - 精草大图奖励(+100积分)
领取精致大图奖励1 - 精致大图奖励(+150积分)
我超级满意这张图1 - 超常发挥奖励(+30积分)

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
        # 这里应该调用游戏服务的陷阱选择处理方法
        # 目前先返回确认消息，等待游戏服务实现具体逻辑

        choice_responses = {
            "都是我掉的": "土地神：「贪心的人类啊！」你失去了所有临时标记！",
            "金骰子": "土地神：「很好，诚实的孩子。」你获得了金骰子的祝福！下次掷骰结果+1！",
            "银骰子": "土地神：「银子也不错。」你获得了银骰子的祝福！下次掷骰可重骰一次！",
            "普通d6骰子": "土地神：「平凡也是一种智慧。」你获得了10积分奖励！",
            "我没掉": "土地神：「诚实的孩子！」你没有掉任何东西，继续前进吧！"
        }

        response_text = choice_responses.get(choice, f"你选择了：{choice}")

        return BotResponse(
            content=response_text,
            message_type=MessageType.GAME_ACTION,
            should_mention=True
        )

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

        response = await self.message_processor.process_message(user_message)
        return response.content

    async def handle_private_message(self, user_id: str, username: str, message: str) -> str:
        """处理私聊消息"""
        user_message = UserMessage(
            user_id=user_id,
            username=username,
            content=message
        )

        response = await self.message_processor.process_message(user_message)
        return response.content

    def get_bot_response_with_mention(self, response: BotResponse, username: str) -> str:
        """获取带@的回复"""
        if response.should_mention:
            return f"@{username} {response.content}"
        return response.content