"""
陷阱插件实现 - 所有陷阱效果的具体实现
"""

import random
from typing import Dict, Any, Optional
from .trap_plugin_system import TrapPluginBase


class FireballTrap(TrapPluginBase):
    """小小火球术陷阱"""

    def __init__(self):
        super().__init__(
            name="小小火球术",
            description="火球砸出的坑洞让你无处下脚。"
        )

    def get_character_quote(self) -> str:
        return "为什么我的火球术不能骰出这种伤害啊？！！"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：停止一回合，下回合强制骰子结果"""
        return {
            "type": "composite",
            "effects": [
                {
                    "type": "skip_turn",
                    "cost_score": True,
                    "description": "停止一回合（消耗一回合积分）"
                },
                {
                    "type": "forced_dice_result",
                    "value": [4, 5, 5, 5, 6, 6],
                    "duration": 1,
                    "description": "下回合骰子结果自动变为（4，5，5，5，6，6）"
                },
                {
                    "type": "prevent_end_turn",
                    "description": "在完成此惩罚前不得主动结束当前轮次"
                }
            ],
            "achievement": "fire_master",
            "description": "停止一回合，下回合骰子强制为（4，5，5，5，6，6）"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        """重复惩罚：-10积分"""
        return {
            "type": "score_change",
            "value": -10,
            "description": "-10积分"
        }


class DontLookBackTrap(TrapPluginBase):
    """\"不要回头\"陷阱"""

    def __init__(self):
        super().__init__(
            name="不要回头",
            description="你感到身后一股寒意，当你战战兢兢地转过身试图搞清楚状况时，你发现在看到它脸的那一刻一切都已经晚了……"
        )

    def get_character_quote(self) -> str:
        return "…话说回来，我有一计。"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：清空当前列进度"""
        return {
            "type": "reset_column_progress",
            "description": "清空当前列进度回到上一个永久旗子位置或初始位置",
            "achievement": "curiosity_killed_cat"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -15,
            "description": "-15积分"
        }


class WeddingRingTrap(TrapPluginBase):
    """婚戒...？陷阱"""

    def __init__(self):
        super().__init__(
            name="婚戒…？",
            description="象征契约精神的戒指。在你触碰它时，你突然被困在原地无法动弹。"
        )

    def get_character_quote(self) -> str:
        return "直到死亡将我们分开..."

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：强制暂停直到完成绘制"""
        return {
            "type": "force_artwork",
            "description": "强制暂停该轮次直到你完成此陷阱相关绘制（不计算积分）",
            "achievement_check": "explorer",  # 如果有探索家成就则免疫
            "achievement": "cold_heart"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -10,
            "description": "-10积分"
        }


class OddEvenTrap(TrapPluginBase):
    """奇变偶不变陷阱"""

    def __init__(self):
        super().__init__(
            name="奇变偶不变",
            description="这是什么神秘的暗号吗？"
        )

    def get_character_quote(self) -> str:
        return "符号看象限！"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：根据奇数个数判断奖励/惩罚"""
        return {
            "type": "dice_check_odd_even",
            "description": "下回合中，奇数大于3个则获得额外d6，否则本回合作废",
            "success_effect": {
                "type": "extra_dice",
                "dice": "1d6",
                "description": "额外获得一个d6骰可以随意加到两个加值的任意一个中",
                "achievement": "math_king"
            },
            "fail_effect": {
                "type": "void_turn_or_skip",
                "description": "本回合作废或下轮次停止一回合",
                "achievement": "math_zero"
            }
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -10,
            "description": "-10积分"
        }


class LightningKingTrap(TrapPluginBase):
    """雷电法王陷阱"""

    def __init__(self):
        super().__init__(
            name="雷电法王",
            description="一阵强劲的电流从脚底直达你的头顶"
        )

    def get_character_quote(self) -> str:
        return "学不学？"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：检查33加值数量"""
        return {
            "type": "dice_check_combinations",
            "description": "下回合中，33加值可得数字数量小于8种则本回合作废",
            "threshold": 8,
            "success_effect": {
                "type": "nothing",
                "achievement": "enter_in"
            },
            "fail_effect": {
                "type": "void_turn",
                "description": "本回合作废",
                "achievement": "crying_student"
            }
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -10,
            "description": "-10积分"
        }


class HeadshotTrap(TrapPluginBase):
    """中门对狙陷阱"""

    def __init__(self):
        super().__init__(
            name="中门对狙",
            description="有什么东西挡住了你的去路？哦！是另一个玩家！快快清除阻碍吧～"
        )

    def get_character_quote(self) -> str:
        return "Fire in the hole!"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：与另一玩家比大小"""
        return {
            "type": "pvp_dice_battle",
            "description": "任选一位玩家分别rd6比大小",
            "winner_reward": {
                "type": "score_change",
                "value": 5
            },
            "loser_penalty": {
                "type": "skip_turn",
                "cost_score": True
            },
            "tie_effect": {
                "type": "nothing",
                "description": "无事发生"
            }
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -10,
            "description": "-10积分"
        }


class SekiroTrap(TrapPluginBase):
    """影逝二度陷阱"""

    def __init__(self):
        super().__init__(
            name="影逝二度",
            description="如何决定的时候，你的骰子已经自己丢出去了…"
        )

    def get_character_quote(self) -> str:
        return "犹豫就会败北！"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：强制再进行两回合"""
        return {
            "type": "force_extra_turns",
            "turns": 2,
            "description": "你强制再进行两回合后才能结束该轮次",
            "achievement": "sekiro"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -10,
            "description": "-10积分"
        }


class RainbowOctopusTrap(TrapPluginBase):
    """七色章鱼陷阱"""

    def __init__(self):
        super().__init__(
            name="七色章鱼",
            description="一只闪着七色光芒的章鱼拦住了你的去路。萌萌的一小只看起来很无害，下一秒却卷起你把你丢了出去。"
        )

    def get_character_quote(self) -> str:
        return "你，审核不通过。"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：所有列回退一格"""
        return {
            "type": "all_columns_retreat",
            "value": 1,
            "description": "该轮次所有列的当前的进度回退一格",
            "achievement": "sad_painter"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -15,
            "description": "-15积分"
        }


class HollowFloorTrap(TrapPluginBase):
    """中空格子陷阱"""

    def __init__(self):
        super().__init__(
            name="中空格子",
            description="脚下的格子竟然是中空的？！！你一脚踩空快速下落，想要抓住边缘爬上来却始终无法成功。"
        )

    def get_character_quote(self) -> str:
        return "啊啊啊啊啊——"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：暂停2回合"""
        return {
            "type": "skip_multiple_turns",
            "turns": 2,
            "cost_score": True,
            "description": "暂停2回合（消耗2回合积分）",
            "achievement": "fall_guys"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "skip_turn",
            "cost_score": True,
            "description": "暂停1回合（消耗积分）"
        }


class OASAkariaTrap(TrapPluginBase):
    """OAS阿卡利亚陷阱"""

    def __init__(self):
        super().__init__(
            name="OAS阿卡利亚",
            description="你越玩越觉得这场真人游戏出现了太多奇怪的地方：不符合常理的装置、奇怪的音响、天气突然变化…当你停下来观察这一切的时候，你隔着一个个玻璃屏仿佛看到了若隐若现的，成百上千个摄像头正对着你…你忍不住再次思考这一切，道心破碎。"
        )

    def get_character_quote(self) -> str:
        return "这一切...都是真的吗？"

    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """首次惩罚：积分减1/4 + rd20判定"""
        return {
            "type": "composite",
            "effects": [
                {
                    "type": "score_change_percentage",
                    "value": -0.25,
                    "description": "道心破碎，积分减1/4"
                },
                {
                    "type": "dice_check",
                    "dice": "1d20",
                    "success_threshold": 10,
                    "auto_success_faction": "aonreth",
                    "success_effect": {
                        "type": "end_session",
                        "description": "你迅速做出了反击，击退了那怪物，但你仍然受了些伤，看来需要休息一下了。强制结束本轮次。"
                    },
                    "fail_effect": {
                        "type": "score_change",
                        "value": -20,
                        "description": "你被攻击后陷入了昏迷...当你再次清醒过来时，发现身上的糖果都不见了...积分-20。"
                    }
                }
            ],
            "description": "道心破碎后遭遇怪物袭击"
        }

    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        return {
            "type": "score_change",
            "value": -15,
            "description": "-15积分"
        }


# 陷阱插件注册表
TRAP_PLUGINS = {
    "小小火球术": FireballTrap,
    "不要回头": DontLookBackTrap,
    "婚戒…？": WeddingRingTrap,
    "奇变偶不变": OddEvenTrap,
    "雷电法王": LightningKingTrap,
    "中门对狙": HeadshotTrap,
    "影逝二度": SekiroTrap,
    "七色章鱼": RainbowOctopusTrap,
    "中空格子": HollowFloorTrap,
    "OAS阿卡利亚": OASAkariaTrap,
}


def create_trap_plugin(trap_name: str) -> Optional[TrapPluginBase]:
    """创建陷阱插件实例"""
    plugin_class = TRAP_PLUGINS.get(trap_name)
    if plugin_class:
        return plugin_class()
    return None
