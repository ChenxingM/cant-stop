"""
完整的道具定义 - 基于items.md中的24个道具
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ItemFaction(Enum):
    """道具阵营限制"""
    UNIVERSAL = "通用"
    AE = "ae专用"
    ADOPTER = "收养人专用"


@dataclass
class ItemDef:
    """道具定义"""
    id: int
    name: str
    faction: ItemFaction
    price: int  # 0表示不可买卖
    description: str
    effect: str
    can_trade: bool = True  # 是否可买卖
    limited: int = 0  # 限量数量,0表示无限
    unlock_condition: str = ""  # 解锁条件


# 所有24个道具的完整定义
ALL_ITEMS: Dict[int, ItemDef] = {
    1: ItemDef(
        id=1,
        name="败者○尘",
        faction=ItemFaction.UNIVERSAL,
        price=100,
        description="是游戏就有读档！",
        effect="当你的本回合掷骰没有达到理想效果时，可以清空本回合点数重新投掷（r6d6）。",
    ),

    2: ItemDef(
        id=2,
        name="放飞小○！",
        faction=ItemFaction.UNIVERSAL,
        price=200,
        description="飞起来孩子飞起来",
        effect="将你离终点最远的临时标记向前移动两格。",
    ),

    3: ItemDef(
        id=3,
        name="花言巧语",
        faction=ItemFaction.UNIVERSAL,
        price=150,
        description="封锁道路的窗子。",
        effect="你可以选择一个玩家强制其下一轮不能再次在其当前轮次的列上行进。该玩家可以进行一个d6投掷，如果出目为6则抵消该次惩罚。",
    ),

    4: ItemDef(
        id=4,
        name="揍击派对",
        faction=ItemFaction.UNIVERSAL,
        price=0,
        description="你在地图随机一个坐标召唤疯狂大摆锤",
        effect="在地图随机一个坐标（rd列→rd行）召唤疯狂大摆锤，当前在这个坐标上的所有临时标记和永久棋子倒退一格。",
        can_trade=False,
    ),

    5: ItemDef(
        id=5,
        name="沉重的巨剑",
        faction=ItemFaction.AE,
        price=50,
        description="足以劈开骰子的大剑。",
        effect="若你的任意掷骰掷出1，则可以选择重掷一次（.r1d6）。不过哪怕其仍是1，你都必须接受重掷的数值。",
    ),

    6: ItemDef(
        id=6,
        name="女巫的魔法伎俩",
        faction=ItemFaction.ADOPTER,
        price=50,
        description="悄悄更换花纹的小魔法。",
        effect="若你的任意掷骰掷出6，则可以选择重掷一次（.r1d6）。不过哪怕其仍是6，你都必须接受重掷的数值。",
    ),

    7: ItemDef(
        id=7,
        name="变大蘑菇",
        faction=ItemFaction.AE,
        price=50,
        description="一个神秘的红帽子胡子大叔给你送来了一块鲜艳的蘑菇碎片。",
        effect="选择：吃(下次投掷所有结果+1) 或 不吃(无事发生)",
    ),

    8: ItemDef(
        id=8,
        name="中门对狙",
        faction=ItemFaction.UNIVERSAL,
        price=0,
        description="道具版中门对狙",
        effect="特殊道具，从地图位置获取",
        can_trade=False,
    ),

    9: ItemDef(
        id=9,
        name="超级大炮",
        faction=ItemFaction.UNIVERSAL,
        price=200,
        description="外型凶猛的超级手持大炮。",
        effect="你可以在任意一回合掷骰前使用，使用后可直接指定需要的出目。",
    ),

    10: ItemDef(
        id=10,
        name=":）",
        faction=ItemFaction.UNIVERSAL,
        price=100,
        description="一颗金色的星星。",
        effect="选择：互动(本次移动的临时标记转换为永久标记且你可以继续进行当前轮次) 或 不互动(无事发生)",
    ),

    11: ItemDef(
        id=11,
        name="闹Ae魔镜",
        faction=ItemFaction.ADOPTER,
        price=50,
        description="一个华丽的欧式圆镜，隐约能看到黑紫色的液体在其间流动。",
        effect="有契约ae：可以在任意一回合掷骰前使用，每消耗10积分可以指定一个出目数值，最多6个。无契约ae：直接+5积分",
    ),

    12: ItemDef(
        id=12,
        name="小女孩娃娃",
        faction=ItemFaction.AE,
        price=100,
        description="一个小女孩模样的娃娃。",
        effect="无契约小女孩：直接+5积分。有契约小女孩：戳戳脸蛋(消耗5积分免疫下个陷阱)/戳戳手(绘制免疫下个陷阱)/拽拽腿(有点疼疼的)",
    ),

    13: ItemDef(
        id=13,
        name="火堆",
        faction=ItemFaction.UNIVERSAL,
        price=0,
        description="令人安心的温暖火堆，上面插着一根铁签似乎还可以烧烤。",
        effect="使用后可以刷新上一个已使用道具的效果。",
        can_trade=False,
    ),

    14: ItemDef(
        id=14,
        name="阈限空间",
        faction=ItemFaction.UNIVERSAL,
        price=100,
        description="你踏入一片空旷寂静的空白。你感受不到时间的存在。",
        effect="当你进行的轮次触发失败被动结束后，可以使用此道具重新进行上一回合。（若结果仍然触发失败被动结束，则不可再重投）",
    ),

    15: ItemDef(
        id=15,
        name="一斤鸭梨！",
        faction=ItemFaction.UNIVERSAL,
        price=50,
        description="怎么运气又这么差……将思路逆转一下，不是你的运气出了问题，而是系统出了问题！",
        effect="当你的本回合掷骰没有达到理想效果时，任选3个出目重新投掷。",
    ),

    16: ItemDef(
        id=16,
        name="The Room",
        faction=ItemFaction.UNIVERSAL,
        price=0,
        description="一处可原地展开的虚拟密闭空间，只有一次探索机会。",
        effect="探索位置：桌子-抽屉/摆件/连接处，放映机-把手/胶卷/架子，柜子-隔断/柜门/顶端，地板-地砖/墙角/地毯。正确答案：桌子-连接处。奖励：可选择直接在道具所在列登顶。",
        can_trade=False,
    ),

    17: ItemDef(
        id=17,
        name="我的地图",
        faction=ItemFaction.UNIVERSAL,
        price=500,
        description="一个dlc操作界面。地图组件竟然可以自己设置了？！",
        effect="在获得道具后首次触发的陷阱可使用。使用后，你可以免疫该陷阱并临时将该陷阱移动到地图任意位置。",
    ),

    18: ItemDef(
        id=18,
        name="五彩宝石",
        faction=ItemFaction.UNIVERSAL,
        price=200,
        description="6枚蕴含着强大力量的宝石。",
        effect="投掷6d6出目>9：全场随机一半玩家积分-10。出目≤9：你的积分-50",
    ),

    19: ItemDef(
        id=19,
        name="购物卡",
        faction=ItemFaction.UNIVERSAL,
        price=0,
        description="实际上你只是拿了就走",
        effect="商店任一物品可半价购入。",
        can_trade=False,
    ),

    20: ItemDef(
        id=20,
        name="Biango Meow",
        faction=ItemFaction.UNIVERSAL,
        price=100,
        description="投了这么多骰子，手酸了吧，这是给你的奖励～",
        effect="随机奖励：30积分 / 道具卡：The Room / 道具卡：阈限空间 / 道具卡：:）",
        limited=5,
        unlock_condition="累计投满100个骰子后解锁",
    ),

    21: ItemDef(
        id=21,
        name="黑喵",
        faction=ItemFaction.UNIVERSAL,
        price=100,
        description="喵向你走来…等等，它什么时候变成全身黑色了？",
        effect="你之后的所有回合所需要消耗的积分-2。",
        limited=2,
    ),

    22: ItemDef(
        id=22,
        name="火人雕像",
        faction=ItemFaction.AE,
        price=0,
        description="据报道，在古老的神庙之中，OAS协会的探险队发现了两个小小的雕像...",
        effect="在你还未抵达的地图版块上随机生成一枚红色宝石(+100积分)和一块蓝色池沼(-10积分并使红色宝石消失)。可联系管理员知晓使用冰人雕像的玩家的红色池沼位置。",
        can_trade=False,
    ),

    23: ItemDef(
        id=23,
        name="冰人雕像",
        faction=ItemFaction.ADOPTER,
        price=0,
        description="据报道，在古老的神庙之中，OAS协会的探险队发现了两个小小的雕像...",
        effect="在你还未抵达的地图版块上随机生成一枚蓝色宝石(+100积分)和一块红色池沼(-10积分并使蓝色宝石消失)。可联系管理员知晓使用火人雕像的玩家的蓝色池沼位置。",
        can_trade=False,
    ),

    24: ItemDef(
        id=24,
        name="灵魂之叶",
        faction=ItemFaction.UNIVERSAL,
        price=100,
        description="你登上一艘巨大的船。在宁静的氛围里为乘客忙碌，最后收到了灵魂的赠礼。",
        effect="你可选择一个永久棋子，向前移动一格。",
    ),
}


def get_item_by_id(item_id: int) -> Optional[ItemDef]:
    """通过ID获取道具定义"""
    return ALL_ITEMS.get(item_id)


def get_item_by_name(name: str) -> Optional[ItemDef]:
    """通过名称获取道具定义"""
    # 移除可能的后缀
    clean_name = name.replace("（通用）", "").replace("（ae专用）", "").replace("（收养人专用）", "").strip()

    for item in ALL_ITEMS.values():
        if item.name == clean_name or item.name == name:
            return item
    return None


def get_shop_items(faction: str) -> List[ItemDef]:
    """获取商店中可购买的道具"""
    result = []
    for item in ALL_ITEMS.values():
        # 只显示可交易且有价格的道具
        if item.can_trade and item.price > 0:
            # 检查阵营限制
            if item.faction == ItemFaction.AE and faction != "Aeonreth":
                continue
            if item.faction == ItemFaction.ADOPTER and faction != "收养人":
                continue
            result.append(item)
    return result


def format_shop_display(faction: str) -> str:
    """格式化商店显示"""
    shop_items = get_shop_items(faction)

    display = "🏪 道具商店\n\n"
    display += "━━━━━━━━━━━━━━━━━━\n\n"

    # 按阵营分组
    universal = [i for i in shop_items if i.faction == ItemFaction.UNIVERSAL]
    faction_items = [i for i in shop_items if i.faction != ItemFaction.UNIVERSAL]

    if universal:
        display += "📦 通用道具:\n\n"
        for item in sorted(universal, key=lambda x: x.price):
            display += f"🔹 {item.name} - {item.price}积分\n"
            display += f"   📝 {item.description}\n"
            if item.limited > 0:
                display += f"   ⚠️ 限量: {item.limited}个\n"
            if item.unlock_condition:
                display += f"   🔓 {item.unlock_condition}\n"
            display += f"   ⚡ {item.effect}\n\n"

    if faction_items:
        display += "━━━━━━━━━━━━━━━━━━\n\n"
        display += f"🎯 {faction}专属道具:\n\n"
        for item in sorted(faction_items, key=lambda x: x.price):
            display += f"🔸 {item.name} - {item.price}积分\n"
            display += f"   📝 {item.description}\n"
            display += f"   ⚡ {item.effect}\n\n"

    display += "━━━━━━━━━━━━━━━━━━\n"
    display += "💡 使用: 购买道具 <道具名称>\n"
    display += "💡 出售: 出售道具 <道具名称> (半价)\n"

    return display
