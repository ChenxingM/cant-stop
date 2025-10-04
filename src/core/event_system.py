"""
游戏事件系统 - 用于触发成就检测和其他自动化逻辑
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GameEventType(Enum):
    """游戏事件类型"""
    # 游戏进程事件
    GAME_STARTED = "game_started"
    TURN_STARTED = "turn_started"
    DICE_ROLLED = "dice_rolled"
    MARKERS_MOVED = "markers_moved"
    TURN_ENDED = "turn_ended"
    GAME_COMPLETED = "game_completed"

    # 陷阱相关事件
    TRAP_TRIGGERED = "trap_triggered"
    TRAP_FIRST_TIME = "trap_first_time"
    TRAP_REPEAT = "trap_repeat"
    TRAP_CHOICE_MADE = "trap_choice_made"

    # 进度相关事件
    COLUMN_COMPLETED = "column_completed"
    PROGRESS_UPDATED = "progress_updated"
    PLAYER_DIED = "player_died"

    # 积分相关事件
    SCORE_GAINED = "score_gained"
    SCORE_LOST = "score_lost"
    ITEM_PURCHASED = "item_purchased"
    ITEM_USED = "item_used"

    # 成就相关事件
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    FIRST_TIME_ACHIEVEMENT = "first_time_achievement"


@dataclass
class GameEvent:
    """游戏事件数据结构"""
    event_type: GameEventType
    player_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None

    def get(self, key: str, default=None):
        """获取事件数据"""
        return self.data.get(key, default)


class GameEventSystem:
    """游戏事件系统"""

    def __init__(self):
        self.listeners: Dict[GameEventType, List[Callable]] = {}
        self.event_history: List[GameEvent] = []
        self.max_history_size = 1000  # 限制历史记录大小

    def subscribe(self, event_type: GameEventType, callback: Callable[[GameEvent], None]):
        """订阅事件"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type: GameEventType, callback: Callable):
        """取消订阅"""
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)

    def emit(self, event_type: GameEventType, player_id: str, data: Dict[str, Any] = None, session_id: str = None):
        """发布事件"""
        event = GameEvent(
            event_type=event_type,
            player_id=player_id,
            data=data or {},
            session_id=session_id
        )

        # 记录事件历史
        self._add_to_history(event)

        # 通知所有监听器
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"事件处理器错误 {event_type}: {e}")

    def _add_to_history(self, event: GameEvent):
        """添加到历史记录"""
        self.event_history.append(event)

        # 限制历史记录大小
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]

    def get_player_events(self, player_id: str, event_type: GameEventType = None, limit: int = None) -> List[GameEvent]:
        """获取玩家的事件历史"""
        events = [e for e in self.event_history if e.player_id == player_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if limit:
            events = events[-limit:]

        return events

    def count_player_events(self, player_id: str, event_type: GameEventType, since: datetime = None) -> int:
        """统计玩家特定事件次数"""
        events = self.get_player_events(player_id, event_type)

        if since:
            events = [e for e in events if e.timestamp >= since]

        return len(events)

    def clear_history(self):
        """清空事件历史"""
        self.event_history.clear()


# 全局事件系统实例
_global_event_system = None

def get_event_system() -> GameEventSystem:
    """获取全局事件系统实例"""
    global _global_event_system
    if _global_event_system is None:
        _global_event_system = GameEventSystem()
    return _global_event_system

def emit_game_event(event_type: GameEventType, player_id: str, data: Dict[str, Any] = None, session_id: str = None):
    """便捷函数：发布游戏事件"""
    get_event_system().emit(event_type, player_id, data, session_id)