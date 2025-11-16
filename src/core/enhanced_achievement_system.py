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
                # 保存额外的配置数据
                if not hasattr(self, 'achievement_config'):
                    self.achievement_config = {}
                self.achievement_config[achievement_id] = achievement_data
                self.achievements[achievement_id] = achievement

        except Exception as e:
            print(f"加载成就配置失败: {e}")

    def _format_conditions(self, conditions: List[Dict]) -> str:
        """将条件列表格式化为字符串（用于显示）"""
        if not conditions:
            return "特殊条件"

        condition_texts = []
        for condition in conditions:
            ctype = condition["type"]
            if ctype == "event_count":
                condition_texts.append(f'{condition["event"]} {condition["count"]}次')
            elif ctype == "trap_triggered":
                condition_texts.append(f'触发{condition["trap_name"]}陷阱')
            elif ctype == "game_complete_count":
                if condition.get("exact", False):
                    condition_texts.append(f'第{condition["count"]}次通关游戏')
                else:
                    condition_texts.append(f'通关游戏{condition["count"]}次')
            elif ctype == "first_complete_column":
                condition_texts.append('首次完成任意列')
            elif ctype == "avoid_trap_penalty":
                condition_texts.append('在陷阱后触发奖励/规避惩罚')
            elif ctype == "hidden_achievements_count":
                condition_texts.append(f'解锁{condition["count"]}个隐藏成就')
            elif ctype == "avoid_trap_penalty_count":
                condition_texts.append(f'{condition["count"]}次规避陷阱惩罚')
            elif ctype == "consecutive_peaceful_choices":
                condition_texts.append(f'连续{condition["count"]}次和平选择')
            elif ctype == "consecutive_special_effects":
                condition_texts.append(f'连续{condition["count"]}次触发特殊效果')
            elif ctype == "collection_complete":
                items = ", ".join(condition.get("items_required", []))
                condition_texts.append(f'收集完成: {items}')
            elif ctype == "single_turn_complete":
                condition_texts.append('单回合完成列')
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
                # 使用新的带奖励处理的解锁方法
                result = self.unlock_achievement_with_reward(
                    achievement_id,
                    event.player_id,
                    event.timestamp.isoformat()
                )

                if result["success"]:
                    print(f"🎉 成就解锁: {achievement_data['name']}")
                    if result["reward_result"]["messages"]:
                        for msg in result["reward_result"]["messages"]:
                            print(f"   {msg}")

                    # 发出成就解锁事件
                    from .event_system import emit_game_event, GameEventType
                    emit_game_event(
                        GameEventType.ACHIEVEMENT_UNLOCKED,
                        event.player_id,
                        {
                            "achievement_id": achievement_id,
                            "achievement_name": achievement_data["name"],
                            "is_hidden": result.get("is_hidden", False)
                        },
                        event.session_id
                    )

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
        elif condition_type == "game_complete_count":
            return self._check_game_complete_count_condition(condition, event)
        elif condition_type == "first_complete_column":
            return self._check_first_complete_column_condition(condition, event)
        elif condition_type == "avoid_trap_penalty":
            return self._check_avoid_trap_penalty_condition(condition, event)
        elif condition_type == "hidden_achievements_count":
            return self._check_hidden_achievements_count_condition(condition, event)
        elif condition_type == "avoid_trap_penalty_count":
            return self._check_avoid_trap_penalty_count_condition(condition, event)
        elif condition_type == "consecutive_peaceful_choices":
            return self._check_consecutive_peaceful_choices_condition(condition, event)
        elif condition_type == "consecutive_special_effects":
            return self._check_consecutive_special_effects_condition(condition, event)
        elif condition_type == "collection_complete":
            return self._check_collection_complete_condition(condition, event)

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

    def _check_game_complete_count_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查游戏完成次数条件"""
        if event.event_type != GameEventType.GAME_COMPLETED:
            return False

        required_count = condition.get("count", 1)
        exact_match = condition.get("exact", False)

        # 从数据库获取玩家的完成次数
        from ..database.database import DatabaseManager
        db_manager = DatabaseManager()
        player = db_manager.get_player(event.player_id)

        if not player:
            return False

        games_won = player.games_won

        if exact_match:
            return games_won == required_count
        else:
            return games_won >= required_count

    def _check_first_complete_column_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查首次完成任意列条件"""
        if event.event_type != GameEventType.COLUMN_COMPLETED:
            return False

        # 从数据库检查这是否是玩家的第一次列完成
        from ..database.database import DatabaseManager
        db_manager = DatabaseManager()

        # 检查first_completions表
        # 如果这是第一次完成任意列，这个事件应该是触发点
        is_first = event.get("is_first_completion", False)

        return is_first

    def _check_avoid_trap_penalty_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查规避陷阱惩罚条件"""
        # 这个需要检测玩家触发陷阱后立即获得奖励或规避负面影响
        # 可以通过检查事件序列来判断

        # 检查玩家是否在触发陷阱后立即触发了奖励事件
        if event.event_type in [GameEventType.SCORE_GAINED, GameEventType.ITEM_PURCHASED]:
            # 获取最近的事件
            recent_events = self.event_system.get_player_events(event.player_id, limit=10)

            # 查找最近是否有陷阱触发
            for i, evt in enumerate(reversed(recent_events)):
                if evt.event_type == GameEventType.TRAP_TRIGGERED:
                    # 检查陷阱触发和当前奖励事件之间的时间差
                    time_diff = (event.timestamp - evt.timestamp).total_seconds()
                    if time_diff <= 60:  # 60秒内
                        return True
                    break

        return False

    def _check_hidden_achievements_count_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查解锁隐藏成就数量条件"""
        if event.event_type != GameEventType.ACHIEVEMENT_UNLOCKED:
            return False

        required_count = condition.get("count", 1)

        # 统计玩家已解锁的隐藏成就数量
        config_achievements = self._get_config_achievements()
        unlocked_hidden_count = 0

        for achievement_id, achievement_data in config_achievements.items():
            if achievement_data.get("is_hidden", False):
                if self.check_achievement_unlocked(achievement_id):
                    unlocked_hidden_count += 1

        return unlocked_hidden_count >= required_count

    def _check_avoid_trap_penalty_count_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查多次规避陷阱惩罚条件"""
        required_count = condition.get("count", 2)

        # 追踪玩家规避陷阱惩罚的次数
        player_id = event.player_id
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}

        if "avoid_trap_penalty_count" not in self.player_progress[player_id]:
            self.player_progress[player_id]["avoid_trap_penalty_count"] = 0

        # 如果当前事件满足规避条件，增加计数
        if self._check_avoid_trap_penalty_condition(condition, event):
            self.player_progress[player_id]["avoid_trap_penalty_count"] += 1

        return self.player_progress[player_id]["avoid_trap_penalty_count"] >= required_count

    def _check_consecutive_peaceful_choices_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查连续和平选择条件"""
        required_count = condition.get("count", 3)
        player_id = event.player_id

        # 追踪玩家连续和平选择次数
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}

        if "consecutive_peaceful" not in self.player_progress[player_id]:
            self.player_progress[player_id]["consecutive_peaceful"] = 0

        # 检查当前事件是否是和平选择
        is_peaceful = event.get("choice_type") == "peaceful" and event.get("result") == "nothing"

        if is_peaceful:
            self.player_progress[player_id]["consecutive_peaceful"] += 1
        else:
            # 如果不是和平选择，重置计数
            if event.get("is_encounter_choice", False):
                self.player_progress[player_id]["consecutive_peaceful"] = 0

        return self.player_progress[player_id]["consecutive_peaceful"] >= required_count

    def _check_consecutive_special_effects_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查连续触发特殊效果条件"""
        required_count = condition.get("count", 3)
        player_id = event.player_id

        # 追踪玩家连续特殊效果次数
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}

        if "consecutive_special_effects" not in self.player_progress[player_id]:
            self.player_progress[player_id]["consecutive_special_effects"] = 0

        # 检查当前事件是否触发了特殊效果
        is_special = event.get("choice_type") == "special" and event.get("has_effect", False)

        if is_special:
            self.player_progress[player_id]["consecutive_special_effects"] += 1
        else:
            # 如果不是特殊效果，重置计数
            if event.get("is_encounter_choice", False):
                self.player_progress[player_id]["consecutive_special_effects"] = 0

        return self.player_progress[player_id]["consecutive_special_effects"] >= required_count

    def _check_collection_complete_condition(self, condition: Dict, event: GameEvent) -> bool:
        """检查收集完成条件"""
        items_required = condition.get("items_required", [])

        # 这需要从数据库或游戏状态检查玩家是否收集了所有必需项目
        from ..database.database import DatabaseManager
        db_manager = DatabaseManager()

        player_id = event.player_id

        # 检查每个必需项目
        for requirement in items_required:
            if requirement == "all_items":
                # 检查玩家是否拥有所有道具
                # TODO: 需要从道具系统获取所有道具列表并检查
                pass
            elif requirement == "all_maps":
                # 检查玩家是否探索了所有地图区域
                # TODO: 需要从地图系统获取探索进度
                pass

        # 目前返回False，等待实现完整的收集系统
        return False

    def is_achievement_hidden(self, achievement_id: str) -> bool:
        """检查成就是否为隐藏成就"""
        if not hasattr(self, 'achievement_config'):
            return False

        achievement_data = self.achievement_config.get(achievement_id, {})
        return achievement_data.get("is_hidden", False)

    def get_visible_achievements(self) -> List[Achievement]:
        """获取可见的成就（排除未解锁的隐藏成就）"""
        visible = []
        for achievement_id, achievement in self.achievements.items():
            # 如果成就已解锁，或者不是隐藏成就，则显示
            if achievement.is_unlocked or not self.is_achievement_hidden(achievement_id):
                visible.append(achievement)
        return visible

    def process_achievement_reward(self, achievement_id: str, player_id: str) -> Dict[str, Any]:
        """处理成就奖励"""
        if not hasattr(self, 'achievement_config'):
            return {"success": False, "message": "成就配置未加载"}

        achievement_data = self.achievement_config.get(achievement_id, {})
        reward_type = achievement_data.get("reward_type", "item")
        reward_data = achievement_data.get("reward_data", {})

        result = {
            "success": True,
            "reward_type": reward_type,
            "messages": []
        }

        if reward_type == "mixed":
            # 处理混合奖励（游戏内 + 现实奖励）
            # 游戏内奖励
            if "score" in reward_data:
                from ..database.database import DatabaseManager
                db_manager = DatabaseManager()
                player = db_manager.get_player(player_id)
                if player:
                    db_manager.update_player_score(player_id, reward_data["score"], f"成就奖励：{achievement_data['name']}")
                    result["messages"].append(f"✨ 获得 {reward_data['score']} 积分")

            if "item" in reward_data:
                # TODO: 添加道具到玩家库存
                result["messages"].append(f"🎁 获得道具：{reward_data['item']}")

            # 现实奖励
            if "real_world" in reward_data:
                result["messages"].append(f"🎊 现实奖励：{reward_data['real_world']}")
                result["has_real_world_reward"] = True

        elif reward_type == "score":
            # 纯积分奖励
            from ..database.database import DatabaseManager
            db_manager = DatabaseManager()
            score_amount = reward_data.get("score", 0)
            db_manager.update_player_score(player_id, score_amount, f"成就奖励：{achievement_data['name']}")
            result["messages"].append(f"✨ 获得 {score_amount} 积分")

        elif reward_type == "item":
            # 纯道具奖励
            # TODO: 添加道具到玩家库存
            item_name = reward_data.get("item", achievement_data.get("reward_description", "神秘道具"))
            result["messages"].append(f"🎁 获得道具：{item_name}")

        elif reward_type == "title":
            # 称号奖励
            title = reward_data.get("title", achievement_data.get("reward_description", "特殊称号"))
            result["messages"].append(f"👑 获得称号：{title}")

        elif reward_type == "none":
            # 无奖励
            result["messages"].append("😅 这次没有奖励哦～")

        return result

    def unlock_achievement_with_reward(self, achievement_id: str, player_id: str, unlock_date: str = None) -> Dict[str, Any]:
        """解锁成就并处理奖励"""
        # 解锁成就
        success = self.unlock_achievement(achievement_id, unlock_date)

        if not success:
            return {"success": False, "message": "成就解锁失败"}

        # 处理奖励
        reward_result = self.process_achievement_reward(achievement_id, player_id)

        achievement = self.achievements.get(achievement_id)
        if not achievement:
            return {"success": False, "message": "成就不存在"}

        return {
            "success": True,
            "achievement": achievement,
            "reward_result": reward_result,
            "is_hidden": self.is_achievement_hidden(achievement_id)
        }