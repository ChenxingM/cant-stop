"""
遭遇事件系统
处理玩家与遭遇事件的交互
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
from pathlib import Path


@dataclass
class EncounterChoice:
    """遭遇选项"""
    name: str
    type: str  # peaceful, normal, special
    effect: str
    message: str
    cost: int = 0
    cost_item: Optional[str] = None
    game_effect: Optional[Dict[str, Any]] = None
    follow_up: Optional[Dict[str, Any]] = None


@dataclass
class EncounterEvent:
    """遭遇事件"""
    id: int
    name: str
    description: str
    quote: Optional[str]
    choices: List[EncounterChoice]


@dataclass
class PendingEncounter:
    """等待处理的遭遇"""
    player_id: str
    encounter_name: str
    encounter_data: EncounterEvent
    triggered_at: datetime = field(default_factory=datetime.now)
    follow_up_pending: Optional[Dict[str, Any]] = None


class EncounterManager:
    """遭遇事件管理器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = "config/encounters.json"

        self.config_path = Path(config_path)
        self.encounters: Dict[str, EncounterEvent] = {}
        self.pending_encounters: Dict[str, PendingEncounter] = {}  # player_id -> pending
        self.player_choices: Dict[str, List[str]] = {}  # player_id -> choice history

        self.load_encounters()

    def load_encounters(self):
        """加载遭遇配置"""
        try:
            if not self.config_path.exists():
                print(f"遭遇配置文件不存在: {self.config_path}")
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for name, config in data.get("encounters", {}).items():
                choices = []
                for choice_data in config.get("choices", []):
                    choice = EncounterChoice(
                        name=choice_data["name"],
                        type=choice_data["type"],
                        effect=choice_data["effect"],
                        message=choice_data["message"],
                        cost=choice_data.get("cost", 0),
                        cost_item=choice_data.get("cost_item"),
                        game_effect=choice_data.get("game_effect"),
                        follow_up=choice_data.get("follow_up")
                    )
                    choices.append(choice)

                encounter = EncounterEvent(
                    id=config["id"],
                    name=config["name"],
                    description=config["description"],
                    quote=config.get("quote"),
                    choices=choices
                )
                self.encounters[name] = encounter

            print(f"成功加载 {len(self.encounters)} 个遭遇事件")

        except Exception as e:
            print(f"加载遭遇配置失败: {e}")

    def trigger_encounter(self, player_id: str, encounter_name: str) -> Tuple[bool, str]:
        """触发遭遇事件"""
        if encounter_name not in self.encounters:
            return False, f"遭遇 '{encounter_name}' 不存在"

        encounter = self.encounters[encounter_name]

        # 构建遭遇消息
        message = f"👥 触发遭遇：{encounter.name}\n"
        message += f"📖 {encounter.description}\n"
        if encounter.quote:
            message += f"💬 \"{encounter.quote}\"\n"
        message += "\n🎭 请选择你的行动：\n"

        for i, choice in enumerate(encounter.choices, 1):
            choice_text = f"{i}. {choice.name}"
            if choice.cost > 0:
                choice_text += f"（消耗{choice.cost}积分）"
            if choice.cost_item:
                choice_text += f"（需要{choice.cost_item}）"
            message += choice_text + "\n"

        message += f"\n💡 使用格式：{choice.name}"

        # 保存待处理的遭遇
        pending = PendingEncounter(
            player_id=player_id,
            encounter_name=encounter_name,
            encounter_data=encounter
        )
        self.pending_encounters[player_id] = pending

        return True, message

    def process_choice(self, player_id: str, choice_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """处理玩家的遭遇选择"""
        if player_id not in self.pending_encounters:
            return False, "你当前没有待处理的遭遇事件", {}

        pending = self.pending_encounters[player_id]
        encounter = pending.encounter_data

        # 查找选择
        selected_choice = None
        for choice in encounter.choices:
            if choice.name == choice_name:
                selected_choice = choice
                break

        if not selected_choice:
            return False, f"无效的选择：{choice_name}", {}

        # 记录选择类型（用于成就追踪）
        if player_id not in self.player_choices:
            self.player_choices[player_id] = []
        self.player_choices[player_id].append(selected_choice.type)

        # 移除pending（除非有follow_up）
        if not selected_choice.follow_up:
            del self.pending_encounters[player_id]
        else:
            # 设置follow_up等待
            pending.follow_up_pending = selected_choice.follow_up

        # 返回选择结果
        result_data = {
            "choice_type": selected_choice.type,
            "effect": selected_choice.effect,
            "cost": selected_choice.cost,
            "cost_item": selected_choice.cost_item,
            "game_effect": selected_choice.game_effect or {}
        }

        return True, selected_choice.message, result_data

    def process_follow_up(self, player_id: str, response: str) -> Tuple[bool, str, Dict[str, Any]]:
        """处理follow_up响应"""
        if player_id not in self.pending_encounters:
            return False, "", {}

        pending = self.pending_encounters[player_id]
        if not pending.follow_up_pending:
            return False, "", {}

        follow_up = pending.follow_up_pending

        # 检查响应是否匹配
        if response.strip() == follow_up.get("trigger"):
            reward = follow_up.get("reward", {})
            message = reward.get("message", "")

            # 清除pending
            del self.pending_encounters[player_id]

            return True, message, reward

        # 检查超时
        elapsed = (datetime.now() - pending.triggered_at).total_seconds()
        if elapsed > follow_up.get("timeout", 60):
            del self.pending_encounters[player_id]
            return False, "", {}

        return False, "", {}

    def get_consecutive_choice_type(self, player_id: str, choice_type: str) -> int:
        """获取连续选择同一类型的次数"""
        if player_id not in self.player_choices:
            return 0

        choices = self.player_choices[player_id]
        count = 0

        # 从后往前数连续的同类型选择
        for choice in reversed(choices):
            if choice == choice_type:
                count += 1
            else:
                break

        return count

    def clear_choice_history(self, player_id: str):
        """清除选择历史"""
        if player_id in self.player_choices:
            del self.player_choices[player_id]

    def roll_dice_check(self, target: int, dice_type: str = "d6") -> Tuple[int, bool]:
        """骰子判定"""
        if dice_type == "d6":
            result = random.randint(1, 6)
        elif dice_type == "d20":
            result = random.randint(1, 20)
        elif dice_type.startswith("d"):
            sides = int(dice_type[1:])
            result = random.randint(1, sides)
        else:
            result = random.randint(1, 6)

        success = result > target if ">" in str(target) else result >= target
        return result, success


# 全局遭遇管理器
_global_encounter_manager = None


def get_encounter_manager() -> EncounterManager:
    """获取全局遭遇管理器"""
    global _global_encounter_manager
    if _global_encounter_manager is None:
        _global_encounter_manager = EncounterManager()
    return _global_encounter_manager
