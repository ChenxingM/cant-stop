"""
效果处理器 - 处理遭遇、道具和其他游戏事件产生的各种效果
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class EffectType(Enum):
    """效果类型"""
    # 积分相关
    SCORE_CHANGE = "score_change"
    SCORE_CHANGE_PERCENTAGE = "score_change_percentage"

    # 骰子相关
    DICE_COUNT_CHANGE = "dice_count_change"
    FORCED_DICE_RESULT = "forced_dice_result"
    DICE_MODIFIER = "dice_modifier"
    EXTRA_DICE_WITH_RISK = "extra_dice_with_risk"
    EXTRA_DICE = "extra_dice"
    REPLACE_WITH_PREVIOUS = "replace_with_previous"
    REROLL_SELECTED = "reroll_selected"

    # 骰子判定相关
    DICE_CHECK = "dice_check"
    DICE_CHECK_ODD_EVEN = "dice_check_odd_even"
    DICE_CHECK_COMBINATIONS = "dice_check_combinations"

    # 道具相关
    GIVE_ITEM = "give_item"
    RANDOM_ITEM = "random_item"
    GIVE_REROLL_TOKEN = "give_reroll_token"

    # 回合控制
    SKIP_TURN = "skip_turn"
    SKIP_MULTIPLE_TURNS = "skip_multiple_turns"
    VOID_TURN = "void_turn"
    VOID_TURN_OR_SKIP = "void_turn_or_skip"
    END_SESSION = "end_session"
    PREVENT_END_TURN = "prevent_end_turn"
    FORCE_EXTRA_TURNS = "force_extra_turns"

    # Buff相关
    PERMANENT_BUFF = "permanent_buff"
    COST_REDUCTION_BUFF = "cost_reduction_buff"
    REROLL_BUFF = "reroll_buff"
    SELECTIVE_REROLL_BUFF = "selective_reroll_buff"

    # 特殊效果
    UNLOCK_COMMANDS = "unlock_commands"
    DELAYED_REWARD = "delayed_reward"
    DELAYED_COMPETITION = "delayed_competition"
    CLEAR_TEMP_MARKERS = "clear_temp_markers"
    DISGUISE = "disguise"
    COOPERATIVE_DICE = "cooperative_dice"
    RESET_COLUMN_PROGRESS = "reset_column_progress"
    ALL_COLUMNS_RETREAT = "all_columns_retreat"
    FORCE_ARTWORK = "force_artwork"
    PVP_DICE_BATTLE = "pvp_dice_battle"

    # 复合效果
    COMPOSITE = "composite"

    # 其他
    NOTHING = "nothing"
    RETRY_LAST_ENCOUNTER = "retry_last_encounter"
    MODIFY_ENCOUNTER_FOR_OTHERS = "modify_encounter_for_others"


@dataclass
class DelayedEffect:
    """延迟效果"""
    player_id: str
    effect_type: str
    effect_data: Dict[str, Any]
    trigger_turn: int  # 在哪个回合触发
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""


@dataclass
class ActiveBuff:
    """活跃的Buff"""
    player_id: str
    buff_type: str
    buff_data: Dict[str, Any]
    duration: int  # 持续回合数，-1表示永久
    remaining_turns: int
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""


class EffectHandler:
    """效果处理器"""

    def __init__(self):
        self.delayed_effects: Dict[str, List[DelayedEffect]] = {}  # player_id -> [effects]
        self.active_buffs: Dict[str, List[ActiveBuff]] = {}  # player_id -> [buffs]
        self.player_unlocked_commands: Dict[str, List[str]] = {}  # player_id -> [commands]

        # 可用道具列表
        self.available_items = [
            "后悔券", "免费掷骰券", "意外之财", "变身器",
            "水壶", "食物", "手电筒", "蓝玫瑰", "黄玫瑰", "红玫瑰",
            "重投券", "加速券", "保护券"
        ]

    def apply_effect(self, player_id: str, effect_data: Dict[str, Any],
                    game_engine: Any, turn_number: int = 0) -> Tuple[bool, str, Dict[str, Any]]:
        """
        应用效果

        Args:
            player_id: 玩家ID
            effect_data: 效果数据
            game_engine: 游戏引擎实例（用于修改游戏状态）
            turn_number: 当前回合数

        Returns:
            (成功, 消息, 额外数据)
        """
        effect_type = effect_data.get("type")

        if effect_type == "score_change":
            return self._apply_score_change(player_id, effect_data, game_engine)
        elif effect_type == "dice_count_change":
            return self._apply_dice_count_change(player_id, effect_data, turn_number)
        elif effect_type == "forced_dice_result":
            return self._apply_forced_dice_result(player_id, effect_data, game_engine)
        elif effect_type == "dice_modifier":
            return self._apply_dice_modifier(player_id, effect_data, turn_number)
        elif effect_type == "give_item":
            return self._apply_give_item(player_id, effect_data, game_engine)
        elif effect_type == "random_item":
            return self._apply_random_item(player_id, game_engine)
        elif effect_type == "skip_turn":
            return self._apply_skip_turn(player_id, effect_data, game_engine)
        elif effect_type == "dice_check":
            return self._apply_dice_check(player_id, effect_data, game_engine, turn_number)
        elif effect_type == "unlock_commands":
            return self._apply_unlock_commands(player_id, effect_data)
        elif effect_type == "permanent_buff":
            return self._apply_permanent_buff(player_id, effect_data)
        elif effect_type == "delayed_reward":
            return self._apply_delayed_reward(player_id, effect_data, turn_number)
        elif effect_type == "reroll_buff":
            return self._apply_reroll_buff(player_id, effect_data)
        elif effect_type == "give_reroll_token":
            return self._apply_give_item(player_id, {"item": "重投券"}, game_engine)
        elif effect_type == "clear_temp_markers":
            return self._apply_clear_temp_markers(player_id, effect_data, game_engine)
        elif effect_type == "extra_dice_with_risk":
            return self._apply_extra_dice_with_risk(player_id, effect_data, turn_number)
        elif effect_type == "cost_reduction_buff":
            return self._apply_cost_reduction_buff(player_id, effect_data)
        elif effect_type == "selective_reroll_buff":
            return self._apply_selective_reroll_buff(player_id, effect_data)
        elif effect_type == "void_turn":
            return self._apply_void_turn(player_id, game_engine)
        elif effect_type == "end_session":
            return self._apply_end_session(player_id, effect_data, game_engine)
        elif effect_type == "nothing":
            return True, "", {}
        # 新增陷阱效果
        elif effect_type == "score_change_percentage":
            return self._apply_score_change_percentage(player_id, effect_data, game_engine)
        elif effect_type == "prevent_end_turn":
            return self._apply_prevent_end_turn(player_id, effect_data)
        elif effect_type == "reset_column_progress":
            return self._apply_reset_column_progress(player_id, effect_data, game_engine)
        elif effect_type == "force_artwork":
            return self._apply_force_artwork(player_id, effect_data, game_engine)
        elif effect_type == "dice_check_odd_even":
            return self._apply_dice_check_odd_even(player_id, effect_data, turn_number)
        elif effect_type == "extra_dice":
            return self._apply_extra_dice(player_id, effect_data)
        elif effect_type == "void_turn_or_skip":
            return self._apply_void_turn_or_skip(player_id, effect_data, game_engine)
        elif effect_type == "dice_check_combinations":
            return self._apply_dice_check_combinations(player_id, effect_data, turn_number)
        elif effect_type == "pvp_dice_battle":
            return self._apply_pvp_dice_battle(player_id, effect_data, game_engine)
        elif effect_type == "force_extra_turns":
            return self._apply_force_extra_turns(player_id, effect_data)
        elif effect_type == "all_columns_retreat":
            return self._apply_all_columns_retreat(player_id, effect_data, game_engine)
        elif effect_type == "skip_multiple_turns":
            return self._apply_skip_multiple_turns(player_id, effect_data, game_engine)
        elif effect_type == "composite":
            return self._apply_composite(player_id, effect_data, game_engine, turn_number)
        else:
            return False, f"未知效果类型: {effect_type}", {}

    def _apply_score_change(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """应用积分变化"""
        value = effect_data.get("value", 0)

        try:
            player = game_engine.get_player(player_id)
            old_score = player.current_score

            if value > 0:
                player.add_score(value, "遭遇奖励")
                message = f"💰 获得 {value} 积分！"
            else:
                player.add_score(value, "遭遇惩罚")
                actual_deduction = old_score - player.current_score
                message = f"💸 失去 {abs(actual_deduction)} 积分"
                if actual_deduction < abs(value):
                    message += f"（不足{abs(value)}积分，仅扣除{actual_deduction}积分）"

            return True, message, {"score_change": value}
        except Exception as e:
            return False, f"积分变化失败: {e}", {}

    def _apply_dice_count_change(self, player_id: str, effect_data: Dict, turn_number: int) -> Tuple[bool, str, Dict]:
        """应用骰子数量变化"""
        new_count = effect_data.get("value", 6)
        duration = effect_data.get("duration", 1)

        # 添加延迟效果
        delayed = DelayedEffect(
            player_id=player_id,
            effect_type="dice_count_override",
            effect_data={"count": new_count},
            trigger_turn=turn_number + 1,
            description=f"下次投掷使用{new_count}个骰子"
        )

        if player_id not in self.delayed_effects:
            self.delayed_effects[player_id] = []
        self.delayed_effects[player_id].append(delayed)

        message = f"🎲 下一次投掷将使用 {new_count} 个骰子！"
        return True, message, {"dice_count": new_count, "duration": duration}

    def _apply_forced_dice_result(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """应用强制骰子结果"""
        dice_result = effect_data.get("value", [])
        score_penalty = effect_data.get("score_penalty", 0)

        try:
            # 设置强制骰子结果（需要在game_engine中实现）
            session = game_engine.get_player_active_session(player_id)
            if session:
                session.forced_dice_result = dice_result
                message = f"🎲 下次掷骰结果将被强制为: {dice_result}"

                if score_penalty != 0:
                    player = game_engine.get_player(player_id)
                    player.add_score(score_penalty, "遭遇惩罚")
                    message += f"\n💸 同时失去 {abs(score_penalty)} 积分"

                return True, message, {"forced_dice": dice_result}
        except Exception as e:
            return False, f"设置强制骰子失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_dice_modifier(self, player_id: str, effect_data: Dict, turn_number: int) -> Tuple[bool, str, Dict]:
        """应用骰子修正值"""
        modifier_value = effect_data.get("value", 0)
        duration = effect_data.get("duration", 1)
        value_from_dice = effect_data.get("value_from_dice", False)
        negative = effect_data.get("negative", False)

        # 如果modifier来自骰子结果，需要先投掷
        if value_from_dice:
            dice_result = random.randint(1, 6)
            modifier_value = dice_result if not negative else -dice_result
            message = f"🎲 投掷结果: {dice_result}\n"
        else:
            message = ""

        # 添加buff
        buff = ActiveBuff(
            player_id=player_id,
            buff_type="dice_modifier",
            buff_data={"modifier": modifier_value},
            duration=duration,
            remaining_turns=duration,
            description=f"骰子点数{'+' if modifier_value > 0 else ''}{modifier_value}"
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        if modifier_value > 0:
            message += f"✨ 获得增益：接下来{duration}回合骰子点数+{modifier_value}！"
        else:
            message += f"⚠️ 获得减益：接下来{duration}回合骰子点数{modifier_value}！"

        return True, message, {"dice_modifier": modifier_value, "duration": duration}

    def _apply_give_item(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """给予道具"""
        item_name = effect_data.get("item", "")
        quantity = effect_data.get("quantity", 1)

        try:
            player = game_engine.get_player(player_id)
            # 假设player有add_item方法
            if hasattr(player, 'add_item'):
                player.add_item(item_name, quantity)
                message = f"🎁 获得道具：{item_name} x{quantity}！"
                return True, message, {"item": item_name, "quantity": quantity}
            else:
                # 如果没有道具系统，记录到临时列表
                message = f"🎁 获得道具：{item_name} x{quantity}（道具系统暂未实现）"
                return True, message, {"item": item_name, "quantity": quantity}
        except Exception as e:
            return False, f"给予道具失败: {e}", {}

    def _apply_random_item(self, player_id: str, game_engine: Any) -> Tuple[bool, str, Dict]:
        """给予随机道具"""
        item = random.choice(self.available_items)
        return self._apply_give_item(player_id, {"item": item, "quantity": 1}, game_engine)

    def _apply_skip_turn(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """跳过回合"""
        cost_score = effect_data.get("cost_score", True)

        try:
            session = game_engine.get_player_active_session(player_id)
            if session:
                # 设置会话状态为已结束回合
                session.turn_state = game_engine.TurnState.END_OF_TURN

                message = "⏭️ 本回合被跳过"

                if cost_score:
                    # 消耗回合积分
                    dice_cost = game_engine.config.get('game.dice_cost', 10)
                    player = game_engine.get_player(player_id)
                    player.add_score(-dice_cost, "跳过回合消耗")
                    message += f"（消耗{dice_cost}积分）"

                return True, message, {"skip_turn": True}
        except Exception as e:
            return False, f"跳过回合失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_dice_check(self, player_id: str, effect_data: Dict,
                         game_engine: Any, turn_number: int) -> Tuple[bool, str, Dict]:
        """执行骰子判定"""
        dice_type = effect_data.get("dice", "1d6")

        # 解析骰子类型 (如 "1d6", "1d20")
        if 'd' in dice_type:
            parts = dice_type.split('d')
            count = int(parts[0]) if parts[0] else 1
            sides = int(parts[1])
        else:
            count, sides = 1, 6

        # 投掷骰子
        dice_result = sum(random.randint(1, sides) for _ in range(count))

        message = f"🎲 骰子判定: {dice_result}\n"

        # 检查成功条件
        success_threshold = effect_data.get("success_threshold")
        fail_value = effect_data.get("fail_value")
        thresholds = effect_data.get("thresholds")

        if thresholds:
            # 多阈值判定
            for threshold in thresholds:
                if "exact" in threshold and dice_result == threshold["exact"]:
                    effect = threshold["effect"]
                    msg = threshold.get("message", "")
                    success, sub_msg, data = self.apply_effect(player_id, effect, game_engine, turn_number)
                    return success, message + msg + "\n" + sub_msg, data
                elif "min" in threshold and "max" in threshold:
                    if threshold["min"] <= dice_result <= threshold["max"]:
                        effect = threshold["effect"]
                        msg = threshold.get("message", "")
                        success, sub_msg, data = self.apply_effect(player_id, effect, game_engine, turn_number)
                        return success, message + msg + "\n" + sub_msg, data
                elif "max" in threshold and dice_result <= threshold["max"]:
                    effect = threshold["effect"]
                    msg = threshold.get("message", "")
                    success, sub_msg, data = self.apply_effect(player_id, effect, game_engine, turn_number)
                    return success, message + msg + "\n" + sub_msg, data

        elif success_threshold is not None:
            # 简单成功/失败判定
            if dice_result >= success_threshold:
                success_effect = effect_data.get("success_effect", {})
                success, sub_msg, data = self.apply_effect(player_id, success_effect, game_engine, turn_number)
                return success, message + "✅ 判定成功！\n" + sub_msg, data
            else:
                fail_effect = effect_data.get("fail_effect", {})
                success, sub_msg, data = self.apply_effect(player_id, fail_effect, game_engine, turn_number)
                return success, message + "❌ 判定失败！\n" + sub_msg, data

        elif fail_value is not None:
            # 特定失败值
            if dice_result == fail_value:
                fail_effect = effect_data.get("fail_effect", {})
                success, sub_msg, data = self.apply_effect(player_id, fail_effect, game_engine, turn_number)
                return success, message + "❌ 触发失败条件！\n" + sub_msg, data

        return True, message + "判定完成", {"dice_result": dice_result}

    def _apply_unlock_commands(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """解锁指令"""
        commands = effect_data.get("commands", [])
        daily_limit = effect_data.get("daily_limit", 0)

        if player_id not in self.player_unlocked_commands:
            self.player_unlocked_commands[player_id] = []

        self.player_unlocked_commands[player_id].extend(commands)

        command_list = "、".join(commands)
        message = f"🔓 解锁新指令：{command_list}"
        if daily_limit > 0:
            message += f"（每天限{daily_limit}次）"

        return True, message, {"unlocked_commands": commands, "daily_limit": daily_limit}

    def _apply_permanent_buff(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """应用永久buff"""
        buff_type = effect_data.get("buff", "")
        value = effect_data.get("value", 0)

        buff = ActiveBuff(
            player_id=player_id,
            buff_type=buff_type,
            buff_data={"value": value},
            duration=-1,  # 永久
            remaining_turns=-1,
            description=f"永久{buff_type}"
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        message = f"✨ 获得永久增益：{buff_type}！"
        return True, message, {"buff": buff_type, "value": value}

    def _apply_delayed_reward(self, player_id: str, effect_data: Dict, turn_number: int) -> Tuple[bool, str, Dict]:
        """应用延迟奖励"""
        turns = effect_data.get("turns", 3)
        reward = effect_data.get("reward", {})
        restriction = effect_data.get("restriction", None)

        delayed = DelayedEffect(
            player_id=player_id,
            effect_type="delayed_reward",
            effect_data=reward,
            trigger_turn=turn_number + turns,
            description=f"{turns}回合后领取奖励"
        )

        if player_id not in self.delayed_effects:
            self.delayed_effects[player_id] = []
        self.delayed_effects[player_id].append(delayed)

        message = f"⏳ 延迟奖励：{turns}回合后可领取"
        if restriction:
            message += f"\n⚠️ 限制：{restriction}"

        return True, message, {"delayed_turns": turns, "reward": reward}

    def _apply_reroll_buff(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """应用重投buff"""
        duration = effect_data.get("duration", 3)
        per_turn_limit = effect_data.get("per_turn_limit", 1)

        buff = ActiveBuff(
            player_id=player_id,
            buff_type="reroll",
            buff_data={"per_turn_limit": per_turn_limit},
            duration=duration,
            remaining_turns=duration,
            description=f"可重投骰子（每回合{per_turn_limit}次）"
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        message = f"✨ 获得重投buff：接下来{duration}回合可重投骰子（每回合{per_turn_limit}次）！"
        return True, message, {"duration": duration, "limit": per_turn_limit}

    def _apply_clear_temp_markers(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """清除临时标记"""
        player_choice = effect_data.get("player_choice", False)

        if player_choice:
            message = "🧹 你可以选择清除任意一列的临时标记（使用指令：清除临时标记 [列号]）"
            return True, message, {"action_required": "choose_column_to_clear"}
        else:
            # 直接清除所有临时标记
            try:
                session = game_engine.get_player_active_session(player_id)
                if session:
                    session.clear_all_temporary_markers()
                    message = "🧹 清除了所有临时标记！"
                    return True, message, {}
            except Exception as e:
                return False, f"清除失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_extra_dice_with_risk(self, player_id: str, effect_data: Dict, turn_number: int) -> Tuple[bool, str, Dict]:
        """额外骰子但有风险"""
        risk_value = effect_data.get("risk_value", 6)

        delayed = DelayedEffect(
            player_id=player_id,
            effect_type="extra_dice_risk",
            effect_data={"risk_value": risk_value},
            trigger_turn=turn_number + 1,
            description="额外投掷1d6，若为6则本回合作废"
        )

        if player_id not in self.delayed_effects:
            self.delayed_effects[player_id] = []
        self.delayed_effects[player_id].append(delayed)

        message = f"⚡ 下回合将额外投掷1d6，若结果为{risk_value}则本回合作废！"
        return True, message, {"risk_value": risk_value}

    def _apply_cost_reduction_buff(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """应用花费减少buff"""
        value = effect_data.get("value", 1)
        duration = effect_data.get("duration", 3)

        buff = ActiveBuff(
            player_id=player_id,
            buff_type="cost_reduction",
            buff_data={"reduction": value},
            duration=duration,
            remaining_turns=duration,
            description=f"掷骰花费-{value}"
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        message = f"✨ 获得「平和」buff：接下来{duration}回合掷骰花费-{value}！"
        return True, message, {"duration": duration, "reduction": value}

    def _apply_selective_reroll_buff(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """应用选择性重投buff"""
        count = effect_data.get("count", 3)
        duration = effect_data.get("duration", 3)

        buff = ActiveBuff(
            player_id=player_id,
            buff_type="selective_reroll",
            buff_data={"count": count},
            duration=duration,
            remaining_turns=duration,
            description=f"可重投任意{count}个骰子"
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        message = f"✨ 获得「艺术灵感」buff：接下来{duration}回合可选择重投{count}个骰子！"
        return True, message, {"duration": duration, "count": count}

    def _apply_void_turn(self, player_id: str, game_engine: Any) -> Tuple[bool, str, Dict]:
        """作废本回合"""
        try:
            session = game_engine.get_player_active_session(player_id)
            if session:
                # 清除所有临时标记
                session.clear_all_temporary_markers()
                # 结束回合
                session.turn_state = game_engine.TurnState.END_OF_TURN

                message = "❌ 本回合作废！所有进度清零"
                return True, message, {"void_turn": True}
        except Exception as e:
            return False, f"作废回合失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_end_session(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """结束游戏会话"""
        save_progress = effect_data.get("save_progress", True)

        try:
            session = game_engine.get_player_active_session(player_id)
            if session:
                if save_progress:
                    # 保存进度并结束
                    game_engine.end_game(player_id, save_progress=True)
                    message = "🏁 游戏结束，进度已保存"
                else:
                    game_engine.end_game(player_id, save_progress=False)
                    message = "🏁 游戏结束"

                return True, message, {"session_ended": True}
        except Exception as e:
            return False, f"结束会话失败: {e}", {}

        return False, "未找到活跃会话", {}

    # 辅助方法

    def get_delayed_effects_for_turn(self, player_id: str, turn_number: int) -> List[DelayedEffect]:
        """获取在指定回合触发的延迟效果"""
        if player_id not in self.delayed_effects:
            return []

        effects = []
        remaining = []

        for effect in self.delayed_effects[player_id]:
            if effect.trigger_turn == turn_number:
                effects.append(effect)
            else:
                remaining.append(effect)

        self.delayed_effects[player_id] = remaining

        return effects

    def get_active_buffs(self, player_id: str) -> List[ActiveBuff]:
        """获取玩家的所有活跃buff"""
        return self.active_buffs.get(player_id, [])

    def tick_buffs(self, player_id: str):
        """减少buff持续时间（每回合调用一次）"""
        if player_id not in self.active_buffs:
            return

        remaining = []
        for buff in self.active_buffs[player_id]:
            if buff.duration == -1:  # 永久buff
                remaining.append(buff)
            else:
                buff.remaining_turns -= 1
                if buff.remaining_turns > 0:
                    remaining.append(buff)

        self.active_buffs[player_id] = remaining

    def has_unlocked_command(self, player_id: str, command: str) -> bool:
        """检查玩家是否已解锁某个指令"""
        if player_id not in self.player_unlocked_commands:
            return False
        return command in self.player_unlocked_commands[player_id]

    def get_dice_modifier(self, player_id: str) -> int:
        """获取玩家的骰子修正值"""
        total_modifier = 0
        for buff in self.get_active_buffs(player_id):
            if buff.buff_type == "dice_modifier":
                total_modifier += buff.buff_data.get("modifier", 0)
        return total_modifier

    def get_cost_reduction(self, player_id: str) -> int:
        """获取花费减少值"""
        total_reduction = 0
        for buff in self.get_active_buffs(player_id):
            if buff.buff_type in ["cost_reduction", "dice_cost_reduction"]:
                total_reduction += buff.buff_data.get("reduction", 0)
                total_reduction += buff.buff_data.get("value", 0)
        return total_reduction

    # ========== 新增陷阱效果实现 ==========

    def _apply_score_change_percentage(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """按百分比改变积分"""
        percentage = effect_data.get("value", 0)  # -0.25 = 减少25%
        description = effect_data.get("description", "")

        try:
            from ..database.database import DatabaseManager
            db_manager = DatabaseManager()
            player = db_manager.get_player(player_id)

            if not player:
                return False, "玩家不存在", {}

            current_score = player.current_score
            change_amount = int(current_score * percentage)

            db_manager.update_player_score(player_id, change_amount, description or "陷阱效果")

            if change_amount > 0:
                message = f"💰 积分增加 {abs(int(percentage * 100))}%（+{change_amount}）"
            else:
                message = f"💸 积分减少 {abs(int(percentage * 100))}%（{change_amount}）"

            return True, message, {"score_change": change_amount}
        except Exception as e:
            return False, f"百分比积分变化失败: {e}", {}

    def _apply_prevent_end_turn(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """禁止主动结束回合"""
        description = effect_data.get("description", "在完成此惩罚前不得主动结束当前轮次")

        # 添加buff禁止结束回合
        buff = ActiveBuff(
            player_id=player_id,
            buff_type="prevent_end_turn",
            buff_data={},
            duration=1,
            remaining_turns=1,
            description=description
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        return True, f"⚠️ {description}", {"prevent_end": True}

    def _apply_reset_column_progress(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """重置列进度"""
        try:
            session = game_engine.get_player_active_session(player_id)
            if not session:
                return False, "未找到活跃会话", {}

            # 获取当前列（从最近移动的标记获取）
            if not session.temporary_markers:
                return False, "没有临时标记可以重置", {}

            # 清空当前列的临时标记，回到永久标记位置
            # 这个逻辑需要在game_engine中实现
            session.reset_current_column_progress = True

            return True, "🔄 当前列进度已重置，回到上一个永久旗子位置或初始位置", {"column_reset": True}
        except Exception as e:
            return False, f"重置列进度失败: {e}", {}

    def _apply_force_artwork(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """强制绘制"""
        achievement_check = effect_data.get("achievement_check")
        description = effect_data.get("description", "强制暂停该轮次直到你完成此陷阱相关绘制（不计算积分）")

        # 检查是否有免疫成就
        if achievement_check:
            from ..core.achievement_manager import AchievementManager
            manager = AchievementManager()
            if manager.check_achievement_unlocked(achievement_check):
                return True, f"✨ 你拥有【{achievement_check}】成就，免疫此效果！", {"immune": True}

        # 设置强制绘制状态
        try:
            session = game_engine.get_player_active_session(player_id)
            if session:
                session.forced_artwork = True
                return True, f"🎨 {description}", {"forced_artwork": True}
        except Exception as e:
            return False, f"设置强制绘制失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_dice_check_odd_even(self, player_id: str, effect_data: Dict, turn_number: int) -> Tuple[bool, str, Dict]:
        """奇偶数检查（延迟到下一回合）"""
        success_effect = effect_data.get("success_effect", {})
        fail_effect = effect_data.get("fail_effect", {})
        description = effect_data.get("description", "下回合根据奇数个数判断结果")

        # 添加延迟效果
        delayed = DelayedEffect(
            player_id=player_id,
            effect_type="odd_even_check",
            effect_data={
                "success_effect": success_effect,
                "fail_effect": fail_effect
            },
            trigger_turn=turn_number + 1,
            description=description
        )

        if player_id not in self.delayed_effects:
            self.delayed_effects[player_id] = []
        self.delayed_effects[player_id].append(delayed)

        return True, f"🎲 {description}", {"delayed_check": True}

    def _apply_extra_dice(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """额外骰子"""
        dice = effect_data.get("dice", "1d6")
        description = effect_data.get("description", "额外获得一个d6骰")

        # 添加buff给玩家额外骰子
        buff = ActiveBuff(
            player_id=player_id,
            buff_type="extra_dice",
            buff_data={"dice": dice},
            duration=1,
            remaining_turns=1,
            description=description
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        return True, f"🎲 {description}", {"extra_dice": dice}

    def _apply_void_turn_or_skip(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """作废回合或跳过"""
        description = effect_data.get("description", "本回合作废或下轮次停止一回合")

        # 这个需要在游戏逻辑中判断
        # 如果当前回合触发了失败被动停止，则改为跳过下一回合
        # 否则作废本回合
        try:
            session = game_engine.get_player_active_session(player_id)
            if session:
                # 标记为可能作废或跳过
                session.void_or_skip_pending = True
                return True, f"⚠️ {description}", {"void_or_skip": True}
        except Exception as e:
            return False, f"设置作废/跳过失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_dice_check_combinations(self, player_id: str, effect_data: Dict, turn_number: int) -> Tuple[bool, str, Dict]:
        """检查骰子组合数量"""
        threshold = effect_data.get("threshold", 8)
        success_effect = effect_data.get("success_effect", {})
        fail_effect = effect_data.get("fail_effect", {})
        description = effect_data.get("description", f"下回合33加值数量需达到{threshold}种")

        # 添加延迟效果
        delayed = DelayedEffect(
            player_id=player_id,
            effect_type="combination_check",
            effect_data={
                "threshold": threshold,
                "success_effect": success_effect,
                "fail_effect": fail_effect
            },
            trigger_turn=turn_number + 1,
            description=description
        )

        if player_id not in self.delayed_effects:
            self.delayed_effects[player_id] = []
        self.delayed_effects[player_id].append(delayed)

        return True, f"🎲 {description}", {"delayed_check": True}

    def _apply_pvp_dice_battle(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """玩家对战"""
        winner_reward = effect_data.get("winner_reward", {})
        loser_penalty = effect_data.get("loser_penalty", {})
        tie_effect = effect_data.get("tie_effect", {})

        # 这需要UI交互来选择对手和投掷骰子
        # 暂时返回提示消息
        message = "⚔️ 请选择一位玩家进行对战！\n"
        message += "双方将各投掷1d6，点数大者获胜\n"
        message += f"胜者：{winner_reward.get('description', '获得奖励')}\n"
        message += f"败者：{loser_penalty.get('description', '受到惩罚')}\n"
        message += f"平局：{tie_effect.get('description', '无事发生')}"

        # 设置PVP状态
        try:
            session = game_engine.get_player_active_session(player_id)
            if session:
                session.pvp_battle_pending = {
                    "winner_reward": winner_reward,
                    "loser_penalty": loser_penalty,
                    "tie_effect": tie_effect
                }
                return True, message, {"pvp_battle": True}
        except Exception as e:
            return False, f"设置PVP对战失败: {e}", {}

        return False, "未找到活跃会话", {}

    def _apply_force_extra_turns(self, player_id: str, effect_data: Dict) -> Tuple[bool, str, Dict]:
        """强制额外回合"""
        turns = effect_data.get("turns", 2)
        description = effect_data.get("description", f"你强制再进行{turns}回合后才能结束该轮次")

        # 添加buff
        buff = ActiveBuff(
            player_id=player_id,
            buff_type="force_extra_turns",
            buff_data={"turns": turns},
            duration=-1,  # 直到完成额外回合
            remaining_turns=-1,
            description=description
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        return True, f"⏰ {description}", {"extra_turns": turns}

    def _apply_all_columns_retreat(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """所有列回退"""
        value = effect_data.get("value", 1)
        description = effect_data.get("description", f"所有列的当前进度回退{value}格")

        try:
            session = game_engine.get_player_active_session(player_id)
            if not session:
                return False, "未找到活跃会话", {}

            # 回退所有临时标记
            retreated = []
            for marker in session.temporary_markers:
                if marker.position > 0:
                    marker.position = max(0, marker.position - value)
                    retreated.append(marker.column)

            if retreated:
                message = f"📉 {description}\n受影响的列：{', '.join(map(str, retreated))}"
            else:
                message = "📉 所有标记已在起点，无法回退"

            return True, message, {"retreated_columns": retreated}
        except Exception as e:
            return False, f"回退进度失败: {e}", {}

    def _apply_skip_multiple_turns(self, player_id: str, effect_data: Dict, game_engine: Any) -> Tuple[bool, str, Dict]:
        """跳过多个回合"""
        turns = effect_data.get("turns", 2)
        cost_score = effect_data.get("cost_score", True)
        description = effect_data.get("description", f"暂停{turns}回合")

        # 添加buff
        buff = ActiveBuff(
            player_id=player_id,
            buff_type="skip_turns",
            buff_data={"turns": turns, "cost_score": cost_score},
            duration=turns,
            remaining_turns=turns,
            description=description
        )

        if player_id not in self.active_buffs:
            self.active_buffs[player_id] = []
        self.active_buffs[player_id].append(buff)

        if cost_score:
            return True, f"⏸️ {description}（每回合消耗积分）", {"skip_turns": turns}
        else:
            return True, f"⏸️ {description}", {"skip_turns": turns}

    def _apply_composite(self, player_id: str, effect_data: Dict, game_engine: Any, turn_number: int) -> Tuple[bool, str, Dict]:
        """复合效果（依次应用多个效果）"""
        effects = effect_data.get("effects", [])
        description = effect_data.get("description", "")

        messages = []
        all_data = {}

        for effect in effects:
            success, message, data = self.apply_effect(player_id, effect, game_engine, turn_number)
            if message:
                messages.append(message)
            all_data.update(data)

        final_message = "\n".join(messages) if messages else description
        return True, final_message, all_data


# 全局效果处理器实例
_effect_handler: Optional[EffectHandler] = None


def get_effect_handler() -> EffectHandler:
    """获取全局效果处理器实例"""
    global _effect_handler
    if _effect_handler is None:
        _effect_handler = EffectHandler()
    return _effect_handler
