"""
陷阱系统
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import random
from ..config.config_manager import get_config


class TrapType(Enum):
    """陷阱类型"""
    FIREBALL = "小小火球术"
    NO_LOOK_BACK = "不要回头"
    RIVER_SPIRIT = "河土地神"
    SWEET_TALK = "花言巧语"


@dataclass
class TrapEffect:
    """陷阱效果数据结构"""
    trap_type: TrapType
    description: str
    penalty_description: str
    character_quote: str
    first_time_penalty: str
    repeat_penalty: str = None

    def __post_init__(self):
        if self.repeat_penalty is None:
            dice_cost = get_config("game_config", "game.dice_cost", 10)
            self.repeat_penalty = f"-{dice_cost}积分"


class TrapSystem:
    """陷阱系统"""

    def __init__(self):
        self.traps: Dict[TrapType, TrapEffect] = {}
        self.player_trap_history: Dict[str, List[str]] = {}  # 玩家陷阱触发历史
        self._init_traps()

    def _init_traps(self):
        """初始化所有陷阱"""
        dice_cost = get_config("game_config", "game.dice_cost", 10)
        self.traps[TrapType.FIREBALL] = TrapEffect(
            trap_type=TrapType.FIREBALL,
            description="火球砸出的坑洞让你无处下脚。",
            penalty_description="停止一回合（仍需消耗回合积分）\n强制骰子结果：下回合掷骰自动变为 [4, 5, 5, 5, 6, 6]\n无法主动结束：完成此惩罚前不得主动结束当前轮次",
            character_quote="为什么我的火球术不能骰出这种伤害啊?!!",
            first_time_penalty="fireball_curse",
            repeat_penalty=f"-{dice_cost}积分"
        )

        self.traps[TrapType.NO_LOOK_BACK] = TrapEffect(
            trap_type=TrapType.NO_LOOK_BACK,
            description="你感到身后一股寒意，当你战战兢兢地转过身试图搞清楚状况时，你发现在看到它脸的那一刻一切都已经晚了……",
            penalty_description="清空当前列进度回到上一个永久旗子位置或初始位置",
            character_quote="…话说回来，我有一计。",
            first_time_penalty="clear_current_column",
            repeat_penalty="clear_current_column"
        )

        self.traps[TrapType.RIVER_SPIRIT] = TrapEffect(
            trap_type=TrapType.RIVER_SPIRIT,
            description="河边的土地神要求你做出选择。",
            penalty_description=f"选择惩罚：\n1. 失去下回合行动权（-{dice_cost}积分）\n2. 当前轮次标记位置-1（所有临时标记后退一格）",
            character_quote="你选择相信我，还是相信你自己？",
            first_time_penalty="choice_penalty",
            repeat_penalty=f"-{dice_cost}积分"
        )

        self.traps[TrapType.SWEET_TALK] = TrapEffect(
            trap_type=TrapType.SWEET_TALK,
            description="甜言蜜语让你迷失方向。",
            penalty_description="迷惑效果：下回合必须选择与本回合不同的列进行移动\n如果无法满足条件，额外-15积分",
            character_quote="相信我，这条路更好走～",
            first_time_penalty="direction_confusion",
            repeat_penalty=f"-{dice_cost}积分"
        )

    def get_trap_for_position(self, column: int, position: int) -> Optional[TrapType]:
        """根据位置获取陷阱类型"""
        # 小数字列陷阱（第3-6列）
        if 3 <= column <= 6:
            return TrapType.FIREBALL

        # 其他陷阱随机分布（这里简化处理）
        trap_positions = {
            (7, 3): TrapType.NO_LOOK_BACK,
            (8, 4): TrapType.RIVER_SPIRIT,
            (12, 5): TrapType.SWEET_TALK,
            (15, 3): TrapType.NO_LOOK_BACK,
        }

        return trap_positions.get((column, position))

    def trigger_trap(self, player_id: str, trap_type: TrapType) -> Tuple[bool, str, Optional[dict]]:
        """触发陷阱"""
        if trap_type not in self.traps:
            return False, "未知陷阱类型", None

        trap = self.traps[trap_type]

        # 检查是否是首次触发
        player_history = self.player_trap_history.get(player_id, [])
        is_first_time = trap_type.value not in player_history

        # 记录触发历史
        if player_id not in self.player_trap_history:
            self.player_trap_history[player_id] = []
        self.player_trap_history[player_id].append(trap_type.value)

        message = f"🕳️ 触发陷阱：{trap_type.value}\n"
        message += f"📖 {trap.description}\n"
        message += f"💬 \"{trap.character_quote}\"\n\n"

        penalty_data = None

        if is_first_time:
            message += f"⚠️ 首次触发特殊惩罚：\n{trap.penalty_description}"
            penalty_data = self._apply_first_time_penalty(trap_type)
        else:
            message += f"💰 重复触发惩罚：{trap.repeat_penalty}"
            penalty_data = {"type": "score_penalty", "amount": 10}

        return True, message, penalty_data

    def _apply_first_time_penalty(self, trap_type: TrapType) -> dict:
        """应用首次触发惩罚"""
        if trap_type == TrapType.FIREBALL:
            return {
                "type": "fireball_curse",
                "skip_turn": True,
                "forced_dice": [4, 5, 5, 5, 6, 6],
                "no_voluntary_end": True
            }

        elif trap_type == TrapType.NO_LOOK_BACK:
            penalty_amount = random.randint(1, 5)
            special_trigger = random.random() < 0.15

            penalty_data = {
                "type": "no_look_back",
                "score_penalty": penalty_amount
            }

            if special_trigger:
                penalty_data["clear_markers"] = True

            return penalty_data

        elif trap_type == TrapType.RIVER_SPIRIT:
            dice_cost = get_config("game_config", "game.dice_cost", 10)
            return {
                "type": "river_spirit_choice",
                "choices": [
                    {"id": "skip_turn", "description": f"失去下回合行动权（-{dice_cost}积分）"},
                    {"id": "markers_back", "description": "当前轮次标记位置-1（所有临时标记后退一格）"}
                ]
            }

        elif trap_type == TrapType.SWEET_TALK:
            return {
                "type": "direction_confusion",
                "must_change_direction": True,
                "penalty_if_failed": 15
            }

        return {"type": "unknown"}

    def get_all_traps(self) -> List[TrapEffect]:
        """获取所有陷阱信息"""
        return list(self.traps.values())

    def get_player_trap_history(self, player_id: str) -> List[str]:
        """获取玩家陷阱触发历史"""
        return self.player_trap_history.get(player_id, [])

    def get_trap_by_name(self, trap_name: str) -> Optional[TrapType]:
        """根据陷阱名称获取陷阱类型"""
        for trap_type in TrapType:
            if trap_type.value == trap_name:
                return trap_type
        return None