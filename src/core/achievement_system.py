"""
成就系统
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class AchievementCategory(Enum):
    """成就分类"""
    UNLUCKY = "倒霉类"
    CHALLENGE = "挑战类"
    COLLECTION = "收集类"
    SPECIAL = "特殊类"


@dataclass
class Achievement:
    """成就数据结构"""
    id: str
    name: str
    description: str
    category: AchievementCategory
    reward_description: str
    unlock_condition: str
    is_unlocked: bool = False
    unlock_date: Optional[str] = None


class AchievementSystem:
    """成就系统"""

    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self._init_achievements()

    def _init_achievements(self):
        """初始化所有成就"""
        # 倒霉类成就
        self.achievements["territory_awareness"] = Achievement(
            id="territory_awareness",
            name="🏠 领地意识",
            description="回家吧孩子回家吧\n恭喜？您已在当前列回家三次，太倒霉啦！",
            category=AchievementCategory.UNLUCKY,
            reward_description="修改液 - 下一次掷骰可以将结果直接改变成上一轮行进竖列的任意两个数字",
            unlock_condition="在当前列回家三次"
        )

        self.achievements["bad_luck_day"] = Achievement(
            id="bad_luck_day",
            name="📅 出门没看黄历",
            description="人总不能一直倒霉吧\n恭喜？您已遭遇三次首达陷阱，太倒霉啦！",
            category=AchievementCategory.UNLUCKY,
            reward_description="风水罗盘 - 下一次掷骰可以将任意一个数值的临时标记移动两格",
            unlock_condition="遭遇三次首达陷阱"
        )

        self.achievements["self_cruise"] = Achievement(
            id="self_cruise",
            name="🎯 自巡航",
            description="自巡航导弹但是是自己的自\n恭喜？您在使用道具的时候触发陷阱/自己触发惩罚，太倒霉啦！",
            category=AchievementCategory.UNLUCKY,
            reward_description="婴儿般的睡眠 - 下一回合免费",
            unlock_condition="使用道具时触发陷阱/自己触发惩罚"
        )

        # 挑战类成就
        self.achievements["one_turn_complete"] = Achievement(
            id="one_turn_complete",
            name="⚡ 看我一命通关！",
            description="真正的赌狗无惧挑战！\n恭喜您在一轮次内从起点到达列终点",
            category=AchievementCategory.CHALLENGE,
            reward_description="奇妙的变身器 - 特殊道具，具体效果待解锁后发现",
            unlock_condition="在一轮次内从起点到达列终点"
        )

        self.achievements["peaceful_life"] = Achievement(
            id="peaceful_life",
            name="🎭 平平淡淡才是真",
            description="啊？还有这事？\n恭喜您在遭遇中三次选择结果均无事发生",
            category=AchievementCategory.CHALLENGE,
            reward_description="老头款大背心 - 纪念品道具",
            unlock_condition="在遭遇中三次选择结果均无事发生"
        )

        self.achievements["karma"] = Achievement(
            id="karma",
            name="🎲 善恶有报",
            description="怪我吗？\n恭喜您在遭遇中三次选择结果均触发特殊效果",
            category=AchievementCategory.CHALLENGE,
            reward_description="游戏机打折券 - 商店相关优惠道具",
            unlock_condition="在遭遇中三次选择结果均触发特殊效果"
        )

        # 收集类成就
        self.achievements["collector"] = Achievement(
            id="collector",
            name="📦 收集癖",
            description="不拿全浑身难受啊\n恭喜您解锁全部地图及道具",
            category=AchievementCategory.COLLECTION,
            reward_description="协会的赞助奖金 - 大量积分奖励",
            unlock_condition="解锁全部地图及道具"
        )

        # 特殊成就
        self.achievements["fire_master"] = Achievement(
            id="fire_master",
            name="🔥 火球术大师",
            description="体验魔法的不稳定性",
            category=AchievementCategory.SPECIAL,
            reward_description="火球术经验 - 特殊称号",
            unlock_condition="触发小小火球术陷阱"
        )

        self.achievements["curiosity_killed_cat"] = Achievement(
            id="curiosity_killed_cat",
            name="🐈 好奇心害死猫",
            description="有些真相不该被知道",
            category=AchievementCategory.SPECIAL,
            reward_description="神秘经验 - 特殊称号",
            unlock_condition="触发不要回头陷阱"
        )

    def get_all_achievements(self) -> List[Achievement]:
        """获取所有成就"""
        return list(self.achievements.values())

    def get_unlocked_achievements(self) -> List[Achievement]:
        """获取已解锁成就"""
        return [a for a in self.achievements.values() if a.is_unlocked]

    def get_locked_achievements(self) -> List[Achievement]:
        """获取未解锁成就"""
        return [a for a in self.achievements.values() if not a.is_unlocked]

    def unlock_achievement(self, achievement_id: str, unlock_date: str = None) -> bool:
        """解锁成就"""
        if achievement_id in self.achievements:
            self.achievements[achievement_id].is_unlocked = True
            self.achievements[achievement_id].unlock_date = unlock_date
            return True
        return False

    def check_achievement_unlocked(self, achievement_id: str) -> bool:
        """检查成就是否已解锁"""
        return self.achievements.get(achievement_id, Achievement("", "", "", AchievementCategory.SPECIAL, "", "")).is_unlocked

    def get_achievement_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """按分类获取成就"""
        return [a for a in self.achievements.values() if a.category == category]