"""
数据库模型定义
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, CheckConstraint, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..models.game_models import Faction, GameState, TurnState, EventType

Base = declarative_base()


class PlayerDB(Base):
    """玩家数据库模型"""
    __tablename__ = 'players'

    player_id = Column(String(50), primary_key=True)
    username = Column(String(100), nullable=False)
    faction = Column(Enum(Faction), nullable=False)
    current_score = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    total_dice_rolls = Column(Integer, default=0)  # 总掷骰次数
    total_turns = Column(Integer, default=0)       # 总轮次数
    created_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # 关联关系
    sessions = relationship("GameSessionDB", back_populates="player")
    progress = relationship("PlayerProgressDB", back_populates="player")
    inventory = relationship("PlayerInventoryDB", back_populates="player")
    achievements = relationship("PlayerAchievementDB", back_populates="player")
    transactions = relationship("ScoreTransactionDB", back_populates="player")

    # 索引
    __table_args__ = (
        CheckConstraint('current_score >= 0', name='check_current_score_positive'),
        CheckConstraint('total_score >= 0', name='check_total_score_positive'),
        CheckConstraint('games_played >= 0', name='check_games_played_positive'),
        CheckConstraint('games_won >= 0', name='check_games_won_positive'),
        CheckConstraint('games_won <= games_played', name='check_wins_not_exceed_games'),
    )


class GameSessionDB(Base):
    """游戏会话数据库模型"""
    __tablename__ = 'game_sessions'

    session_id = Column(String(50), primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    session_state = Column(Enum(GameState), default=GameState.ACTIVE)
    turn_state = Column(Enum(TurnState), default=TurnState.DICE_ROLL)
    turn_number = Column(Integer, default=1)
    dice_results = Column(JSON)  # [1,2,3,4,5,6]
    forced_dice_result = Column(JSON, nullable=True)  # 强制骰子结果 [4,5,5,5,6,6]
    first_turn = Column(Boolean, default=True)
    needs_checkin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    # 关联关系
    player = relationship("PlayerDB", back_populates="sessions")
    temporary_markers = relationship("TemporaryMarkerDB", back_populates="session")

    __table_args__ = (
        CheckConstraint('turn_number > 0', name='check_turn_number_positive'),
    )


class PlayerProgressDB(Base):
    """玩家进度数据库模型"""
    __tablename__ = 'player_progress'

    progress_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    column_number = Column(Integer, nullable=False)
    permanent_progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    player = relationship("PlayerDB", back_populates="progress")

    __table_args__ = (
        UniqueConstraint('player_id', 'column_number', name='uq_player_column'),
        CheckConstraint('column_number >= 3 AND column_number <= 18', name='check_column_range'),
        CheckConstraint('permanent_progress >= 0', name='check_progress_positive'),
    )


class TemporaryMarkerDB(Base):
    """临时标记数据库模型"""
    __tablename__ = 'temporary_markers'

    marker_id = Column(Integer, primary_key=True)
    session_id = Column(String(50), ForeignKey('game_sessions.session_id'), nullable=False)
    column_number = Column(Integer, nullable=False)
    current_position = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    session = relationship("GameSessionDB", back_populates="temporary_markers")

    __table_args__ = (
        UniqueConstraint('session_id', 'column_number', name='uq_session_column'),
        CheckConstraint('column_number >= 3 AND column_number <= 18', name='check_marker_column_range'),
        CheckConstraint('current_position >= 0', name='check_position_positive'),
    )


class FirstCompletionDB(Base):
    """首达记录数据库模型"""
    __tablename__ = 'first_completions'

    completion_id = Column(Integer, primary_key=True)
    column_number = Column(Integer, unique=True, nullable=False)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    completed_at = Column(DateTime, default=func.now())
    reward_given = Column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint('column_number >= 3 AND column_number <= 18', name='check_completion_column_range'),
    )


class PlayerInventoryDB(Base):
    """玩家库存数据库模型"""
    __tablename__ = 'player_inventory'

    inventory_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    item_name = Column(String(100), nullable=False)
    item_type = Column(String(20), default='consumable')  # consumable, permanent, achievement_reward
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=func.now())
    used_count = Column(Integer, default=0)

    # 关联关系
    player = relationship("PlayerDB", back_populates="inventory")

    __table_args__ = (
        UniqueConstraint('player_id', 'item_name', name='uq_player_item'),
        CheckConstraint('quantity >= 0', name='check_quantity_positive'),
        CheckConstraint('used_count >= 0', name='check_used_count_positive'),
    )


class PlayerAchievementDB(Base):
    """玩家成就数据库模型"""
    __tablename__ = 'player_achievements'

    achievement_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    achievement_name = Column(String(100), nullable=False)
    achievement_category = Column(String(20), nullable=False)  # 倒霉类, 挑战类, 收集类, 特殊类
    unlocked_at = Column(DateTime, default=func.now())
    reward_claimed = Column(Boolean, default=False)

    # 关联关系
    player = relationship("PlayerDB", back_populates="achievements")

    __table_args__ = (
        UniqueConstraint('player_id', 'achievement_name', name='uq_player_achievement'),
    )


class GameLogDB(Base):
    """游戏日志数据库模型"""
    __tablename__ = 'game_logs'

    log_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    session_id = Column(String(50), ForeignKey('game_sessions.session_id'), nullable=True)
    action_type = Column(String(20), nullable=False)  # dice_roll, move_marker, end_turn, etc.
    action_data = Column(JSON)  # 详细的动作数据
    timestamp = Column(DateTime, default=func.now())


class MapEventDB(Base):
    """地图事件数据库模型"""
    __tablename__ = 'map_events'

    event_id = Column(String(50), primary_key=True)
    column_number = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    event_name = Column(String(100), nullable=False)
    event_data = Column(JSON)  # 事件配置数据
    faction_specific = Column(Enum(Faction), nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint('column_number', 'position', name='uq_event_position'),
        CheckConstraint('column_number >= 3 AND column_number <= 18', name='check_event_column_range'),
        CheckConstraint('position >= 1', name='check_event_position_positive'),
    )


class ScoreTransactionDB(Base):
    """积分交易记录数据库模型"""
    __tablename__ = 'score_transactions'

    transaction_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    transaction_type = Column(String(10), nullable=False)  # earn, spend
    amount = Column(Integer, nullable=False)
    source = Column(String(20), nullable=False)  # artwork, map_reward, dice_cost, item_purchase, achievement
    description = Column(Text)
    transaction_data = Column(JSON)
    timestamp = Column(DateTime, default=func.now())

    # 关联关系
    player = relationship("PlayerDB", back_populates="transactions")

    __table_args__ = (
        CheckConstraint('amount != 0', name='check_amount_not_zero'),
    )


class GameStatisticsDB(Base):
    """游戏统计数据库模型"""
    __tablename__ = 'game_statistics'

    stat_id = Column(Integer, primary_key=True)
    stat_name = Column(String(50), unique=True, nullable=False)
    stat_value = Column(JSON)  # 存储各种统计数据
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PlayerEncounterStateDB(Base):
    """玩家遭遇状态数据库模型"""
    __tablename__ = 'player_encounter_states'

    state_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    encounter_name = Column(String(100), nullable=False)
    state = Column(String(20), nullable=False)  # waiting_choice, processing, completed, follow_up
    selected_choice = Column(String(100), nullable=True)
    follow_up_trigger = Column(String(100), nullable=True)
    context_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PlayerEffectDB(Base):
    """玩家效果数据库模型（Buff和延迟效果）"""
    __tablename__ = 'player_effects'

    effect_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    effect_type = Column(String(50), nullable=False)  # buff, delayed_effect
    effect_name = Column(String(100), nullable=False)
    effect_data = Column(JSON)
    duration = Column(Integer, default=1)  # -1表示永久
    remaining_turns = Column(Integer, nullable=True)
    trigger_turn = Column(Integer, nullable=True)  # 延迟效果触发回合
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)


class EncounterHistoryDB(Base):
    """遭遇历史记录数据库模型"""
    __tablename__ = 'encounter_history'

    history_id = Column(Integer, primary_key=True)
    player_id = Column(String(50), ForeignKey('players.player_id'), nullable=False)
    encounter_name = Column(String(100), nullable=False)
    selected_choice = Column(String(100), nullable=True)
    result = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=func.now())