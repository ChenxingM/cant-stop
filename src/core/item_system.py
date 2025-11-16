"""
道具系统核心
包含道具效果、Buff管理和道具使用逻辑
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import random


class ItemEffectType(Enum):
    """道具效果类型枚举"""
    # 积分相关
    SCORE = "score"                          # 直接获得积分
    DICE_COST_REDUCTION = "dice_cost_reduction"  # 降低掷骰消耗
    SHOP_DISCOUNT_50 = "shop_discount_50"    # 商店5折
    SHOP_DISCOUNT_20 = "shop_discount_20"    # 商店8折

    # 骰子相关
    DICE_PLUS_1 = "dice_plus_1"              # 骰子结果+1
    DICE_MINUS_1 = "dice_minus_1"            # 骰子结果-1
    REROLL_ON_CONDITION = "reroll_on_condition"  # 条件重骰
    REROLL_3_DICE = "reroll_3_dice"          # 重骰3个骰子
    MODIFY_DICE = "modify_dice"              # 修改骰子结果

    # 陷阱相关
    TRAP_IMMUNITY = "trap_immunity"          # 陷阱免疫

    # 回合相关
    RETRY_TURN = "retry_turn"                # 重试回合
    REFRESH_LAST_ITEM = "refresh_last_item"  # 刷新上个道具

    # 移动相关
    EXTRA_MOVEMENT = "extra_movement"        # 额外移动

    # 特殊效果
    RANDOM_REWARD = "random_reward"          # 随机奖励
    SPECIAL = "special"                      # 特殊效果
    COMMEMORATIVE = "commemorative"          # 纪念品
    NOTHING = "nothing"                      # 无事发生


class BuffType(Enum):
    """Buff类型枚举"""
    DICE_MODIFIER = "dice_modifier"          # 骰子修正
    COST_REDUCTION = "cost_reduction"        # 消耗减免
    SHOP_DISCOUNT = "shop_discount"          # 商店折扣
    TRAP_IMMUNITY = "trap_immunity"          # 陷阱免疫
    REROLL_AVAILABLE = "reroll_available"    # 可重骰
    RETRY_TURN_AVAILABLE = "retry_turn_available"  # 可重试回合


@dataclass
class PlayerBuff:
    """玩家Buff/效果"""
    buff_type: BuffType
    value: Any  # buff的数值（如+1, -2, 0.5等）
    duration: int = 1  # 持续轮数（-1表示永久）
    source: str = "unknown"  # buff来源
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def is_expired(self) -> bool:
        """检查buff是否已过期"""
        return self.duration == 0

    def consume(self) -> bool:
        """消耗一次buff（减少持续时间）"""
        if self.duration > 0:
            self.duration -= 1
            return True
        elif self.duration == -1:  # 永久buff
            return True
        return False


@dataclass
class ItemInstance:
    """道具实例"""
    item_name: str
    item_type: str  # consumable, permanent, achievement_reward, special
    quantity: int = 1
    acquired_at: datetime = field(default_factory=datetime.now)
    used_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BuffManager:
    """Buff管理器"""

    def __init__(self):
        self.buffs: Dict[str, List[PlayerBuff]] = {}  # player_id -> buffs

    def add_buff(self, player_id: str, buff: PlayerBuff):
        """为玩家添加buff"""
        if player_id not in self.buffs:
            self.buffs[player_id] = []
        self.buffs[player_id].append(buff)

    def get_buffs(self, player_id: str, buff_type: Optional[BuffType] = None) -> List[PlayerBuff]:
        """获取玩家的buff"""
        if player_id not in self.buffs:
            return []

        player_buffs = self.buffs[player_id]
        if buff_type:
            return [b for b in player_buffs if b.buff_type == buff_type and not b.is_expired()]
        return [b for b in player_buffs if not b.is_expired()]

    def consume_buff(self, player_id: str, buff_type: BuffType) -> Optional[PlayerBuff]:
        """消耗指定类型的buff"""
        buffs = self.get_buffs(player_id, buff_type)
        if buffs:
            buff = buffs[0]
            buff.consume()
            return buff
        return None

    def clear_expired_buffs(self, player_id: str):
        """清除过期的buff"""
        if player_id in self.buffs:
            self.buffs[player_id] = [b for b in self.buffs[player_id] if not b.is_expired()]

    def get_dice_modifier(self, player_id: str) -> int:
        """获取骰子修正值"""
        buffs = self.get_buffs(player_id, BuffType.DICE_MODIFIER)
        return sum(b.value for b in buffs)

    def get_cost_reduction(self, player_id: str) -> int:
        """获取消耗减免值"""
        buffs = self.get_buffs(player_id, BuffType.COST_REDUCTION)
        return sum(b.value for b in buffs)

    def get_shop_discount(self, player_id: str) -> float:
        """获取商店折扣率（返回1.0表示无折扣，0.5表示半价）"""
        buffs = self.get_buffs(player_id, BuffType.SHOP_DISCOUNT)
        if buffs:
            return min(b.value for b in buffs)  # 取最大折扣（最小值）
        return 1.0

    def has_trap_immunity(self, player_id: str) -> bool:
        """检查是否有陷阱免疫"""
        return len(self.get_buffs(player_id, BuffType.TRAP_IMMUNITY)) > 0

    def has_reroll_available(self, player_id: str) -> bool:
        """检查是否可以重骰"""
        return len(self.get_buffs(player_id, BuffType.REROLL_AVAILABLE)) > 0

    def has_retry_turn_available(self, player_id: str) -> bool:
        """检查是否可以重试回合"""
        return len(self.get_buffs(player_id, BuffType.RETRY_TURN_AVAILABLE)) > 0


class ItemEffectExecutor:
    """道具效果执行器"""

    def __init__(self, buff_manager: BuffManager, config: Dict[str, Any]):
        self.buff_manager = buff_manager
        self.config = config
        self.last_used_items: Dict[str, str] = {}  # player_id -> item_name

    def execute_effect(self, player_id: str, item_name: str, choice: Optional[str] = None) -> tuple[bool, str, Dict[str, Any]]:
        """
        执行道具效果

        返回: (成功, 消息, 额外数据)
        """
        item_config = self.config.get("game", {}).get("items", {}).get(item_name)
        if not item_config:
            return False, f"道具 {item_name} 配置不存在", {}

        # 记录最后使用的道具
        self.last_used_items[player_id] = item_name

        # 处理交互式道具
        if item_config.get("interactive") and choice:
            return self._execute_interactive_effect(player_id, item_name, choice, item_config)

        # 处理普通道具效果
        effects = item_config.get("effects", [])
        if not effects:
            return True, "道具已使用，但没有配置效果", {}

        return self._execute_effects(player_id, item_name, effects)

    def _execute_interactive_effect(self, player_id: str, item_name: str, choice: str,
                                   item_config: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
        """执行交互式道具效果"""
        choices = item_config.get("choices", [])

        for choice_config in choices:
            if choice_config["name"] == choice:
                effect_type = choice_config["effect"]
                message = choice_config["message"]

                # 执行效果
                if effect_type == "nothing":
                    return True, message, {}

                elif effect_type == "dice_plus_1":
                    buff = PlayerBuff(
                        buff_type=BuffType.DICE_MODIFIER,
                        value=1,
                        duration=1,
                        source=item_name
                    )
                    self.buff_manager.add_buff(player_id, buff)
                    return True, message, {"buff_added": "dice_plus_1"}

                elif effect_type == "dice_minus_1":
                    buff = PlayerBuff(
                        buff_type=BuffType.DICE_MODIFIER,
                        value=-1,
                        duration=1,
                        source=item_name
                    )
                    self.buff_manager.add_buff(player_id, buff)
                    return True, message, {"buff_added": "dice_minus_1"}

                elif effect_type == "trap_immunity":
                    buff = PlayerBuff(
                        buff_type=BuffType.TRAP_IMMUNITY,
                        value=1,
                        duration=1,
                        source=item_name,
                        metadata={"requires_drawing": True}
                    )
                    self.buff_manager.add_buff(player_id, buff)
                    return True, message, {"buff_added": "trap_immunity"}

                else:
                    return True, f"{message}\n（效果 {effect_type} 待实现）", {}

        return False, f"未找到选项：{choice}", {}

    def _execute_effects(self, player_id: str, item_name: str,
                        effects: List[Dict[str, Any]]) -> tuple[bool, str, Dict[str, Any]]:
        """执行道具效果列表"""
        messages = []
        extra_data = {}

        for effect in effects:
            effect_type = effect.get("type")

            # 随机概率效果
            if "probability" in effect:
                if random.random() > effect["probability"]:
                    continue

            # 根据效果类型执行
            if effect_type == "score":
                score_value = random.randint(effect.get("min", 0), effect.get("max", 0))
                extra_data["score_gain"] = score_value
                messages.append(f"获得 {score_value} 积分！")

            elif effect_type == "nothing":
                messages.append("什么也没发生...")

            elif effect_type == "dice_cost_reduction":
                value = effect.get("value", 2)
                buff = PlayerBuff(
                    buff_type=BuffType.COST_REDUCTION,
                    value=value,
                    duration=-1,  # 永久
                    source=item_name
                )
                self.buff_manager.add_buff(player_id, buff)
                messages.append(effect.get("message", f"掷骰消耗-{value}"))
                extra_data["buff_added"] = "cost_reduction"

            elif effect_type == "shop_discount_50":
                buff = PlayerBuff(
                    buff_type=BuffType.SHOP_DISCOUNT,
                    value=0.5,
                    duration=1,
                    source=item_name
                )
                self.buff_manager.add_buff(player_id, buff)
                messages.append(effect.get("message", "下次购买半价！"))
                extra_data["buff_added"] = "shop_discount_50"

            elif effect_type == "shop_discount_20":
                buff = PlayerBuff(
                    buff_type=BuffType.SHOP_DISCOUNT,
                    value=0.8,
                    duration=1,
                    source=item_name
                )
                self.buff_manager.add_buff(player_id, buff)
                messages.append(effect.get("message", "下次购买8折！"))
                extra_data["buff_added"] = "shop_discount_20"

            elif effect_type == "retry_turn":
                buff = PlayerBuff(
                    buff_type=BuffType.RETRY_TURN_AVAILABLE,
                    value=1,
                    duration=1,
                    source=item_name
                )
                self.buff_manager.add_buff(player_id, buff)
                messages.append(effect.get("message", "可以重试本回合！"))
                extra_data["buff_added"] = "retry_turn"

            elif effect_type == "reroll_3_dice":
                buff = PlayerBuff(
                    buff_type=BuffType.REROLL_AVAILABLE,
                    value=3,
                    duration=1,
                    source=item_name,
                    metadata={"dice_count": 3}
                )
                self.buff_manager.add_buff(player_id, buff)
                messages.append(effect.get("message", "可以重骰3个骰子！"))
                extra_data["buff_added"] = "reroll_3_dice"

            elif effect_type == "refresh_last_item":
                last_item = self.last_used_items.get(player_id)
                if last_item and last_item != item_name:
                    messages.append(f"刷新道具：{last_item}")
                    extra_data["refreshed_item"] = last_item
                else:
                    messages.append("没有可刷新的道具")

            elif effect_type == "random_reward":
                rewards = effect.get("rewards", [])
                reward = self._select_random_reward(rewards)
                if reward:
                    reward_type = reward.get("reward_type")
                    value = reward.get("value")

                    if reward_type == "score":
                        extra_data["score_gain"] = value
                        messages.append(f"获得 {value} 积分！")
                    elif reward_type == "item":
                        extra_data["item_reward"] = value
                        messages.append(f"获得道具：{value}")

            elif effect_type == "reroll_on_condition":
                condition = effect.get("condition")
                buff = PlayerBuff(
                    buff_type=BuffType.REROLL_AVAILABLE,
                    value=1,
                    duration=1,
                    source=item_name,
                    metadata={"condition": condition}
                )
                self.buff_manager.add_buff(player_id, buff)
                messages.append(effect.get("message", "条件重骰已激活"))
                extra_data["buff_added"] = "reroll_condition"

            else:
                messages.append(f"（效果 {effect_type} 待实现）")

        return True, "\n".join(messages) if messages else "道具已使用", extra_data

    def _select_random_reward(self, rewards: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """根据概率选择随机奖励"""
        if not rewards:
            return None

        total_prob = sum(r.get("probability", 0) for r in rewards)
        rand_val = random.random() * total_prob

        cumulative = 0
        for reward in rewards:
            cumulative += reward.get("probability", 0)
            if rand_val <= cumulative:
                return reward

        return rewards[-1]  # 兜底返回最后一个


# 全局buff管理器实例
_global_buff_manager = BuffManager()

def get_buff_manager() -> BuffManager:
    """获取全局buff管理器"""
    return _global_buff_manager
