"""
增强的成就系统 - 支持配置文件驱动和事件自动检测
向后兼容原有的 achievement_system.py
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .achievement_system import AchievementSystem, Achievement, AchievementCategory
from .event_system import GameEventSystem, GameEvent, GameEventType, get_event_system


@dataclass
class AchievementCondition:
    """成就解锁条件"""
    condition_type: str
    parameters: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AchievementCondition':
        return cls(
            condition_type=data["type"],
            parameters={k: v for k, v in data.items() if k != "type"}
        )


class EnhancedAchievementSystem(AchievementSystem):
    """增强的成就系统，向后兼容原系统"""

    def __init__(self, config_file: str = "config/achievements.json"):
        # 初始化父类（保持向后兼容）
        super().__init__()

        self.config_file = config_file
        self.event_system = get_event_system()
        self.player_progress: Dict[str, Dict[str, Any]] = {}  # 玩家进度追踪

        # 加载配置文件中的成就（如果存在）
        self._load_achievements_from_config()

        # 设置事件监听器
        self._setup_event_listeners()

    def _load_achievements_from_config(self):
        """从配置文件加载成就（保持原有成就不变）"""
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for achievement_id, achievement_data in config.get("achievements", {}).items():
                # 如果成就已存在（硬编码的），跳过
                if achievement_id in self.achievements:
                    continue

                # 从配置文件创建新成就
                category = getattr(AchievementCategory, achievement_data.get("category", "SPECIAL"))
                achievement = Achievement(
                    id=achievement_id,
                    name=achievement_data["name"],
                    description=achievement_data["description"],
                    category=category,
                    reward_description=achievement_data["reward_description"],
                    unlock_condition=self._format_conditions(achievement_data.get("conditions", []))
                )
                self.achievements[achievement_id] = achievement

        except Exception as e:
            print(f"加载成就配置失败: {e}")

    def _format_conditions(self, conditions: List[Dict]) -> str:
        """将条件列表格式化为字符串（用于显示）"""
        if not conditions:
            return "特殊条件"

        condition_texts = []
        for condition in conditions:
            if condition["type"] == "event_count":
                condition_texts.append(f'{condition["event"]} {condition["count"]}次')
            elif condition["type"] == "trap_triggered":
                condition_texts.append(f'触发{condition["trap_name"]}陷阱')
            else:
                condition_texts.append(condition.get("description", "特殊条件"))

        return " | ".join(condition_texts)

    def _setup_event_listeners(self):
        """设置事件监听器"""
        # 监听所有游戏事件进行成就检测
        for event_type in GameEventType:
            self.event_system.subscribe(event_type, self._on_game_event)

    def _on_game_event(self, event: GameEvent):
        """处理游戏事件，检测成就解锁"""
        # 只处理配置文件中的成就（保持原有成就系统不变）
        config_achievements = self._get_config_achievements()

        for achievement_id, achievement_data in config_achievements.items():
            if self.check_achievement_unlocked(achievement_id):
                continue  # 已解锁的成就跳过

            if self._check_achievement_conditions(achievement_id, achievement_data, event):
                self.unlock_achievement(achievement_id, event.timestamp.isoformat())
                print(f"🎉 成就解锁: {achievement_data['name']}")

    def _get_config_achievements(self) -> Dict[str, Dict]:
        """获取配置文件中的成就"""
        if not os.path.exists(self.config_file):
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get("achievements", {})
        except:
            return {}

    def _check_achievement_conditions(self, achievement_id: str, achievement_data: Dict, event: GameEvent) -> bool:
        """检查成就解锁条件"""
        conditions = achievement_data.get("conditions", [])

        for condition in conditions:
            if not self._check_single_condition(condition, event):
                return False

        return True

    def _check_single_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查单个条件"""
        condition_type = condition["type"]

        if condition_type == "event_count":
            return self._check_event_count_condition(condition, event)
        elif condition_type == "trap_triggered":
            return self._check_trap_triggered_condition(condition, event)
        elif condition_type == "single_turn_complete":
            return self._check_single_turn_complete_condition(condition, event)
        elif condition_type == "complex":
            return self._check_complex_condition(condition, event)

        return False

    def _check_event_count_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查事件计数条件"""
        target_event = condition["event"]
        required_count = condition["count"]
        scope = condition.get("scope", "lifetime")

        # 将条件中的事件名映射到实际的事件类型
        event_mapping = {
            "player_died": GameEventType.PLAYER_DIED,
            "trap_first_time": GameEventType.TRAP_FIRST_TIME,
            "trap_triggered": GameEventType.TRAP_TRIGGERED,
            "column_completed": GameEventType.COLUMN_COMPLETED
        }

        mapped_event = event_mapping.get(target_event)
        if not mapped_event:
            return False

        # 统计事件次数
        if scope == "lifetime":
            count = self.event_system.count_player_events(event.player_id, mapped_event)
        elif scope == "session":
            # 当前会话内的事件
            session_start = datetime.now() - timedelta(hours=24)  # 简化：24小时内
            count = self.event_system.count_player_events(event.player_id, mapped_event, session_start)
        else:
            count = 0

        return count >= required_count

    def _check_trap_triggered_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查陷阱触发条件"""
        if event.event_type != GameEventType.TRAP_TRIGGERED:
            return False

        required_trap = condition.get("trap_name")
        if not required_trap:
            return True

        triggered_trap = event.get("trap_name")
        return triggered_trap == required_trap

    def _check_single_turn_complete_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查一回合通关条件"""
        if event.event_type != GameEventType.COLUMN_COMPLETED:
            return False

        # 检查是否在单回合内完成
        starting_progress = event.get("starting_progress", 0)
        return starting_progress == 0

    def _check_complex_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查复杂条件（需要自定义逻辑）"""
        check_function = condition.get("check_function")

        if check_function == "check_self_cruise":
            # 使用道具时触发陷阱的逻辑
            if event.event_type == GameEventType.TRAP_TRIGGERED:
                return event.get("triggered_during_item_use", False)

        return False

    def add_achievement_from_config(self, achievement_id: str, achievement_data: Dict[str, Any]) -> bool:
        """从配置添加新成就（运行时添加）"""
        try:
            category = getattr(AchievementCategory, achievement_data.get("category", "SPECIAL"))
            achievement = Achievement(
                id=achievement_id,
                name=achievement_data["name"],
                description=achievement_data["description"],
                category=category,
                reward_description=achievement_data["reward_description"],
                unlock_condition=self._format_conditions(achievement_data.get("conditions", []))
            )
            self.achievements[achievement_id] = achievement
            return True
        except Exception as e:
            print(f"添加成就失败: {e}")
            return False

    def save_achievement_to_config(self, achievement_id: str, achievement_data: Dict[str, Any]) -> bool:
        """将新成就保存到配置文件"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            if "achievements" not in config:
                config["achievements"] = {}

            config["achievements"][achievement_id] = achievement_data

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"保存成就配置失败: {e}")
            return False

    def get_player_progress(self, player_id: str) -> Dict[str, Any]:
        """获取玩家成就进度"""
        return self.player_progress.get(player_id, {})

    def update_player_progress(self, player_id: str, progress_data: Dict[str, Any]):
        """更新玩家成就进度"""
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}
        self.player_progress[player_id].update(progress_data)