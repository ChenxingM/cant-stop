"""
成就管理器 - 向后兼容的成就系统包装器
"""

from typing import List, Optional
from .achievement_system import AchievementSystem, Achievement
from .enhanced_achievement_system import EnhancedAchievementSystem


class AchievementManager:
    """成就管理器 - 提供向后兼容的接口"""

    def __init__(self, use_enhanced_system: bool = True):
        self.use_enhanced = use_enhanced_system

        if use_enhanced_system:
            # 使用增强的成就系统
            self.system = EnhancedAchievementSystem()
        else:
            # 使用原有的成就系统
            self.system = AchievementSystem()

    def get_all_achievements(self) -> List[Achievement]:
        """获取所有成就（向后兼容）"""
        return self.system.get_all_achievements()

    def get_unlocked_achievements(self) -> List[Achievement]:
        """获取已解锁成就（向后兼容）"""
        return self.system.get_unlocked_achievements()

    def get_locked_achievements(self) -> List[Achievement]:
        """获取未解锁成就（向后兼容）"""
        return self.system.get_locked_achievements()

    def unlock_achievement(self, achievement_id: str, unlock_date: str = None) -> bool:
        """解锁成就（向后兼容）"""
        return self.system.unlock_achievement(achievement_id, unlock_date)

    def check_achievement_unlocked(self, achievement_id: str) -> bool:
        """检查成就是否已解锁（向后兼容）"""
        return self.system.check_achievement_unlocked(achievement_id)

    def get_achievement_by_category(self, category):
        """按分类获取成就（向后兼容）"""
        return self.system.get_achievement_by_category(category)

    # 增强功能（仅在使用增强系统时可用）
    def add_achievement_from_config(self, achievement_id: str, achievement_data: dict) -> bool:
        """从配置添加新成就"""
        if hasattr(self.system, 'add_achievement_from_config'):
            return self.system.add_achievement_from_config(achievement_id, achievement_data)
        return False

    def save_achievement_to_config(self, achievement_id: str, achievement_data: dict) -> bool:
        """保存成就到配置文件"""
        if hasattr(self.system, 'save_achievement_to_config'):
            return self.system.save_achievement_to_config(achievement_id, achievement_data)
        return False

    def get_player_progress(self, player_id: str) -> dict:
        """获取玩家成就进度"""
        if hasattr(self.system, 'get_player_progress'):
            return self.system.get_player_progress(player_id)
        return {}

    def is_enhanced_system(self) -> bool:
        """检查是否使用增强系统"""
        return self.use_enhanced