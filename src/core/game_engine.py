"""
Can't Stop游戏引擎 - 核心游戏逻辑实现
"""

import random
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime

from ..models.game_models import (
    Player, GameSession, DiceRoll, TemporaryMarker, MapConfig,
    GameState, TurnState, Faction, EventType, MapEvent
)
from .trap_config import TrapConfigManager
from .encounter_config import EncounterConfigManager
from ..config.config_manager import get_config
from .event_system import GameEventType, emit_game_event


class GameEngine:
    """Can't Stop游戏引擎"""

    def __init__(self):
        self.map_config = MapConfig()
        self.game_sessions: Dict[str, GameSession] = {}
        self.players: Dict[str, Player] = {}
        self.map_events: Dict[str, List[MapEvent]] = {}  # column_position -> events
        self.trap_config = TrapConfigManager()
        self.encounter_config = EncounterConfigManager()
        self._init_map_events()

    def _init_map_events(self):
        """初始化地图事件"""
        # 从配置文件加载现有陷阱（不生成新的随机陷阱）
        # 这样可以保持陷阱状态，直到GM手动重置或随机生成
        self.update_map_events_from_config()

        # 添加固定的道具和遭遇事件
        fixed_events = [
            # # 道具示例
            # {"column": 7, "position": 4, "type": EventType.ITEM, "name": "传送卷轴"},
            # {"column": 9, "position": 6, "type": EventType.ITEM, "name": "幸运符"},
            # # 遭遇事件
            # {"column": 13, "position": 5, "type": EventType.ENCOUNTER, "name": "神秘商人"},
            # {"column": 16, "position": 3, "type": EventType.ENCOUNTER, "name": "古老遗迹"},
        ]

        for event_data in fixed_events:
            event_key = f"{event_data['column']}_{event_data['position']}"
            event = MapEvent(
                event_id=event_key,
                column=event_data['column'],
                position=event_data['position'],
                event_type=event_data['type'],
                name=event_data['name'],
                description=f"{event_data['name']}事件",
            )

            if event_key not in self.map_events:
                self.map_events[event_key] = []
            self.map_events[event_key].append(event)

    def regenerate_traps(self):
        """重新生成陷阱位置"""
        # 清除现有陷阱事件
        trap_keys = []
        for key, events in self.map_events.items():
            self.map_events[key] = [event for event in events if event.event_type != EventType.TRAP]
            if not self.map_events[key]:
                trap_keys.append(key)

        # 移除空的事件列表
        for key in trap_keys:
            del self.map_events[key]

        # 生成新的陷阱位置
        trap_positions = self.trap_config.generate_trap_positions()

        for position_key, trap_name in trap_positions.items():
            column, position = position_key.split('_')
            column, position = int(column), int(position)

            event = MapEvent(
                event_id=position_key,
                column=column,
                position=position,
                event_type=EventType.TRAP,
                name=trap_name,
                description=f"{trap_name}陷阱",
            )

            if position_key not in self.map_events:
                self.map_events[position_key] = []
            self.map_events[position_key].append(event)

    def reload_traps_from_config(self):
        """从配置文件重新加载陷阱数据（确保获取最新配置）"""
        # 重新从文件加载配置
        self.trap_config.load_config()
        # 更新map_events
        self.update_map_events_from_config()

    def update_map_events_from_config(self):
        """仅根据当前陷阱和遭遇配置更新map_events，不重新生成随机内容"""
        # 清除现有陷阱和遭遇事件
        keys_to_remove = []
        for key, events in self.map_events.items():
            self.map_events[key] = [event for event in events
                                   if event.event_type not in (EventType.TRAP, EventType.ENCOUNTER)]
            if not self.map_events[key]:
                keys_to_remove.append(key)

        # 移除空的事件列表
        for key in keys_to_remove:
            del self.map_events[key]

        # 使用现有的generated_traps（不重新生成）
        for position_key, trap_name in self.trap_config.generated_traps.items():
            column, position = position_key.split('_')
            column, position = int(column), int(position)

            event = MapEvent(
                event_id=position_key,
                column=column,
                position=position,
                event_type=EventType.TRAP,
                name=trap_name,
                description=f"{trap_name}陷阱",
            )

            if position_key not in self.map_events:
                self.map_events[position_key] = []
            self.map_events[position_key].append(event)

        # 加载遭遇事件
        for position_key, encounter_name in self.encounter_config.generated_encounters.items():
            column, position = position_key.split('_')
            column, position = int(column), int(position)

            event = MapEvent(
                event_id=f"encounter_{position_key}",
                column=column,
                position=position,
                event_type=EventType.ENCOUNTER,
                name=encounter_name,
                description=f"{encounter_name}遭遇",
            )

            if position_key not in self.map_events:
                self.map_events[position_key] = []
            self.map_events[position_key].append(event)

    def create_player(self, player_id: str, username: str, faction: Faction) -> Player:
        """创建新玩家"""
        if player_id in self.players:
            raise ValueError(f"玩家 {player_id} 已存在")

        player = Player(
            player_id=player_id,
            username=username,
            faction=faction
        )
        self.players[player_id] = player
        return player

    def get_player(self, player_id: str) -> Optional[Player]:
        """获取玩家"""
        return self.players.get(player_id)

    def create_game_session(self, player_id: str) -> GameSession:
        """创建游戏会话"""
        player = self.get_player(player_id)
        if not player:
            raise ValueError(f"玩家 {player_id} 不存在")

        session_id = f"{player_id}_{datetime.now().timestamp()}"
        session = GameSession(session_id=session_id, player_id=player_id)
        self.game_sessions[session_id] = session
        return session

    def get_game_session(self, session_id: str) -> Optional[GameSession]:
        """获取游戏会话"""
        return self.game_sessions.get(session_id)

    def get_player_active_session(self, player_id: str) -> Optional[GameSession]:
        """获取玩家的活跃会话"""
        for session in self.game_sessions.values():
            if session.player_id == player_id and session.state == GameState.ACTIVE:
                return session
        return None

    def roll_dice(self, session_id: str) -> DiceRoll:
        """掷骰子"""
        session = self.get_game_session(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")

        player = self.get_player(session.player_id)
        if not player:
            raise ValueError(f"玩家 {session.player_id} 不存在")

        # 检查轮次状态 - 只有在特定状态下才能掷骰子
        if session.turn_state == TurnState.WAITING_FOR_SUMMIT_CONFIRMATION:
            pending_columns = ', '.join([f'数列{c}登顶' for c in session.pending_summit_columns])
            raise ValueError(f"⚠️ 请先确认登顶！\n待确认的列: {pending_columns}")

        if session.turn_state == TurnState.WAITING_FOR_CHECKIN:
            raise ValueError("⚠️ 请先完成打卡！输入 '打卡完毕' 继续游戏")

        if session.turn_state not in [TurnState.DICE_ROLL, TurnState.DECISION]:
            raise ValueError(f"当前状态 ({session.turn_state.value}) 无法掷骰子")

        # 处理本回合的延迟效果
        from ..core.effect_handler import get_effect_handler
        effect_handler = get_effect_handler()
        delayed_effects = effect_handler.get_delayed_effects_for_turn(
            player.player_id,
            session.turn_number
        )

        # 应用延迟效果
        for delayed_effect in delayed_effects:
            if delayed_effect.effect_type == "dice_count_override":
                dice_count = delayed_effect.effect_data.get("count", 6)
                # 将骰子数量信息存储到session中以便后续使用
                session.next_dice_count = dice_count
            elif delayed_effect.effect_type == "extra_dice_risk":
                # 标记需要额外投掷风险骰子
                session.has_extra_dice_risk = True
                session.extra_dice_risk_value = delayed_effect.effect_data.get("risk_value", 6)

        # 检查积分是否足够（考虑消耗减免buff）
        from ..core.item_system import get_buff_manager
        buff_manager = get_buff_manager()
        cost_reduction = buff_manager.get_cost_reduction(player.player_id)

        # 同时考虑effect_handler中的cost_reduction
        effect_cost_reduction = effect_handler.get_cost_reduction(player.player_id)
        total_cost_reduction = cost_reduction + effect_cost_reduction

        base_dice_cost = get_config("game_config", "game.dice_cost", 10)
        dice_cost = max(0, base_dice_cost - total_cost_reduction)  # 确保不为负

        if not player.spend_score(dice_cost, "掷骰消耗"):
            raise ValueError("积分不足，无法掷骰")

        # 检查是否有强制骰子结果
        if session.forced_dice_result:
            dice_results = session.forced_dice_result
            session.forced_dice_result = None  # 使用后清空
        else:
            # 生成6个1-6的随机数
            dice_results = [random.randint(1, 6) for _ in range(6)]

        # 应用骰子修正buff（+1或-1）
        dice_modifier = buff_manager.get_dice_modifier(player.player_id)
        if dice_modifier != 0:
            dice_results = [max(1, min(6, d + dice_modifier)) for d in dice_results]
            # 消耗骰子修正buff
            from ..core.item_system import BuffType
            buff_manager.consume_buff(player.player_id, BuffType.DICE_MODIFIER)

        dice_roll = DiceRoll(results=dice_results)

        session.current_dice = dice_roll
        session.turn_state = TurnState.MOVE_MARKERS
        session.updated_at = datetime.now()

        # 发布骰子事件
        emit_game_event(GameEventType.DICE_ROLLED, session.player_id, {
            "dice_results": dice_results,
            "session_id": session_id,
            "turn_number": session.turn_number,
            "combinations": dice_roll.get_possible_combinations()
        }, session_id)

        return dice_roll

    def can_move_markers(self, session_id: str, target_columns: List[int]) -> Tuple[bool, str]:
        """检查是否可以移动标记到目标列"""
        session = self.get_game_session(session_id)
        if not session:
            return False, "会话不存在"

        player = self.get_player(session.player_id)
        if not player:
            return False, "玩家不存在"

        # 检查轮次状态 - 只有在MOVE_MARKERS状态下才能移动标记
        if session.turn_state != TurnState.MOVE_MARKERS:
            return False, "当前状态无法移动标记，请先掷骰子"

        # 检查目标列是否有效
        for column in target_columns:
            if not self.map_config.is_valid_column(column):
                return False, f"无效的列号: {column}"

        # 检查是否已完成的列
        for column in target_columns:
            if player.progress.is_completed(column):
                return False, f"列 {column} 已完成，无法再放置标记"

        # 检查标记数量限制
        if session.first_turn:
            if len(target_columns) != 2:
                return False, "首轮必须选择两个数值"
        else:
            if len(target_columns) > 2:
                return False, "每回合最多选择两个数值"

        # 检查是否超过3个临时标记限制
        current_markers = len(session.temporary_markers)
        new_markers = len([col for col in target_columns
                          if not session.get_temporary_marker(col)])

        if current_markers + new_markers > 3:
            return False, "临时标记数量不能超过3个"

        # 检查骰子结果是否包含目标数值
        if not session.current_dice:
            return False, "没有骰子结果"

        possible_combinations = session.current_dice.get_possible_combinations()
        target_tuple = tuple(sorted(target_columns))

        if target_tuple not in possible_combinations and len(target_columns) == 2:
            return False, f"骰子结果无法组合出 {target_columns}"

        if len(target_columns) == 1:
            # 检查单个数值是否可达
            column = target_columns[0]
            valid = False
            for combo in possible_combinations:
                if column in combo:
                    valid = True
                    break
            if not valid:
                return False, f"骰子结果无法组合出 {column}"

        # 检查移动后是否会超过列的最大高度
        # 统计每列需要移动的次数
        column_moves = {}
        for column in target_columns:
            column_moves[column] = column_moves.get(column, 0) + 1

        for column, move_count in column_moves.items():
            # 获取该列的最大高度
            column_length = self.map_config.get_column_length(column)

            # 获取永久进度
            permanent_progress = player.progress.get_progress(column)

            # 获取当前临时标记位置
            existing_marker = session.get_temporary_marker(column)
            current_temp_position = existing_marker.position if existing_marker else 0

            # 计算移动后的总位置
            new_total_position = permanent_progress + current_temp_position + move_count

            # 检查是否超过列的最大高度
            if new_total_position > column_length:
                return False, f"❌ 列 {column} 移动后位置将超过最大高度！\n📏 列 {column} 最大高度: {column_length}\n📍 当前永久进度: {permanent_progress}\n🎯 当前临时位置: {current_temp_position}\n➕ 本次移动: {move_count}\n❗ 总位置将达到: {new_total_position} (超出限制)"

        return True, "可以移动"

    def move_markers(self, session_id: str, target_columns: List[int]) -> Tuple[bool, str]:
        """移动临时标记"""
        can_move, message = self.can_move_markers(session_id, target_columns)
        if not can_move:
            # 特殊处理：如果是标记数量超过3个，清空临时标记并强制结束轮次
            if "临时标记数量不能超过3个" in message:
                session = self.get_game_session(session_id)
                if session:
                    # 清空所有临时标记（失去本轮进度）
                    session.clear_temporary_markers()

                    # 强制结束轮次，需要打卡
                    session.needs_checkin = True
                    session.turn_state = TurnState.WAITING_FOR_CHECKIN

                    return False, "❌ 临时标记数量不能超过3个！\n⚠️ 已清空所有临时标记\n💔 本轮进度丢失\n📝 请完成打卡后继续游戏"

            return False, message

        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)

        moved_columns = []

        # 统计每列需要移动的次数
        column_moves = {}
        for column in target_columns:
            column_moves[column] = column_moves.get(column, 0) + 1

        for column, move_count in column_moves.items():
            existing_marker = session.get_temporary_marker(column)
            if existing_marker:
                # 移动现有标记，累加移动次数
                existing_marker.position += move_count
                moved_columns.extend([column] * move_count)  # 记录实际移动次数
            else:
                # 添加新标记，位置为移动次数
                if session.add_temporary_marker(column, move_count):
                    moved_columns.extend([column] * move_count)

        session.turn_state = TurnState.DECISION
        session.first_turn = False

        # 检查是否有登顶
        self._check_column_completions(session_id)

        # 检查并触发地图事件
        event_messages = self._check_and_trigger_events(session_id, moved_columns)

        # 构建完整的返回消息
        base_message = f"已移动标记到列: {moved_columns}"
        if event_messages:
            return True, f"{base_message}\n\n{event_messages}"
        else:
            return True, base_message

    def _check_column_completions(self, session_id: str) -> List[int]:
        """检查列完成情况，返回待确认的登顶列"""
        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)

        pending_completions = []

        for marker in session.temporary_markers[:]:  # 复制列表以避免修改时的问题
            column_length = self.map_config.get_column_length(marker.column)
            total_progress = player.progress.get_progress(marker.column) + marker.position

            if total_progress >= column_length:
                # 检测到登顶，但不立即完成，需要用户确认
                if marker.column not in session.pending_summit_columns:
                    pending_completions.append(marker.column)
                    session.pending_summit_columns.append(marker.column)

        # 如果有待确认的登顶，切换到等待确认状态
        if pending_completions:
            session.turn_state = TurnState.WAITING_FOR_SUMMIT_CONFIRMATION
            # 打印提示消息
            for column in pending_completions:
                print(f"🎊 检测到第{column}列登顶！")
            print(f"\n⚠️ 请输入 '数列{pending_completions[0]}登顶' 来确认登顶")
            if len(pending_completions) > 1:
                print(f"多个列登顶，请依次确认: {', '.join([f'数列{c}登顶' for c in pending_completions])}")

        return pending_completions

    def _clear_column_temporary_markers(self, column: int):
        """清空指定列的所有临时标记"""
        for session in self.game_sessions.values():
            session.remove_temporary_marker(column)

    def _handle_column_completions(self, session_id: str, completed_columns: List[int]) -> str:
        """处理列完成（登顶）事件，返回奖励信息"""
        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)

        reward_messages = []

        for column in completed_columns:
            column_messages = []
            column_messages.append(f"🎉 恭喜您在第{column}列登顶～")

            # 更新玩家永久进度
            column_length = self.map_config.get_column_length(column)
            player.progress.set_progress(column, column_length)

            # 清空该列所有玩家的临时标记
            self._clear_column_temporary_markers(column)
            column_messages.append("已清空该列场上所有临时标记。")

            # 检查是否是首次登顶该列（首达奖励）
            # 注意：set_progress 已经将列添加到 completed_columns，所以这里是首次
            is_first_time = True  # 因为刚刚才添加到 completed_columns

            # 登顶奖励逻辑
            base_reward = 50  # 基础奖励
            column_reward = column * 2  # 根据列号的额外奖励
            total_reward = base_reward + column_reward

            # player.add_score(total_reward, f"登顶奖励-第{column}列")
            column_messages.append(f"恭喜您登顶")

            # 首达奖励（只在首次登顶时给予）
            if is_first_time:
                column_messages.append("✦首达奖励")
                first_time_bonus = 20
                player.add_score(first_time_bonus, f"首达奖励-第{column}列")
                column_messages.append(f"大吉大利，今晚吃鸡\n" +
                                        f"肥美的烤鸡扑扇着翅膀飞到了你面前的盘子里，诱人的香气让你迫不及待地切开金黄外皮…不对，等一下？！\n"+
                                        f"获得成就：鹤立oas群\n" +
                                        f"获得奖励：积分+20 \n" +
                                        f"获得现实奖励：纪念币一枚（私信官号领取，不包邮）")

            # 发布列完成事件
            emit_game_event(GameEventType.COLUMN_COMPLETED, session.player_id, {
                "column": column,
                "reward": total_reward,
                "session_id": session_id,
                "starting_progress": 0,
                "completed_columns_count": player.progress.get_completed_count()
            }, session_id)

            reward_messages.append("\n".join(column_messages))

        # 检查是否获胜（3列登顶）
        if player.progress.is_winner():
            reward_messages.append("🎊 恭喜您获胜！您已在3列登顶！")
            session.state = GameState.COMPLETED
            player.games_won += 1

        return "\n".join(reward_messages)

    def confirm_summit(self, session_id: str, column: int) -> Tuple[bool, str]:
        """确认登顶指定列"""
        session = self.get_game_session(session_id)
        if not session:
            return False, "会话不存在"

        player = self.get_player(session.player_id)
        if not player:
            return False, "玩家不存在"

        # 检查是否在等待登顶确认状态
        if session.turn_state != TurnState.WAITING_FOR_SUMMIT_CONFIRMATION:
            return False, "当前不在等待登顶确认状态"

        # 如果待确认列表为空，自动检测所有达到登顶的列（处理GM手动修改的情况）
        if not session.pending_summit_columns:
            for marker in session.temporary_markers:
                column_length = self.map_config.get_column_length(marker.column)
                total_progress = player.progress.get_progress(marker.column) + marker.position
                if total_progress >= column_length:
                    session.pending_summit_columns.append(marker.column)

        # 检查该列是否实际达到登顶（支持GM手动修改的情况）
        marker = session.get_temporary_marker(column)
        if marker:
            column_length = self.map_config.get_column_length(column)
            total_progress = player.progress.get_progress(column) + marker.position

            # 如果该列确实达到登顶，但不在待确认列表中，自动添加
            if total_progress >= column_length and column not in session.pending_summit_columns:
                session.pending_summit_columns.append(column)

        # 检查该列是否在待确认列表中
        if column not in session.pending_summit_columns:
            return False, f"第{column}列未在待确认登顶列表中\n💡 当前待确认列表: {session.pending_summit_columns}"

        # 执行登顶确认，获取奖励信息
        reward_message = self._handle_column_completions(session_id, [column])

        # 从待确认列表中移除
        session.pending_summit_columns.remove(column)

        # 检查是否还有待确认的列
        if len(session.pending_summit_columns) == 0:
            # 所有列都已确认，恢复到决策状态
            session.turn_state = TurnState.DECISION
            final_message = f"{reward_message}\n\n✅ 所有登顶已确认，可以继续游戏！"
            return True, final_message
        else:
            # 还有其他列待确认
            next_column = session.pending_summit_columns[0]
            final_message = f"{reward_message}\n\n⚠️ 请继续确认：数列{next_column}登顶"
            return True, final_message

    def _check_and_trigger_events(self, session_id: str, moved_columns: List[int]) -> str:
        """检查并触发地图事件"""
        # 重新加载陷阱配置（确保获取最新的陷阱数据）
        self.reload_traps_from_config()

        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)
        event_messages = []

        for column in moved_columns:
            marker = session.get_temporary_marker(column)
            if not marker:
                continue

            total_position = player.progress.get_progress(column) + marker.position
            event_key = f"{column}_{total_position}"

            if event_key in self.map_events:
                for event in self.map_events[event_key]:
                    if event.can_trigger(player):
                        trap_message = self._trigger_event(session_id, event, column)  # 传递触发列
                        if trap_message:
                            event_messages.append(trap_message)

        return "\n\n".join(event_messages)

    def _trigger_event(self, session_id: str, event: MapEvent, trigger_column: int = None) -> str:
        """触发地图事件"""
        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)

        event.trigger(player.player_id)

        if event.event_type == EventType.TRAP:
            return self._handle_trap_event(session_id, event, trigger_column)
        elif event.event_type == EventType.ITEM:
            return self._handle_item_event(session_id, event)
        elif event.event_type == EventType.ENCOUNTER:
            return self._handle_encounter_event(session_id, event)

        return ""

    def _handle_trap_event(self, session_id: str, event: MapEvent, trigger_column: int = None) -> str:
        """处理陷阱事件"""
        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)

        if event.name == "小小火球术":
            # 小小火球术：停止一回合，强制骰子结果
            session.turn_state = TurnState.ENDED
            # 设置下回合强制骰子结果
            session.forced_dice_result = [4, 5, 5, 5, 6, 6]
            penalty_amount = get_config("game_config", "game.dice_cost", 10)
            original_score = player.current_score
            player.add_score(-penalty_amount, "陷阱惩罚")
            actual_deduction = original_score - player.current_score

            penalty_msg = f"- 扣除{actual_deduction}积分"
            if actual_deduction < penalty_amount:
                penalty_msg += f"（不足{penalty_amount}积分，仅扣除{actual_deduction}积分）"

            return f"◉触发陷阱：小小火球术！\n📖 火球砸出的坑洞让你无处下脚。\n💬 \"为什么我的火球术不能骰出这种伤害啊?!!\"\n\n⚠️ 惩罚效果：\n- 停止一回合（仍需消耗回合积分）\n- 强制骰子结果：下回合掷骰自动变为 [4,5,5,5,6,6]\n{penalty_msg}"

        elif event.name == "不要回头":
            # 清空触发陷阱的列进度，退回到上一个永久位置
            affected_column = trigger_column if trigger_column else event.column
            marker = session.get_temporary_marker(affected_column)
            if marker:
                session.remove_temporary_marker(affected_column)
                player.progress.set_progress(affected_column, 0)
            # 触发成就：好奇心害死猫
            if hasattr(player, 'achievements'):
                if "好奇心害死猫" not in player.achievements:
                    player.achievements.add("好奇心害死猫")

            return f"◉触发陷阱：\"不要回头\"\n你感到身后一股寒意，当你战战兢兢地转过身试图搞清楚状况时，你发现在看到它脸的那一刻一切都已经晚了……\n清空当前列进度回到上一个永久旗子位置或初始位置。\n\"…话说回来，我有一计。\"\n［获得成就：好奇心害死猫］"

        elif event.name == "河..土地神":
            return f"◉触发陷阱：河..土地神！\n📖 ber得一声，你面前的空地冒出了一个白胡子小老头...\n💬 \"你掉的是这个金骰子还是这个银骰子?\"\n\n🎭 请选择你的回答（使用相应指令）：\n1. 都是我掉的\n2. 金骰子\n3. 银骰子\n4. 普通d6骰子\n5. 我没掉"

        elif event.name == "花言巧语":
            # 获取所有玩家列表用于选择
            from ..services.game_service import GameService
            service = GameService()
            success, players = service.get_all_players()

            player_list_str = ""
            if success and players:
                player_list_str = "\n\n📋 选择一个玩家承受惩罚：\n"
                for player_info in players:
                    if player_info["player_id"] != session.player_id:  # 不显示当前玩家
                        player_list_str += f"{player_info['id']}. {player_info['username']} ({player_info['faction']})\n"

                player_list_str += "\n💡 请输入对应数字选择玩家（如：1）"
            else:
                player_list_str = "\n\n⚠️ 没有找到其他玩家，惩罚效果无法生效"

            return f"◉触发陷阱：花言巧语！\n📖 封锁道路的窗子。\n💬 \"停停，哪儿来的窗子。\"\n\n⚠️ 惩罚效果：\n- 请选择一个玩家\n- 强制该玩家下一轮不能在其当前轮次的列上行进\n- 被选中玩家可投掷1d6，投出6点则抵消惩罚{player_list_str}"

        return f"◉触发未知陷阱：{event.name}"

    def _handle_item_event(self, session_id: str, event: MapEvent) -> str:
        """处理道具事件"""
        player = self.get_player(self.get_game_session(session_id).player_id)

        # 首次获得道具
        player.add_item(event.name)
        # 可以选择保留或半价出售
        return f"🎁 获得道具：{event.name}！\n💡 可以选择保留或半价出售"

    def _handle_encounter_event(self, session_id: str, event: MapEvent) -> str:
        """处理遭遇事件"""
        from ..core.encounter_system import get_encounter_manager

        session = self.get_game_session(session_id)
        player = self.get_player(session.player_id)

        # 使用遭遇系统
        encounter_mgr = get_encounter_manager()
        success, message = encounter_mgr.trigger_encounter(player.player_id, event.name)

        if success:
            return message
        else:
            # 如果遭遇未定义，返回默认消息
            return f"👥 触发遭遇事件：{event.name}！\n💰 打卡后可获得5积分"

    def continue_turn(self, session_id: str) -> bool:
        """继续当前轮次"""
        session = self.get_game_session(session_id)
        if not session:
            return False

        session.turn_state = TurnState.DICE_ROLL
        session.turn_number += 1
        session.current_dice = None
        return True

    def end_turn_actively(self, session_id: str) -> Tuple[bool, str]:
        """主动结束轮次"""
        session = self.get_game_session(session_id)
        if not session:
            return False, "会话不存在"

        player = self.get_player(session.player_id)
        if not player:
            return False, "玩家不存在"

        # 检查是否有待确认的登顶（在主动结束前必须确认所有登顶）
        pending_completions = self._check_column_completions(session_id)
        if pending_completions:
            # 有待确认的登顶，需要先确认
            return False, f"检测到登顶！请先确认：{', '.join([f'数列{c}登顶' for c in pending_completions])}"

        # 将临时标记转换为永久进度
        for marker in session.temporary_markers:
            current_permanent = player.progress.get_progress(marker.column)
            new_progress = current_permanent + marker.position
            player.progress.set_progress(marker.column, new_progress)

        # 清空临时标记
        session.clear_temporary_markers()

        # 检查是否获胜
        if player.progress.is_winner():
            session.state = GameState.COMPLETED
            player.games_won += 1
            return True, "恭喜获胜！已在3列登顶！"

        # 减少buff持续时间
        from ..core.effect_handler import get_effect_handler
        from ..core.item_system import get_buff_manager

        effect_handler = get_effect_handler()
        effect_handler.tick_buffs(player.player_id)

        buff_manager = get_buff_manager()
        buff_manager.clear_expired_buffs(player.player_id)

        # 需要打卡后才能开始下轮
        session.needs_checkin = True
        session.turn_state = TurnState.WAITING_FOR_CHECKIN

        return True, "轮次结束，请完成打卡后继续游戏"

    def check_passive_stop(self, session_id: str) -> bool:
        """检查是否触发被动停止"""
        session = self.get_game_session(session_id)
        if not session or not session.current_dice:
            return False

        # 如果已有3个临时标记，检查是否还能移动
        if len(session.temporary_markers) == 3:
            possible_combinations = session.current_dice.get_possible_combinations()
            current_columns = [marker.column for marker in session.temporary_markers]

            # 检查是否有任何组合可以移动现有标记
            for combo in possible_combinations:
                if any(col in current_columns for col in combo):
                    return False

            # 无法移动，触发被动停止
            self._trigger_passive_stop(session_id)
            return True

        return False

    def _trigger_passive_stop(self, session_id: str):
        """触发被动停止"""
        session = self.get_game_session(session_id)

        # 清空所有临时标记进度
        session.clear_temporary_markers()
        session.state = GameState.FAILED
        session.turn_state = TurnState.ENDED

    def complete_checkin(self, session_id: str) -> bool:
        """完成打卡，恢复游戏功能"""
        session = self.get_game_session(session_id)
        if not session:
            return False

        session.needs_checkin = False
        session.turn_state = TurnState.DICE_ROLL
        session.first_turn = True  # 新轮次开始
        return True

    def get_game_status(self, player_id: str) -> Dict:
        """获取游戏状态"""
        player = self.get_player(player_id)
        session = self.get_player_active_session(player_id)

        if not player:
            return {"error": "玩家不存在"}

        status = {
            "player": {
                "username": player.username,
                "faction": player.faction.value,
                "current_score": player.current_score,
                "completed_columns": list(player.progress.completed_columns),
                "completed_count": player.progress.get_completed_count()
            },
            "permanent_progress": player.progress.permanent_progress,
        }

        if session:
            status["session"] = {
                "session_id": session.session_id,
                "state": session.state.value,
                "turn_state": session.turn_state.value,
                "turn_number": session.turn_number,
                "temporary_markers": [
                    {"column": m.column, "position": m.position}
                    for m in session.temporary_markers
                ],
                "remaining_markers": 3 - len(session.temporary_markers),
                "needs_checkin": session.needs_checkin,
                "dice_results": session.current_dice.results if session.current_dice else None
            }

        return status