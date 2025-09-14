"""
数据库连接和操作管理
"""

import asyncio
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager

from .models import Base, PlayerDB, GameSessionDB, PlayerProgressDB, TemporaryMarkerDB
from ..models.game_models import Player, GameSession, Faction, GameState


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str = "sqlite:///cant_stop.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.session_factory = sessionmaker(bind=self.engine)

    def create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """删除数据库表"""
        Base.metadata.drop_all(self.engine)

    def reset_all_game_data(self):
        """重置所有玩家的游戏数据，保留玩家基本信息和阵营"""
        with self.get_session() as session:
            # 删除所有游戏会话
            session.query(GameSessionDB).delete()

            # 删除所有临时标记
            session.query(TemporaryMarkerDB).delete()

            # 重置所有玩家进度
            session.query(PlayerProgressDB).delete()

            # 重置玩家积分但保留基本信息
            players = session.query(PlayerDB).all()
            for player in players:
                player.current_score = 0
                player.total_score = 0
                player.games_played = 0
                player.games_won = 0
                player.is_active = True

            session.commit()
            return True

    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_player(self, player_id: str, username: str, faction: Faction) -> bool:
        """创建玩家"""
        with self.get_session() as session:
            # 检查玩家是否已存在
            existing = session.query(PlayerDB).filter_by(player_id=player_id).first()
            if existing:
                return False

            player_db = PlayerDB(
                player_id=player_id,
                username=username,
                faction=faction
            )
            session.add(player_db)
            return True

    def get_player(self, player_id: str) -> Optional[Player]:
        """获取玩家"""
        with self.get_session() as session:
            player_db = session.query(PlayerDB).filter_by(player_id=player_id).first()
            if not player_db:
                return None

            # 获取玩家进度
            progress_records = session.query(PlayerProgressDB).filter_by(
                player_id=player_id
            ).all()

            # 转换为业务模型
            player = Player(
                player_id=player_db.player_id,
                username=player_db.username,
                faction=player_db.faction,
                current_score=player_db.current_score,
                total_score=player_db.total_score,
                games_played=player_db.games_played,
                games_won=player_db.games_won,
                is_active=player_db.is_active,
                created_at=player_db.created_at,
                last_active=player_db.last_active
            )

            # 设置进度
            for progress in progress_records:
                player.progress.set_progress(
                    progress.column_number,
                    progress.permanent_progress
                )
                if progress.is_completed:
                    player.progress.completed_columns.add(progress.column_number)

            return player

    def update_player(self, player: Player) -> bool:
        """更新玩家信息"""
        with self.get_session() as session:
            player_db = session.query(PlayerDB).filter_by(
                player_id=player.player_id
            ).first()
            if not player_db:
                return False

            # 更新基本信息
            player_db.username = player.username
            player_db.faction = player.faction
            player_db.current_score = player.current_score
            player_db.total_score = player.total_score
            player_db.games_played = player.games_played
            player_db.games_won = player.games_won
            player_db.is_active = player.is_active
            player_db.last_active = player.last_active

            # 更新进度
            for column, progress in player.progress.permanent_progress.items():
                progress_db = session.query(PlayerProgressDB).filter_by(
                    player_id=player.player_id,
                    column_number=column
                ).first()

                if progress_db:
                    progress_db.permanent_progress = progress
                    progress_db.is_completed = column in player.progress.completed_columns
                    if progress_db.is_completed and not progress_db.completed_at:
                        progress_db.completed_at = player.last_active
                else:
                    progress_db = PlayerProgressDB(
                        player_id=player.player_id,
                        column_number=column,
                        permanent_progress=progress,
                        is_completed=column in player.progress.completed_columns,
                        completed_at=player.last_active if column in player.progress.completed_columns else None
                    )
                    session.add(progress_db)

            return True

    def save_game_session(self, session_obj: GameSession) -> bool:
        """保存游戏会话"""
        with self.get_session() as session:
            session_db = session.query(GameSessionDB).filter_by(
                session_id=session_obj.session_id
            ).first()

            dice_results = None
            if session_obj.current_dice:
                dice_results = session_obj.current_dice.results

            if session_db:
                # 更新现有会话
                session_db.session_state = session_obj.state
                session_db.turn_state = session_obj.turn_state
                session_db.turn_number = session_obj.turn_number
                session_db.dice_results = dice_results
                session_db.forced_dice_result = session_obj.forced_dice_result
                session_db.first_turn = session_obj.first_turn
                session_db.needs_checkin = session_obj.needs_checkin
                session_db.updated_at = session_obj.updated_at
                if session_obj.state == GameState.COMPLETED:
                    session_db.completed_at = session_obj.updated_at
            else:
                # 创建新会话
                session_db = GameSessionDB(
                    session_id=session_obj.session_id,
                    player_id=session_obj.player_id,
                    session_state=session_obj.state,
                    turn_state=session_obj.turn_state,
                    turn_number=session_obj.turn_number,
                    dice_results=dice_results,
                    forced_dice_result=session_obj.forced_dice_result,
                    first_turn=session_obj.first_turn,
                    needs_checkin=session_obj.needs_checkin,
                    created_at=session_obj.created_at,
                    updated_at=session_obj.updated_at
                )
                session.add(session_db)

            # 清除现有的临时标记
            session.query(TemporaryMarkerDB).filter_by(
                session_id=session_obj.session_id
            ).delete()

            # 添加新的临时标记
            for marker in session_obj.temporary_markers:
                marker_db = TemporaryMarkerDB(
                    session_id=session_obj.session_id,
                    column_number=marker.column,
                    current_position=marker.position
                )
                session.add(marker_db)

            return True

    def get_game_session(self, session_id: str) -> Optional[GameSession]:
        """获取游戏会话"""
        with self.get_session() as session:
            session_db = session.query(GameSessionDB).filter_by(
                session_id=session_id
            ).first()
            if not session_db:
                return None

            # 获取临时标记
            markers_db = session.query(TemporaryMarkerDB).filter_by(
                session_id=session_id
            ).all()

            # 转换为业务模型
            game_session = GameSession(
                session_id=session_db.session_id,
                player_id=session_db.player_id,
                state=session_db.session_state,
                turn_state=session_db.turn_state,
                turn_number=session_db.turn_number,
                first_turn=session_db.first_turn,
                needs_checkin=session_db.needs_checkin,
                created_at=session_db.created_at,
                updated_at=session_db.updated_at
            )

            # 添加临时标记
            for marker_db in markers_db:
                game_session.add_temporary_marker(
                    marker_db.column_number,
                    marker_db.current_position
                )

            # 恢复骰子结果
            if session_db.dice_results:
                from ..models.game_models import DiceRoll
                game_session.current_dice = DiceRoll(results=session_db.dice_results)

            # 恢复强制骰子结果
            if session_db.forced_dice_result:
                game_session.forced_dice_result = session_db.forced_dice_result

            return game_session

    def get_player_active_session(self, player_id: str) -> Optional[GameSession]:
        """获取玩家活跃会话"""
        with self.get_session() as session:
            session_db = session.query(GameSessionDB).filter_by(
                player_id=player_id,
                session_state=GameState.ACTIVE
            ).first()

            if session_db:
                return self.get_game_session(session_db.session_id)
            return None

    def get_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取排行榜"""
        with self.get_session() as session:
            # 复杂查询：按完成列数和积分排序
            query = session.query(
                PlayerDB.player_id,
                PlayerDB.username,
                PlayerDB.faction,
                PlayerDB.current_score,
                PlayerDB.games_won,
                PlayerDB.games_played
            ).filter(PlayerDB.is_active == True)

            players = query.all()
            leaderboard = []

            for player in players:
                # 获取完成的列数
                completed_count = session.query(PlayerProgressDB).filter_by(
                    player_id=player.player_id,
                    is_completed=True
                ).count()

                win_rate = (player.games_won / player.games_played * 100) if player.games_played > 0 else 0

                leaderboard.append({
                    'player_id': player.player_id,
                    'username': player.username,
                    'faction': player.faction.value,
                    'current_score': player.current_score,
                    'games_won': player.games_won,
                    'games_played': player.games_played,
                    'win_rate': round(win_rate, 2),
                    'completed_columns': completed_count
                })

            # 按完成列数和积分排序
            leaderboard.sort(
                key=lambda x: (x['completed_columns'], x['current_score']),
                reverse=True
            )

            return leaderboard[:limit]

    def cleanup_old_sessions(self, days: int = 7):
        """清理旧的游戏会话"""
        with self.get_session() as session:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # 删除旧的已完成或失败的会话
            old_sessions = session.query(GameSessionDB).filter(
                GameSessionDB.updated_at < cutoff_date,
                GameSessionDB.session_state.in_([GameState.COMPLETED, GameState.FAILED])
            ).all()

            for old_session in old_sessions:
                # 删除相关的临时标记
                session.query(TemporaryMarkerDB).filter_by(
                    session_id=old_session.session_id
                ).delete()

                # 删除会话
                session.delete(old_session)


# 全局数据库实例
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        db_manager.create_tables()
    return db_manager