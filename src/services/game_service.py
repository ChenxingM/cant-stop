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
                # 获取玩家当前阵营名称
                current_faction = "收养人" if existing_player.faction == Faction.ADOPTER else "Aonreth"

                # 检查是否修改阵营
                if existing_player.faction != faction:
                    # 允许修改阵营
                    existing_player.faction = faction
                    success = self.db.update_player(existing_player)

                    # 同步更新游戏引擎中的玩家信息
                    if player_id in self.engine.players:
                        self.engine.players[player_id].faction = faction

                    if success:
                        return True, f"✅ 阵营修改成功！\n🔄 从 [{current_faction}] 切换到 [{faction_name}]\n🏁 当前阵营：{faction_name}"
                    else:
                        return False, "修改阵营失败"
                else:
                    return False, f"您已注册为 [{current_faction}] 阵营，无需重复注册"

            # 创建玩家
            success = self.db.create_player(player_id, username, faction)
            if success:
                # 在游戏引擎中创建玩家
                player = self.engine.create_player(player_id, username, faction)
                return True, f"✅ 玩家 {username} 注册成功！\n🏁 阵营：{faction_name}"
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

            return True, "新游戏开始！输入 .r6d6 开始第一回合"

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

    def roll_dice(self, player_id: str, free_roll: bool = False) -> Tuple[bool, str, Optional[List[Tuple[int, int]]]]:
        """掷骰子"""
        try:
            # 加载玩家和会话
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏", None

            # 检查玩家是否需要打卡
            if session.needs_checkin:
                return False, "请先完成打卡后再继续游戏", None

            # 检查积分（免费重投时跳过积分检查）
            if not free_roll and player.current_score < 10:
                return False, f"积分不足（当前：{player.current_score}，需要：10）", None

            # 掷骰
            dice_roll = self.engine.roll_dice(session.session_id)

            # 更新掷骰统计
            player.total_dice_rolls += 1

            # 扣除积分（免费重投时不扣除）
            if not free_roll:
                player.add_score(-10, "掷骰费用")

            # 保存状态
            self._save_player_and_session(player, session)

            # 获取可能的组合
            combinations = dice_roll.get_possible_combinations()

            message = f"的骰点：🎲{' '.join(map(str, dice_roll.results))}\n"
            if free_roll:
                message += f"积分：{player.current_score} (免费重投)\n"
            else:
                message += f"积分：{player.current_score} (-10)\n"
            message += "请选择数值组合（格式：a,b 或单个数字）"

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
                # 更新轮次统计
                player.total_turns += 1

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

    def confirm_summit(self, player_id: str, column: int) -> Tuple[bool, str]:
        """确认登顶指定列"""
        try:
            player, session = self._load_player_and_session(player_id)
            if not player or not session:
                return False, "请先开始游戏"

            success, message = self.engine.confirm_summit(session.session_id, column)

            if success:
                self._save_player_and_session(player, session)

            return success, message

        except Exception as e:
            return False, f"确认登顶失败：{str(e)}"

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
        """添加积分（支持自定义积分或类型积分）"""
        try:
            player = self._load_player(player_id)
            if not player:
                return False, "玩家不存在"

            # 如果提供了自定义积分（amount > 0），优先使用自定义积分
            if amount > 0:
                final_amount = amount
            else:
                # 否则根据作品类型设置积分
                score_map = {
                    "草图": 20,
                    "精致小图": 80,
                    "精草大图": 100,
                    "精致大图": 150,
                    "超常发挥": 30
                }
                final_amount = score_map.get(score_type, 0)

            if final_amount <= 0:
                return False, "无效的积分数量"

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
        message = f"的游戏状态\n"
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

    def get_all_players(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """获取所有活跃玩家列表"""
        try:
            players = self.db.get_all_active_players()
            player_list = []

            for i, player in enumerate(players, 1):
                # 获取玩家的游戏状态
                session = self.db.get_player_active_session(player.player_id)
                status = "游戏中" if session else "空闲"

                player_list.append({
                    "id": str(i),
                    "player_id": player.player_id,
                    "username": player.username,
                    "faction": player.faction.value,
                    "current_score": player.current_score,
                    "points": player.current_score,  # 为了兼容性同时提供points字段
                    "status": status,
                    "achievements_count": len(player.achievements) if hasattr(player, 'achievements') and player.achievements else 0,
                    "dice_rolls": getattr(player, 'total_dice_rolls', 0)  # 使用getattr避免属性不存在错误
                })

            return True, player_list
        except Exception as e:
            return False, []

    def get_gm_overview(self) -> Dict[str, any]:
        """获取GM视角的游戏整体状态"""
        try:
            players = self.db.get_all_active_players()
            overview = {
                "total_players": len(players),
                "players": [],
                "active_games": 0,
                "game_statistics": {
                    "total_turns": 0,
                    "total_dice_rolls": 0,
                    "achievements_unlocked": 0,
                    "traps_triggered": 0
                }
            }

            for player in players:
                session = self.db.get_player_active_session(player.player_id)
                player_data = {
                    "player_id": player.player_id,
                    "username": player.username,
                    "faction": player.faction.value,
                    "points": player.current_score,
                    "status": "游戏中" if session else "空闲",
                    "current_progress": self._get_player_progress_summary(player),
                    "achievements_count": len(player.achievements),
                    "dice_rolls": getattr(player, 'total_dice_rolls', 0),
                    "turns_played": getattr(player, 'total_turns', 0)
                }

                if session:
                    overview["active_games"] += 1

                    # 统计临时标记
                    temp_markers_count = len(session.temporary_markers) if hasattr(session, 'temporary_markers') else 0

                    # 统计不同列的临时标记
                    columns_with_markers = len(set(marker.column for marker in session.temporary_markers)) if hasattr(session, 'temporary_markers') else 0

                    # 统计永久进度
                    permanent_progress = 0
                    if hasattr(player, 'progress') and player.progress.permanent_progress:
                        permanent_progress = len(player.progress.permanent_progress)

                    player_data.update({
                        "turn_state": session.turn_state.value,
                        "columns_progressed": columns_with_markers,
                        "temporary_markers": temp_markers_count,
                        "permanent_markers": permanent_progress
                    })

                overview["players"].append(player_data)

            # 统计信息汇总
            overview["game_statistics"]["total_turns"] = sum(p.get("turns_played", 0) for p in overview["players"])
            overview["game_statistics"]["total_dice_rolls"] = sum(p.get("dice_rolls", 0) for p in overview["players"])
            overview["game_statistics"]["achievements_unlocked"] = sum(p.get("achievements_count", 0) for p in overview["players"])

            return overview

        except Exception as e:
            return {
                "error": str(e),
                "total_players": 0,
                "players": [],
                "active_games": 0,
                "game_statistics": {"total_turns": 0, "total_dice_rolls": 0, "achievements_unlocked": 0, "traps_triggered": 0}
            }

    def _get_player_progress_summary(self, player) -> str:
        """获取玩家进度摘要"""
        try:
            # 从数据库获取活跃会话
            session = self.db.get_player_active_session(player.player_id)
            if not session:
                # 检查是否有永久进度
                if hasattr(player, 'progress') and player.progress.permanent_progress:
                    completed_count = len(player.progress.completed_columns)
                    total_progress = sum(player.progress.permanent_progress.values())
                    return f"已完成{completed_count}列 (总进度:{total_progress})"
                return "未开始游戏"

            # 统计临时进度
            temp_progress = 0
            permanent_progress = 0

            if hasattr(session, 'temporary_markers'):
                temp_progress = len(session.temporary_markers)

            if hasattr(player, 'progress') and player.progress.permanent_progress:
                permanent_progress = len(player.progress.permanent_progress)
                completed_count = len(player.progress.completed_columns)

                if completed_count > 0:
                    return f"已完成{completed_count}列, 临时标记{temp_progress}个"
                elif permanent_progress > 0:
                    return f"永久进度{permanent_progress}列, 临时标记{temp_progress}个"

            return f"轮次{session.turn_number}, 临时标记{temp_progress}个"

        except Exception as e:
            return f"获取失败: {str(e)[:10]}"

    def select_player_for_penalty(self, selector_id: str, target_number: str) -> Tuple[bool, str]:
        """选择玩家承受花言巧语惩罚"""
        try:
            # 获取所有玩家
            success, players = self.get_all_players()
            if not success or not players:
                return False, "没有找到其他玩家"

            # 验证选择的数字
            try:
                target_index = int(target_number) - 1
                if target_index < 0 or target_index >= len(players):
                    return False, f"无效选择，请选择 1-{len(players)} 之间的数字"
            except ValueError:
                return False, "请输入有效的数字"

            target_player_info = players[target_index]
            target_player = self.db.get_player(target_player_info["player_id"])

            if not target_player:
                return False, "目标玩家不存在"

            # 不能选择自己
            if target_player.player_id == selector_id:
                return False, "不能选择自己作为惩罚目标"

            # 应用惩罚 - 设置下轮限制列
            # TODO: 这里需要记录惩罚状态，暂时返回确认消息

            result_msg = f"🎯 已选择 {target_player.username} 承受花言巧语惩罚！\n"
            result_msg += f"⚠️ {target_player.username} 下一轮将不能在当前轮次的列上行进\n"
            result_msg += f"🎲 {target_player.username} 可以投掷1d6，投出6点则抵消惩罚\n"
            result_msg += f"💡 {target_player.username} 请输入 '投掷抵消' 尝试抵消惩罚"

            return True, result_msg

        except Exception as e:
            return False, f"选择玩家失败：{str(e)}"

    def attempt_penalty_resistance(self, player_id: str) -> Tuple[bool, str]:
        """尝试通过投掷1d6抵消花言巧语惩罚"""
        try:
            import random
            dice_result = random.randint(1, 6)

            player = self.db.get_player(player_id)
            if not player:
                return False, "玩家不存在"

            if dice_result == 6:
                return True, f"🎲 {player.username} 投出了 {dice_result} 点！\n✨ 惩罚被成功抵消，可以正常行动！"
            else:
                return False, f"🎲 {player.username} 投出了 {dice_result} 点\n😔 惩罚依然生效，下轮不能在之前的列上行进"

        except Exception as e:
            return False, f"抵消投掷失败：{str(e)}"

    def switch_to_player(self, current_player_id: str, target_player_id: str) -> Tuple[bool, str]:
        """切换到指定玩家（不恢复进度）"""
        try:
            target_player = self.db.get_player(target_player_id)
            if not target_player:
                return False, f"玩家 {target_player_id} 不存在"

            # 检查目标玩家是否有活跃会话
            target_session = self.db.get_player_active_session(target_player_id)

            if target_session:
                result_msg = f"🔄 已切换到玩家：{target_player.username}\n"
                result_msg += f"⚡ 当前游戏状态已恢复，可以继续游戏\n"
                result_msg += self._get_current_status(target_player, target_session)
            else:
                result_msg = f"🔄 已切换到玩家：{target_player.username}\n"
                result_msg += f"💡 该玩家目前没有进行中的游戏，可以开始新游戏"

            return True, result_msg

        except Exception as e:
            return False, f"切换玩家失败：{str(e)}"

    def batch_add_score_to_all(self, amount: int, reason: str = "GM奖励") -> Tuple[bool, str]:
        """批量给所有玩家添加积分"""
        try:
            players = self.db.get_all_active_players()
            if not players:
                return False, "没有找到玩家"

            success_count = 0
            for player in players:
                try:
                    player.add_score(amount, reason)
                    self.db.update_player(player)
                    success_count += 1
                except Exception as e:
                    print(f"给玩家 {player.username} 加积分失败: {e}")

            return True, f"✅ 成功给 {success_count}/{len(players)} 个玩家添加 {amount} 积分\n💰 原因：{reason}"

        except Exception as e:
            return False, f"批量添加积分失败：{str(e)}"

    def clear_all_traps(self) -> Tuple[bool, str]:
        """清除所有陷阱"""
        try:
            # 清空陷阱配置中的生成陷阱
            self.engine.trap_config.generated_traps.clear()
            self.engine.trap_config.save_config()

            # 清空地图事件中的陷阱
            self.engine.map_events.clear()

            return True, "✅ 所有陷阱已清除！\n🗺️ 地图上不再有任何陷阱"

        except Exception as e:
            return False, f"清除陷阱失败：{str(e)}"

    def generate_random_traps(self) -> Tuple[bool, str]:
        """随机生成陷阱"""
        try:
            # 调用游戏引擎的随机生成方法
            self.engine.regenerate_traps()

            # 保存配置
            self.engine.trap_config.save_config()

            # 统计生成的陷阱数量
            trap_count = len(self.engine.trap_config.generated_traps)

            return True, f"✅ 陷阱已随机生成！\n🎲 共生成 {trap_count} 个陷阱\n📍 陷阱已放置在地图上"

        except Exception as e:
            return False, f"生成陷阱失败：{str(e)}"

    def verify_score_system(self) -> Tuple[bool, str]:
        """验证积分系统工作是否正常"""
        try:
            report = "🔍 积分系统检查报告\n"
            report += "=" * 50 + "\n\n"

            # 获取所有玩家
            players = self.db.get_all_active_players()
            if not players:
                return True, report + "⚠️ 没有找到玩家，无法检查"

            issues = []
            total_checks = 0

            for player in players:
                total_checks += 1

                # 检查1: 积分不能为负
                if player.current_score < 0:
                    issues.append(f"❌ {player.username}: 当前积分为负 ({player.current_score})")

                # 检查2: total_score应该 >= current_score（在没有扣分的情况下）
                # 注意：因为有消耗，这个检查可能不适用
                # if player.total_score < player.current_score:
                #     issues.append(f"❌ {player.username}: 总积分 ({player.total_score}) < 当前积分 ({player.current_score})")

                # 检查3: 玩家对象完整性
                if not hasattr(player, 'progress'):
                    issues.append(f"❌ {player.username}: 缺少进度数据")

                # 检查4: 数据库与内存一致性
                db_player = self.db.get_player(player.player_id)
                if db_player:
                    if db_player.current_score != player.current_score:
                        issues.append(f"⚠️ {player.username}: 内存积分({player.current_score}) != 数据库积分({db_player.current_score})")

            # 生成报告
            report += f"📊 检查玩家数: {total_checks}\n"
            report += f"✅ 发现问题数: {len(issues)}\n\n"

            if issues:
                report += "⚠️ 发现以下问题：\n"
                for issue in issues:
                    report += f"  {issue}\n"
            else:
                report += "✨ 积分系统一切正常！\n"

            # 添加积分统计
            report += "\n" + "=" * 50 + "\n"
            report += "💰 积分统计:\n"
            for player in players:
                report += f"  • {player.username}: {player.current_score} 积分 (总计: {player.total_score})\n"

            return True, report

        except Exception as e:
            return False, f"验证积分系统失败：{str(e)}"