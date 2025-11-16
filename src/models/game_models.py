"""
Can't Stop游戏核心数据模型
"""

from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import random


class Faction(Enum):
    """阵营枚举"""
    ADOPTER = "收养人"
    AONRETH = "Aeonreth"


class GameState(Enum):
    """游戏状态枚举"""
    WAITING = "waiting"          # 等待玩家
    ACTIVE = "active"            # 游戏进行中
    PAUSED = "paused"            # 暂停
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


class TurnState(Enum):
    """轮次状态枚举"""
    DICE_ROLL = "dice_roll"      # 掷骰阶段
    MOVE_MARKERS = "move_markers" # 移动标记阶段
    DECISION = "decision"         # 决策阶段
    WAITING_FOR_SUMMIT_CONFIRMATION = "waiting_for_summit_confirmation"  # 等待登顶确认
    ENDED = "ended"              # 轮次结束
    WAITING_FOR_CHECKIN = "waiting_for_checkin"  # 等待打卡


class EventType(Enum):
    """事件类型枚举"""
    TRAP = "trap"
    ITEM = "item"
    ENCOUNTER = "encounter"
    REWARD = "reward"


@dataclass
class MapConfig:
    """地图配置"""
    # 列号到格子数的映射 (3-18列)
    COLUMN_LENGTHS: Dict[int, int] = field(default_factory=lambda: {
        3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
        9: 9, 10: 10, 11: 10, 12: 9, 13: 8,
        14: 7, 15: 6, 16: 5, 17: 4, 18: 3
    })

    def get_column_length(self, column: int) -> int:
        """获取指定列的长度"""
        return self.COLUMN_LENGTHS.get(column, 0)

    def is_valid_column(self, column: int) -> bool:
        """检查列号是否有效"""
        return column in self.COLUMN_LENGTHS


@dataclass
class DiceRoll:
    """骰子投掷结果"""
    results: List[int]
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if len(self.results) != 6:
            raise ValueError("骰子结果必须是6个数字")
        if not all(1 <= r <= 6 for r in self.results):
            raise ValueError("每个骰子结果必须在1-6之间")

    def get_possible_combinations(self) -> List[Tuple[int, int]]:
        """获取所有可能的数字组合"""
        combinations = []
        used = set()

        # 生成所有可能的3+3组合
        for i in range(6):
            for j in range(i+1, 6):
                for k in range(j+1, 6):
                    group1 = [i, j, k]
                    group2 = [x for x in range(6) if x not in group1]

                    sum1 = sum(self.results[idx] for idx in group1)
                    sum2 = sum(self.results[idx] for idx in group2)

                    # 确保组合在有效范围内(3-18)
                    if 3 <= sum1 <= 18 and 3 <= sum2 <= 18:
                        combo = tuple(sorted([sum1, sum2]))
                        if combo not in used:
                            combinations.append(combo)
                            used.add(combo)

        return sorted(combinations)


@dataclass
class TemporaryMarker:
    """临时标记"""
    column: int
    position: int

    def __post_init__(self):
        if not MapConfig().is_valid_column(self.column):
            raise ValueError(f"无效的列号: {self.column}")
        if self.position < 0:
            raise ValueError("位置不能为负数")


@dataclass
class PlayerProgress:
    """玩家进度"""
    permanent_progress: Dict[int, int] = field(default_factory=dict)  # 列号 -> 永久进度
    completed_columns: Set[int] = field(default_factory=set)  # 已完成的列

    def get_progress(self, column: int) -> int:
        """获取指定列的永久进度"""
        return self.permanent_progress.get(column, 0)

    def set_progress(self, column: int, progress: int):
        """设置指定列的进度"""
        if not MapConfig().is_valid_column(column):
            raise ValueError(f"无效的列号: {column}")

        max_length = MapConfig().get_column_length(column)
        if progress >= max_length:
            self.completed_columns.add(column)
            self.permanent_progress[column] = max_length
        else:
            self.permanent_progress[column] = max(0, progress)

    def is_completed(self, column: int) -> bool:
        """检查指定列是否已完成"""
        return column in self.completed_columns

    def get_completed_count(self) -> int:
        """获取已完成列的数量"""
        return len(self.completed_columns)

    def is_winner(self) -> bool:
        """检查是否获胜(3列登顶)"""
        return self.get_completed_count() >= 3


@dataclass
class Player:
    """玩家类"""
    player_id: str
    username: str
    faction: Faction
    current_score: int = 0
    total_score: int = 0
    games_played: int = 0
    games_won: int = 0
    total_dice_rolls: int = 0  # 总掷骰次数
    total_turns: int = 0       # 总轮次数
    progress: PlayerProgress = field(default_factory=PlayerProgress)
    inventory: List[str] = field(default_factory=list)
    achievements: Set[str] = field(default_factory=set)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    def add_score(self, amount: int, source: str = "unknown"):
        """增加积分"""
        # 如果是负数，确保当前积分不会低于0
        if amount < 0:
            actual_deduction = min(abs(amount), self.current_score)
            self.current_score -= actual_deduction
            # total_score 记录历史总获得积分，不扣减
            if amount > 0:
                self.total_score += amount
        else:
            self.current_score += amount
            self.total_score += amount
        self.last_active = datetime.now()

    def spend_score(self, amount: int, purpose: str = "unknown") -> bool:
        """消耗积分"""
        if self.current_score >= amount:
            self.current_score -= amount
            self.last_active = datetime.now()
            return True
        return False

    def add_item(self, item_name: str):
        """添加道具到库存"""
        self.inventory.append(item_name)

    def use_item(self, item_name: str) -> bool:
        """使用道具"""
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False

    def unlock_achievement(self, achievement_name: str):
        """解锁成就"""
        self.achievements.add(achievement_name)


@dataclass
class GameSession:
    """游戏会话"""
    session_id: str
    player_id: str
    state: GameState = GameState.ACTIVE
    turn_state: TurnState = TurnState.DICE_ROLL
    turn_number: int = 1
    temporary_markers: List[TemporaryMarker] = field(default_factory=list)
    current_dice: Optional[DiceRoll] = None
    first_turn: bool = True  # 是否首轮
    needs_checkin: bool = False  # 是否需要打卡
    forced_dice_result: Optional[List[int]] = None  # 强制骰子结果
    pending_summit_columns: List[int] = field(default_factory=list)  # 待确认的登顶列
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_temporary_marker(self, column: int, position: int) -> bool:
        """添加临时标记"""
        if len(self.temporary_markers) >= 3:
            return False

        # 检查该列是否已有标记
        for marker in self.temporary_markers:
            if marker.column == column:
                return False

        self.temporary_markers.append(TemporaryMarker(column, position))
        self.updated_at = datetime.now()
        return True

    def remove_temporary_marker(self, column: int) -> bool:
        """移除临时标记"""
        for i, marker in enumerate(self.temporary_markers):
            if marker.column == column:
                self.temporary_markers.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def get_temporary_marker(self, column: int) -> Optional[TemporaryMarker]:
        """获取指定列的临时标记"""
        for marker in self.temporary_markers:
            if marker.column == column:
                return marker
        return None

    def clear_temporary_markers(self):
        """清空所有临时标记"""
        self.temporary_markers.clear()
        self.updated_at = datetime.now()

    def has_available_marker_slots(self) -> bool:
        """检查是否还有可用的标记位置"""
        return len(self.temporary_markers) < 3


@dataclass
class MapEvent:
    """地图事件"""
    event_id: str
    column: int
    position: int
    event_type: EventType
    name: str
    description: str
    faction_specific: Optional[Faction] = None
    is_triggered: bool = False
    triggered_by: Optional[str] = None  # 玩家ID
    triggered_at: Optional[datetime] = None

    def can_trigger(self, player: Player) -> bool:
        """检查玩家是否能触发此事件"""
        if self.is_triggered:
            return False

        if self.faction_specific and player.faction != self.faction_specific:
            return False

        return True

    def trigger(self, player_id: str):
        """触发事件"""
        self.is_triggered = True
        self.triggered_by = player_id
        self.triggered_at = datetime.now()


@dataclass
class GameStatistics:
    """游戏统计"""
    total_games: int = 0
    total_players: int = 0
    active_sessions: int = 0
    completed_games: int = 0
    average_game_duration: float = 0.0
    most_popular_columns: Dict[int, int] = field(default_factory=dict)
    achievement_unlock_count: Dict[str, int] = field(default_factory=dict)