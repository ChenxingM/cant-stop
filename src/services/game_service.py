"""
游戏服务层 - 整合游戏引擎和数据库操作
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..core.game_engine import GameEngine
from ..database.database import get_db_manager
from ..models.game_models import Faction, Player, GameSession, DiceRoll


class GameService:
    """游戏服务类"""

    def __init__(self):
        self.engine = GameEngine()
        self.db = get_db_manager()

    def register_player(self, player_id: str, username: str, faction_name: str) -> Tuple[bool, str]:
        """注册新玩家"""
        try:
            # 验证阵营
            if faction_name not in ["收养人", "Aonreth"]:
                return False, "无效的阵营名称，请选择 '收养人' 或 'Aonreth'"

            faction = Faction.ADOPTER if faction_name == "收养人" else Faction.AONRETH

            # 检查玩家是否已存在
            existing_player = self.db.get_player(player_id)
            if existing_player:
                return False, f"玩家 {username} 已存在"

            # 创建玩家
            success = self.db.create_player(player_id, username, faction)
            if success:
                # 在游戏引擎中创建玩家
                player = self.engine.create_player(player_id, username, faction)
                return True, f"玩家 {username} 注册成功，阵营：{faction_name}"
            else:
                return False, "注册失败"

        except Exception as e:
            return False, f"注册失败：{str(e)}"

    def start_new_game(self, player_id: str) -> Tuple[bool, str]:
        """开始新游戏"""
        try:
            # 从数据库加载玩家
            player = self.db.get_player(player_id)
            if not player:
                return False, "玩家不存在，请先注册"

            # 将玩家加载到游戏引擎
            self.engine.players[player_id] = player

            # 检查是否有活跃会话
            active_session = self.db.get_player_active_session(player_id)
            if active_session:
                # 恢复现有会话到游戏引擎
                self.engine.game_sessions[active_session.session_id] = active_session
                return False, "您已有进行中的游戏，请使用继续游戏功能"

            # 创建新会话
            session = self.engine.create_game_session(player_id)
            self.db.save_game_session(session)

            return True, "新游戏开始！输入 '掷骰' 开始第一回合"

        except Exception as e:
            return False, f"开始游戏失败：{str(e)}"

    def resume_game(self, player_id: str) -> Tuple[bool, str]:
        """恢复游戏"""
        try:
            # 从数据库加载玩家
            player = self.db.get_player(player_id)
            if not player:
                return False, "玩家不存在，请先注册"

            # 将玩家加载到游戏引擎
            self.engine.players[player_id] = player

            # 检查是否有活跃会话
            active_session = self.db.get_player_active_session(player_id)
            if not active_session:
                return False, "没有进行中的游戏，请开始新游戏"

            # 恢复现有会话到游戏引擎
            self.engine.game_sessions[active_session.session_id] = active_session

            return True, f"游戏已恢复！当前轮次：{active_session.turn_number}"

        except Exception as e:
            return False, f"恢复游戏失败：{str(e)}"

    def roll_dice(self, player_id: str) -> Tuple[bool, str, Optional[List[Tuple[int, int]]]]:
        """掷骰子"""
        try:
            # 加载玩家和会话
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏", None

            # 检查玩家是否需要打卡
            if session.needs_checkin:
                return False, "请先完成打卡后再继续游戏", None

            # 检查积分
            if player.current_score < 10:
                return False, f"积分不足（当前：{player.current_score}，需要：10）", None

            # 掷骰
            dice_roll = self.engine.roll_dice(session.session_id)

            # 保存状态
            self._save_player_and_session(player, session)

            # 获取可能的组合
            combinations = dice_roll.get_possible_combinations()

            message = f"🎲 {player.username}的骰点：{' '.join(map(str, dice_roll.results))}\n"
            message += f"积分：{player.current_score} (-10)\n"
            message += f"可选组合：{combinations}\n"
            message += "请选择数值组合（格式：8,13 或单个数字）"

            return True, message, combinations

        except Exception as e:
            return False, f"掷骰失败：{str(e)}", None

    def move_markers(self, player_id: str, target_columns: List[int]) -> Tuple[bool, str]:
        """移动标记"""
        try:
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏"

            # 移动标记
            success, message = self.engine.move_markers(session.session_id, target_columns)

            if success:
                # 检查被动停止
                if self.engine.check_passive_stop(session.session_id):
                    message += "\n❌ 无法移动任何标记，触发被动停止！本轮进度清零"

                # 保存状态
                self._save_player_and_session(player, session)

                # 获取当前状态
                status = self._get_current_status(player, session)
                message += f"\n{status}"

            return success, message

        except Exception as e:
            return False, f"移动标记失败：{str(e)}"

    def end_turn(self, player_id: str) -> Tuple[bool, str]:
        """结束回合"""
        try:
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏"

            success, message = self.engine.end_turn_actively(session.session_id)

            if success:
                # 保存状态
                self._save_player_and_session(player, session)

            return success, message

        except Exception as e:
            return False, f"结束回合失败：{str(e)}"

    def continue_turn(self, player_id: str) -> Tuple[bool, str]:
        """继续回合"""
        try:
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏"

            success = self.engine.continue_turn(session.session_id)

            if success:
                self._save_player_and_session(player, session)
                return True, "回合继续，请掷骰子"
            else:
                return False, "无法继续回合"

        except Exception as e:
            return False, f"继续回合失败：{str(e)}"

    def complete_checkin(self, player_id: str) -> Tuple[bool, str]:
        """完成打卡"""
        try:
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏"

            if not session.needs_checkin:
                return False, "当前不需要打卡"

            success = self.engine.complete_checkin(session.session_id)

            if success:
                self._save_player_and_session(player, session)
                return True, "打卡完成！您可以开始新的轮次了～"
            else:
                return False, "打卡失败"

        except Exception as e:
            return False, f"打卡失败：{str(e)}"

    def get_game_status(self, player_id: str) -> Tuple[bool, str]:
        """获取游戏状态"""
        try:
            player, session = self._load_player_and_session(player_id)
            if not player:
                return False, "玩家不存在"

            status = self._get_detailed_status(player, session)
            return True, status

        except Exception as e:
            return False, f"获取状态失败：{str(e)}"

    def add_score(self, player_id: str, amount: int, score_type: str) -> Tuple[bool, str]:
        """添加积分"""
        try:
            player = self._load_player(player_id)
            if not player:
                return False, "玩家不存在"

            # 根据作品类型设置积分
            score_map = {
                "草图": 20,
                "精致小图": 80,
                "精草大图": 100,
                "精致大图": 150,
                "超常发挥": 30
            }

            final_amount = score_map.get(score_type, amount)
            player.add_score(final_amount, score_type)

            self.db.update_player(player)

            return True, f"您的积分 +{final_amount}（{score_type}）\n当前积分：{player.current_score}"

        except Exception as e:
            return False, f"添加积分失败：{str(e)}"

    def get_leaderboard(self, limit: int = 10) -> Tuple[bool, str]:
        """获取排行榜"""
        try:
            leaderboard = self.db.get_leaderboard(limit)

            if not leaderboard:
                return True, "暂无排行榜数据"

            message = "排行榜\n"
            message += "-" * 40 + "\n"
            message += f"{'排名':<4} {'玩家':<10} {'阵营':<8} {'积分':<6} {'登顶':<4}\n"
            message += "-" * 40 + "\n"

            for i, entry in enumerate(leaderboard, 1):
                message += f"{i:<4} {entry['username']:<10} {entry['faction']:<8} {entry['current_score']:<6} {entry['completed_columns']:<4}\n"

            return True, message

        except Exception as e:
            return False, f"获取排行榜失败：{str(e)}"

    def reset_all_game_data(self) -> Tuple[bool, str]:
        """重置所有玩家的游戏数据"""
        try:
            success = self.db.reset_all_game_data()
            if success:
                # 清空游戏引擎中的数据
                self.engine.game_sessions.clear()
                self.engine.players.clear()
                # 重新生成陷阱位置
                self.engine.regenerate_traps()
                return True, "✅ 所有游戏数据已重置！\n📝 已保留：玩家名称、阵营\n🗑️ 已清除：积分、进度、游戏会话、临时标记"
            else:
                return False, "❌ 重置失败"
        except Exception as e:
            return False, f"重置失败：{str(e)}"

    def set_trap_config(self, trap_name: str, columns: List[int], positions: List[int] = None, probability: float = 1.0) -> Tuple[bool, str]:
        """GM设置陷阱配置"""
        try:
            success, message = self.engine.trap_config.set_trap_config(trap_name, columns, positions, probability)
            if success:
                # 保存配置
                self.engine.trap_config.save_config()
                # 重新生成陷阱位置
                self.engine.regenerate_traps()
            return success, message
        except Exception as e:
            return False, f"设置陷阱配置失败：{str(e)}"

    def get_trap_config_info(self) -> Tuple[bool, str]:
        """获取当前陷阱配置信息"""
        try:
            info = self.engine.trap_config.get_config_info()
            return True, info
        except Exception as e:
            return False, f"获取陷阱配置失败：{str(e)}"

    def regenerate_traps(self) -> Tuple[bool, str]:
        """重新生成陷阱位置"""
        try:
            self.engine.regenerate_traps()
            return True, "🕳️ 陷阱位置已重新生成！"
        except Exception as e:
            return False, f"重新生成陷阱失败：{str(e)}"

    def set_manual_trap(self, trap_name: str, column: int, position: int) -> Tuple[bool, str]:
        """手动设置单个陷阱位置"""
        try:
            success, message = self.engine.trap_config.set_manual_trap(trap_name, column, position)
            if success:
                # 仅更新map_events，不重新生成随机陷阱
                self.engine.update_map_events_from_config()
            return success, message
        except Exception as e:
            return False, f"手动设置陷阱失败：{str(e)}"

    def remove_trap_at_position(self, column: int, position: int) -> Tuple[bool, str]:
        """移除指定位置的陷阱"""
        try:
            success, message = self.engine.trap_config.remove_trap_at_position(column, position)
            if success:
                # 仅更新map_events，不重新生成随机陷阱
                self.engine.update_map_events_from_config()
            return success, message
        except Exception as e:
            return False, f"移除陷阱失败：{str(e)}"

    def _load_player_and_session(self, player_id: str) -> Tuple[Optional[Player], Optional[GameSession]]:
        """加载玩家和会话"""
        player = self._load_player(player_id)
        if not player:
            return None, None

        session = self.db.get_player_active_session(player_id)
        if session:
            self.engine.game_sessions[session.session_id] = session

        return player, session

    def _load_player(self, player_id: str) -> Optional[Player]:
        """加载玩家"""
        player = self.db.get_player(player_id)
        if player:
            self.engine.players[player_id] = player
        return player

    def _save_player_and_session(self, player: Player, session: GameSession):
        """保存玩家和会话状态"""
        self.db.update_player(player)
        self.db.save_game_session(session)

    def _get_current_status(self, player: Player, session: GameSession) -> str:
        """获取当前状态摘要"""
        temp_markers = []
        for marker in session.temporary_markers:
            permanent = player.progress.get_progress(marker.column)
            total = permanent + marker.position
            temp_markers.append(f"第{marker.column}列-位置{total}")

        current_pos = "、".join(temp_markers) if temp_markers else "无"
        remaining_markers = 3 - len(session.temporary_markers)

        permanent_pos = []
        for column, progress in player.progress.permanent_progress.items():
            if progress > 0:
                status = "已登顶" if column in player.progress.completed_columns else f"进度{progress}"
                permanent_pos.append(f"第{column}列-{status}")

        permanent_str = "、".join(permanent_pos) if permanent_pos else "无"
        completed_count = player.progress.get_completed_count()

        status = f"当前位置：{current_pos}；剩余可放置标记：{remaining_markers}\n"
        status += f"当前永久棋子位置：{permanent_str}\n"
        status += f"已登顶棋子数：{completed_count}/3"

        return status

    def _get_detailed_status(self, player: Player, session: Optional[GameSession]) -> str:
        """获取详细状态"""
        message = f"{player.username} 的游戏状态\n"
        message += "-" * 30 + "\n"
        message += f"阵营：{player.faction.value}\n"
        message += f"当前积分：{player.current_score}\n"
        message += f"游戏场次：{player.games_played}\n"
        message += f"获胜场次：{player.games_won}\n"

        if session:
            message += f"\n当前游戏状态：{session.state.value}\n"
            message += f"轮次：{session.turn_number}\n"

            if session.needs_checkin:
                message += "WARNING: 需要完成打卡才能继续游戏\n"

            message += "\n" + self._get_current_status(player, session)
        else:
            message += "\n当前没有进行中的游戏"

        return message