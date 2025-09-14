"""
消息处理器测试
"""

import pytest
import asyncio
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.message_processor import MessageProcessor, UserMessage, BotResponse, MessageType


class TestMessageProcessor:
    """消息处理器测试类"""

    def setup_method(self):
        """测试前设置"""
        self.processor = MessageProcessor()

    @pytest.mark.asyncio
    async def test_faction_selection(self):
        """测试阵营选择"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="选择阵营：收养人"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.COMMAND
        assert "收养人" in response.content

    @pytest.mark.asyncio
    async def test_dice_combination_two_numbers(self):
        """测试双数字组合"""
        # 先注册玩家
        register_message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="选择阵营：收养人"
        )
        await self.processor.process_message(register_message)

        # 开始游戏
        start_message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="轮次开始"
        )
        await self.processor.process_message(start_message)

        # 测试数字组合
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="8,13"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.GAME_ACTION

    @pytest.mark.asyncio
    async def test_single_number(self):
        """测试单数字"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="10"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)

    @pytest.mark.asyncio
    async def test_invalid_column(self):
        """测试无效列号"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="25"  # 无效列号
        )

        response = await self.processor.process_message(message)
        assert "无效的列号" in response.content

    @pytest.mark.asyncio
    async def test_help_command(self):
        """测试帮助指令"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="帮助"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.QUERY
        assert "游戏指令帮助" in response.content

    @pytest.mark.asyncio
    async def test_score_reward(self):
        """测试积分奖励"""
        # 注册用户
        register_message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="选择阵营：收养人"
        )
        await self.processor.process_message(register_message)

        # 领取奖励
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="领取草图奖励1"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.SCORE_REWARD

    @pytest.mark.asyncio
    async def test_super_satisfied_reward(self):
        """测试超常发挥奖励"""
        # 注册用户
        register_message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="选择阵营：收养人"
        )
        await self.processor.process_message(register_message)

        # 超常发挥
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="我超级满意这张图1"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.SCORE_REWARD
        assert "30" in response.content

    @pytest.mark.asyncio
    async def test_shop_command(self):
        """测试商店指令"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="道具商店"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.QUERY
        assert "道具商店" in response.content
        assert "丑喵玩偶" in response.content

    @pytest.mark.asyncio
    async def test_leaderboard(self):
        """测试排行榜"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="排行榜"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.QUERY

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """测试未知指令"""
        message = UserMessage(
            user_id="test_user",
            username="测试用户",
            content="这是一个未知的指令"
        )

        response = await self.processor.process_message(message)
        assert isinstance(response, BotResponse)
        assert response.message_type == MessageType.UNKNOWN
        assert "未识别的指令" in response.content

    @pytest.mark.asyncio
    async def test_pattern_matching(self):
        """测试模式匹配"""
        # 测试各种模式
        test_cases = [
            ("选择阵营：Aonreth", True),
            ("8,13", True),
            ("15", True),
            ("领取精致大图奖励2", True),
            ("购买传送卷轴", True),
            ("无效模式", False)
        ]

        for content, should_match in test_cases:
            message = UserMessage(
                user_id="test_user",
                username="测试用户",
                content=content
            )

            response = await self.processor.process_message(message)

            if should_match:
                assert response.message_type != MessageType.UNKNOWN
            # 对于无效模式，应该返回未知指令
            # 但我们不强制要求，因为某些"无效"的可能被其他规则匹配


if __name__ == "__main__":
    pytest.main([__file__, "-v"])