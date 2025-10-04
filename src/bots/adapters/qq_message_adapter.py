"""
QQ消息适配器 - 优化游戏消息在QQ群中的显示效果
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MessageStyle:
    """消息样式配置"""
    use_emoji: bool = True
    max_length: int = 1000
    compact_mode: bool = False
    mention_user: bool = False


class QQMessageAdapter:
    """QQ消息适配器"""

    def __init__(self, style: MessageStyle = None):
        self.style = style or MessageStyle()

        # Emoji替换映射（针对不支持emoji的情况）
        self.emoji_replacements = {
            '🎲': '[骰子]',
            '🎉': '[庆祝]',
            '❌': '[错误]',
            '✅': '[成功]',
            '⚠️': '[警告]',
            '🔥': '[火]',
            '🌊': '[水]',
            '👻': '[鬼]',
            '💬': '[对话]',
            '🏠': '[家]',
            '📅': '[日历]',
            '🎯': '[目标]',
            '⚡': '[闪电]',
            '🎭': '[面具]',
            '📦': '[盒子]',
            '🛒': '[购物车]',
            '💰': '[金币]',
            '🎮': '[游戏]',
            '🏆': '[奖杯]',
            '⭐': '[星星]',
            '🎊': '[彩带]',
            '💯': '[100分]',
            '🔧': '[工具]',
            '📊': '[图表]',
            '🎪': '[马戏团]',
        }

        # 特殊格式标记
        self.format_markers = {
            'bold': ('**', '**'),
            'italic': ('*', '*'),
            'code': ('`', '`'),
            'block': ('```', '```'),
        }

    def adapt_message(self, message: str, user_id: str = None, message_type: str = "game") -> str:
        """适配消息格式"""
        if not message:
            return ""

        adapted = message

        # 1. 处理emoji
        if not self.style.use_emoji:
            adapted = self._replace_emojis(adapted)

        # 2. 格式化特殊内容
        adapted = self._format_game_content(adapted, message_type)

        # 3. 优化显示布局
        adapted = self._optimize_layout(adapted)

        # 4. 限制消息长度
        adapted = self._limit_length(adapted)

        # 5. 添加用户提及（如果需要）
        if self.style.mention_user and user_id:
            adapted = f"[CQ:at,qq={user_id}] {adapted}"

        return adapted

    def _replace_emojis(self, text: str) -> str:
        """替换emoji为文本"""
        for emoji, replacement in self.emoji_replacements.items():
            text = text.replace(emoji, replacement)
        return text

    def _format_game_content(self, text: str, message_type: str) -> str:
        """格式化游戏内容"""
        if message_type == "dice_result":
            return self._format_dice_result(text)
        elif message_type == "game_status":
            return self._format_game_status(text)
        elif message_type == "trap_trigger":
            return self._format_trap_message(text)
        elif message_type == "achievement":
            return self._format_achievement_message(text)
        elif message_type == "leaderboard":
            return self._format_leaderboard(text)
        else:
            return self._format_general_game_message(text)

    def _format_dice_result(self, text: str) -> str:
        """格式化骰子结果"""
        # 识别骰子结果模式
        dice_pattern = r'骰点[:：]\s*(\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+)'
        match = re.search(dice_pattern, text)

        if match:
            dice_str = match.group(1)
            dice_numbers = dice_str.split()

            # 美化骰子显示
            formatted_dice = " | ".join([f"[{num}]" for num in dice_numbers])
            text = re.sub(dice_pattern, f'骰点: {formatted_dice}', text)

        return text

    def _format_game_status(self, text: str) -> str:
        """格式化游戏状态"""
        if self.style.compact_mode:
            # 紧凑模式：简化状态显示
            lines = text.split('\n')
            important_lines = []

            for line in lines:
                if any(keyword in line for keyword in ['当前位置', '积分', '已登顶', '轮次']):
                    important_lines.append(line.strip())

            return ' | '.join(important_lines) if important_lines else text

        return text

    def _format_trap_message(self, text: str) -> str:
        """格式化陷阱消息"""
        # 为陷阱消息添加特殊格式
        if '触发陷阱' in text:
            # 突出显示陷阱名称
            trap_pattern = r'触发陷阱[:：](.+?)(\n|$)'
            text = re.sub(trap_pattern, r'⚡触发陷阱: **\1**\2', text)

        # 格式化角色台词
        quote_pattern = r'"([^"]+)"'
        text = re.sub(quote_pattern, r'💬 "\1"', text)

        return text

    def _format_achievement_message(self, text: str) -> str:
        """格式化成就消息"""
        if '成就解锁' in text:
            # 突出显示成就解锁
            text = f"🎊 **{text}** 🎊"

        return text

    def _format_leaderboard(self, text: str) -> str:
        """格式化排行榜"""
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            if re.match(r'^\d+\.\s', line):  # 排行榜条目
                # 为前三名添加特殊标记
                if line.startswith('1.'):
                    line = f"🥇 {line[2:]}"
                elif line.startswith('2.'):
                    line = f"🥈 {line[2:]}"
                elif line.startswith('3.'):
                    line = f"🥉 {line[2:]}"

            formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _format_general_game_message(self, text: str) -> str:
        """格式化通用游戏消息"""
        # 突出显示重要信息
        if 'ERROR' in text:
            text = f"❌ {text.replace('ERROR', '').strip()}"
        elif 'OK' in text and text.startswith('OK'):
            text = f"✅ {text.replace('OK', '').strip()}"

        # 格式化积分变化
        score_pattern = r'积分\+(\d+)'
        text = re.sub(score_pattern, r'💰+\1积分', text)

        score_pattern = r'积分-(\d+)'
        text = re.sub(score_pattern, r'💸-\1积分', text)

        return text

    def _optimize_layout(self, text: str) -> str:
        """优化显示布局"""
        # 移除多余的空行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        # 优化分隔线
        text = text.replace('=' * 50, '─' * 20)
        text = text.replace('-' * 30, '┄' * 15)

        # 如果是紧凑模式，进一步简化
        if self.style.compact_mode:
            # 移除装饰性分隔线
            text = re.sub(r'[─┄=\-]{5,}', '', text)
            # 合并短行
            lines = text.split('\n')
            merged_lines = []
            current_line = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if len(current_line) + len(line) < 50:
                    current_line += f" {line}" if current_line else line
                else:
                    if current_line:
                        merged_lines.append(current_line)
                    current_line = line

            if current_line:
                merged_lines.append(current_line)

            text = '\n'.join(merged_lines)

        return text

    def _limit_length(self, text: str) -> str:
        """限制消息长度"""
        if len(text) <= self.style.max_length:
            return text

        # 智能截断，尽量在句子边界
        truncate_pos = self.style.max_length - 3  # 为"..."预留空间

        # 寻找最近的句子结束位置
        for i in range(truncate_pos, max(0, truncate_pos - 100), -1):
            if text[i] in '.。\n':
                return text[:i + 1] + "..."

        # 如果找不到合适的截断点，直接截断
        return text[:truncate_pos] + "..."

    def format_help_message(self) -> str:
        """格式化帮助消息"""
        help_text = """🎮 CantStop贪骰无厌 - QQ群版

🎯 基础指令:
• help - 显示帮助
• 轮次开始 - 开始新轮次
• .r6d6 - 掷骰子
• 8,13 - 移动棋子到8列和13列
• 替换永久棋子 - 结束轮次
• 查看当前进度 - 查看状态

🏆 奖励指令:
• 领取(类型)奖励1 - 普通奖励
• 我超级满意这张图1 - 超常发挥奖励

🛒 商店指令:
• 道具商店 - 查看商店
• 购买丑喵玩偶 - 购买道具

💡 提示: 首次使用会自动注册账号"""

        return self.adapt_message(help_text, message_type="help")

    def format_welcome_message(self, username: str) -> str:
        """格式化欢迎消息"""
        welcome = f"""欢迎 {username} 加入CantStop！🎲

这是一个骰子策略游戏，目标是在3列登顶获胜！
输入 'help' 查看完整指令列表
输入 '轮次开始' 开始你的第一局游戏"""

        return self.adapt_message(welcome, message_type="welcome")

    def create_compact_adapter(self) -> 'QQMessageAdapter':
        """创建紧凑模式适配器"""
        compact_style = MessageStyle(
            use_emoji=True,
            max_length=500,
            compact_mode=True,
            mention_user=False
        )
        return QQMessageAdapter(compact_style)

    def create_no_emoji_adapter(self) -> 'QQMessageAdapter':
        """创建无emoji适配器"""
        no_emoji_style = MessageStyle(
            use_emoji=False,
            max_length=1000,
            compact_mode=False,
            mention_user=False
        )
        return QQMessageAdapter(no_emoji_style)