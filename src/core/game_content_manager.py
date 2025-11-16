"""
游戏内容管理器 - 整合陷阱、道具、遭遇系统
"""

from typing import Dict, List, Optional, Tuple, Any
from .fixed_map_config import FixedMapConfigLoader, MapElementType
from .item_definitions import (
    get_item_by_id, get_item_by_name, get_shop_items,
    format_shop_display, ItemDef, ItemFaction
)
from .trap_definitions import (
    get_trap_by_id, get_trap_by_name, format_trap_info,
    TrapDef, TrapEffectExecutor
)
from .encounter_definitions import (
    get_encounter_by_id, get_encounter_by_name, format_encounter_info,
    EncounterDef, EncounterEffectExecutor
)
from ..models.game_models import Faction


class GameContentManager:
    """游戏内容管理器 - 统一管理陷阱、道具、遭遇"""

    def __init__(self):
        self.map_config = FixedMapConfigLoader()
        self.trap_executor = TrapEffectExecutor()
        self.encounter_executor = EncounterEffectExecutor()

    # ==================== 地图元素查询 ====================

    def get_element_at_position(self, column: int, position: int) -> Optional[Dict[str, Any]]:
        """
        获取指定位置的地图元素

        Returns:
            {
                'type': 'trap' | 'item' | 'encounter',
                'id': int,
                'name': str,
                'data': 详细数据
            }
        """
        element = self.map_config.get_element_at_position(column, position)
        if not element:
            return None

        result = {
            'type': element.element_type.value,
            'id': element.element_id,
            'name': element.name,
            'column': element.column,
            'position': element.position
        }

        # 获取详细数据
        if element.element_type == MapElementType.TRAP:
            trap_def = get_trap_by_id(element.element_id)
            result['data'] = trap_def if trap_def else None
        elif element.element_type == MapElementType.ITEM:
            item_def = get_item_by_id(element.element_id)
            result['data'] = item_def if item_def else None
        elif element.element_type == MapElementType.ENCOUNTER:
            encounter_def = get_encounter_by_id(element.element_id)
            result['data'] = encounter_def if encounter_def else None

        return result

    def check_position_has_element(self, column: int, position: int) -> bool:
        """检查指定位置是否有元素"""
        return self.map_config.get_element_at_position(column, position) is not None

    # ==================== 陷阱处理 ====================

    def trigger_trap(
        self,
        trap_id: int,
        player_id: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        触发陷阱

        Args:
            trap_id: 陷阱ID
            player_id: 玩家ID
            context: 上下文信息

        Returns:
            (success, message, extra_data)
        """
        trap = get_trap_by_id(trap_id)
        if not trap:
            return False, f"未知陷阱ID: {trap_id}", {}

        # 添加玩家ID到上下文
        context['player_id'] = player_id

        # 执行陷阱效果
        success, message, extra_data = self.trap_executor.execute_trap_effect(trap_id, context)

        # 添加陷阱信息到extra_data
        extra_data['trap_name'] = trap.name
        extra_data['trap_id'] = trap_id
        if trap.achievement:
            extra_data['achievement'] = trap.achievement

        return success, message, extra_data

    def get_trap_info(self, trap_id: int) -> str:
        """获取陷阱信息"""
        return format_trap_info(trap_id)

    # ==================== 道具处理 ====================

    def get_item_info(self, item_id: int) -> Optional[ItemDef]:
        """获取道具信息"""
        return get_item_by_id(item_id)

    def get_item_by_name_fuzzy(self, name: str) -> Optional[ItemDef]:
        """通过名称模糊查找道具"""
        return get_item_by_name(name)

    def get_shop_display(self, faction: str) -> str:
        """获取商店显示内容"""
        return format_shop_display(faction)

    def can_buy_item(
        self,
        item_id: int,
        player_score: int,
        player_faction: str,
        player_inventory: List[str]
    ) -> Tuple[bool, str]:
        """
        检查是否可以购买道具

        Returns:
            (can_buy, reason)
        """
        item = get_item_by_id(item_id)
        if not item:
            return False, "道具不存在"

        if not item.can_trade:
            return False, "该道具不可购买"

        if item.price == 0:
            return False, "该道具不可购买"

        # 检查阵营限制
        if item.faction == ItemFaction.AE and player_faction != "Aeonreth":
            return False, "该道具仅限Aeonreth阵营使用"

        if item.faction == ItemFaction.ADOPTER and player_faction != "收养人":
            return False, "该道具仅限收养人阵营使用"

        # 检查是否已拥有(某些道具只能拥有一次)
        if item.name in player_inventory:
            # 检查是否是消耗品
            if item.name in ["败者○尘", "放飞小○！", "花言巧语", "超级大炮"]:
                # 消耗品可以多次购买
                pass
            else:
                # 永久道具只能购买一次
                if item.name in ["沉重的巨剑", "女巫的魔法伎俩", "黑喵"]:
                    return False, "你已经拥有该道具"

        # 检查积分
        if player_score < item.price:
            return False, f"积分不足，需要{item.price}积分"

        # 检查限量
        if item.limited > 0:
            # 这里需要查询数据库检查全局购买数量
            # 暂时简化处理
            pass

        return True, "可以购买"

    def calculate_buy_price(
        self,
        item_id: int,
        has_discount: bool = False,
        discount_rate: float = 1.0
    ) -> int:
        """
        计算购买价格

        Args:
            item_id: 道具ID
            has_discount: 是否有折扣
            discount_rate: 折扣率(0.5=半价, 0.8=8折)

        Returns:
            实际价格
        """
        item = get_item_by_id(item_id)
        if not item:
            return 0

        base_price = item.price
        if has_discount:
            return int(base_price * discount_rate)

        return base_price

    def calculate_sell_price(self, item_id: int) -> int:
        """计算出售价格(半价)"""
        item = get_item_by_id(item_id)
        if not item or not item.can_trade:
            return 0
        return item.price // 2

    # ==================== 遭遇处理 ====================

    def trigger_encounter(
        self,
        encounter_id: int,
        player_id: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        触发遭遇(显示遭遇内容和选项)

        Returns:
            (success, message, encounter_data)
        """
        encounter = get_encounter_by_id(encounter_id)
        if not encounter:
            return False, f"未知遭遇ID: {encounter_id}", {}

        # 格式化遭遇信息
        message = format_encounter_info(encounter_id)

        # 返回遭遇数据供后续选择使用
        encounter_data = {
            'encounter_id': encounter_id,
            'encounter_name': encounter.name,
            'choices': [
                {
                    'index': i,
                    'name': choice.choice_name,
                    'description': choice.effect_description
                }
                for i, choice in enumerate(encounter.choices)
            ]
        }

        return True, message, encounter_data

    def execute_encounter_choice(
        self,
        encounter_id: int,
        choice_index: int,
        player_id: str,
        context: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        执行遭遇选择

        Args:
            encounter_id: 遭遇ID
            choice_index: 选择索引(从0开始)
            player_id: 玩家ID
            context: 上下文信息

        Returns:
            (success, message, effect_data)
        """
        encounter = get_encounter_by_id(encounter_id)
        if not encounter:
            return False, f"未知遭遇ID: {encounter_id}", {}

        if choice_index < 0 or choice_index >= len(encounter.choices):
            return False, "无效的选择", {}

        # 添加玩家ID到上下文
        context['player_id'] = player_id

        # 执行遭遇效果
        success, message, effect_data = self.encounter_executor.execute_encounter_effect(
            encounter_id,
            choice_index,
            context
        )

        # 添加遭遇信息到effect_data
        choice = encounter.choices[choice_index]
        effect_data['encounter_name'] = encounter.name
        effect_data['encounter_id'] = encounter_id
        effect_data['choice_name'] = choice.choice_name
        if choice.achievement:
            effect_data['achievement'] = choice.achievement

        return success, message, effect_data

    def get_encounter_info(self, encounter_id: int) -> str:
        """获取遭遇信息"""
        return format_encounter_info(encounter_id)

    # ==================== 统计信息 ====================

    def get_map_summary(self) -> str:
        """获取地图摘要"""
        return self.map_config.get_map_summary()

    def get_column_elements(self, column: int) -> List[Dict[str, Any]]:
        """获取指定列的所有元素"""
        elements = self.map_config.get_elements_in_column(column)
        result = []
        for elem in elements:
            result.append({
                'position': elem.position,
                'type': elem.element_type.value,
                'id': elem.element_id,
                'name': elem.name
            })
        return result

    # ==================== 辅助方法 ====================

    def validate_player_context(
        self,
        player_id: str,
        player_faction: str,
        player_score: int,
        has_contract: bool = False
    ) -> Dict[str, Any]:
        """
        构建玩家上下文

        Args:
            player_id: 玩家ID
            player_faction: 玩家阵营
            player_score: 玩家当前积分
            has_contract: 是否有契约对象

        Returns:
            上下文字典
        """
        return {
            'player_id': player_id,
            'faction': player_faction,
            'current_score': player_score,
            'has_contract': has_contract
        }


# 全局实例
_content_manager = None


def get_content_manager() -> GameContentManager:
    """获取全局游戏内容管理器实例"""
    global _content_manager
    if _content_manager is None:
        _content_manager = GameContentManager()
    return _content_manager
