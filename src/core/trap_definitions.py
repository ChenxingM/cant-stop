"""
完整的陷阱定义 - 基于traps.md中的20个陷阱
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class TrapDef:
    """陷阱定义"""
    id: int
    name: str
    description: str  # 遭遇内容
    effect_description: str  # 触发效果
    achievement: str = ""  # 成就名称
    has_choice: bool = False  # 是否有选择
    choices: List[Dict[str, Any]] = None  # 选择选项

    def __post_init__(self):
        if self.choices is None:
            self.choices = []


# 所有20个陷阱的完整定义
ALL_TRAPS: Dict[int, TrapDef] = {
    1: TrapDef(
        id=1,
        name="小小火球术",
        description="火球砸出的坑洞让你无处下脚。",
        effect_description="停止一回合（消耗一回合积分），并在下回合的掷骰中结果自动变为（4，5，5，5，6，6）。在完成此惩罚前不得主动结束当前轮次。",
        achievement="火球术大师",
    ),

    2: TrapDef(
        id=2,
        name='"不要回头"',
        description="你感到身后一股寒意，当你战战兢兢地转过身试图搞清楚状况时，你发现在看到它脸的那一刻一切都已经晚了……",
        effect_description="清空当前列进度回到上一个永久棋子位置或初始位置",
        achievement="好奇心害死猫",
    ),

    3: TrapDef(
        id=3,
        name="婚戒…？",
        description="象征契约精神的戒指。在你触碰它时，你突然被困在原地无法动弹。",
        effect_description="无契约者：强制暂停该轮次直到你完成此陷阱相关绘制（不计算积分）。有契约者（1期契约者可以未参企）：不受陷阱负面影响，你与你的契约者还均可获得一次免费的回合。",
        achievement="冰冷的心/炽热的心",
        has_choice=True,
        choices=[
            {"type": "no_contract", "effect": "pause_for_drawing", "achievement": "冰冷的心"},
            {"type": "has_contract", "effect": "free_turns", "achievement": "炽热的心"},
        ],
    ),

    4: TrapDef(
        id=4,
        name="白色天○钩",
        description="（远距离出现）随着震动，一个白色的大钢架拔地而起，上面的钩子将你整个拉起，并开始向后移动…",
        effect_description="你在该列当前的进度将无视永久棋子回退两格（若退回到永久棋子前的位置，则当前坐标变为永久棋子新位置）",
        achievement="血祭品",
    ),

    5: TrapDef(
        id=5,
        name="紧闭的大门",
        description=""门不能从这一侧打开" 面对这个突然竖在面前的大门你有些摸不着头脑。",
        effect_description="立即将当前临时标记移动到旁边两列的任意一列的进度上（即清空本轮在该列的进度）。如果当前轮次相邻列均已放置临时标记或登顶，则直接清空本列本轮次进度并在该轮次禁用此临时标记",
        achievement="探索家",
    ),

    6: TrapDef(
        id=6,
        name="奇变偶不变",
        description=""这是什么神秘的暗号吗？"",
        effect_description="下回合投掷结果中奇数>3个：额外获得一个d6骰可以随意加到你得到的两个加值的任意一个中。下回合投掷结果中奇数≤3个：本回合作废（如果该回合触发[失败被动停止]，则惩罚改为下轮次停止一回合）",
        achievement="数学大王/数学0蛋",
        has_choice=True,
    ),

    7: TrapDef(
        id=7,
        name="雷电法王",
        description="一阵强劲的电流从脚底直达你的头顶",
        effect_description="下回合投掷结果的33加值可以得到的数字数量<8种：本回合作废。下回合投掷结果的33加值可以得到的数字数量≥8种：通过检定",
        achievement="哭哭做题家/进去吧你！",
        has_choice=True,
    ),

    8: TrapDef(
        id=8,
        name="中门对狙",
        description="有什么东西挡住了你的去路？哦！是另一个玩家！快快清除阻碍吧～",
        effect_description="任选一位玩家对决，rd6比大小。点数大：+5积分；点数小：停止一回合（消耗一回合积分）；点数相同：无事发生",
        achievement="狙神/尸体/虚晃一枪",
        has_choice=True,
    ),

    9: TrapDef(
        id=9,
        name="传送门",
        description="你捡到一把造型奇异的枪，这是什么？你尝试了一下，随后打开了一道传送门。给我干哪儿来了？这还是国内吗？",
        effect_description="你当前临时标记被传送到地图上的随机一列（rd16）。如该列无永久棋子或已有临时标记，则本轮次作废。如该列有永久棋子且无临时标记，则将临时标记放置在永久棋子向上一格位置",
        achievement="旅行家",
    ),

    10: TrapDef(
        id=10,
        name="刺儿扎扎",
        description=""考验技术的时刻到了"地上突然冒出一排排尖刺…",
        effect_description="投掷d20出目>18：灵巧地规避掉了，获得新鲜三文鱼一条。投掷d20出目≤18：被扎到，丢失20积分",
        achievement="技术大师/新手噩梦",
        has_choice=True,
    ),

    11: TrapDef(
        id=11,
        name="犹豫就会败北",
        description="就在你思考下一步如何决定的时候，你的骰子已经自己丢出去了…",
        effect_description="强制再进行两回合后才能结束该轮次",
        achievement="影逝二度",
    ),

    12: TrapDef(
        id=12,
        name="七色章鱼",
        description="一只闪着七色光芒的章鱼拦住了你的去路。萌萌的一小只看起来很无害，下一秒却卷起你把你丢了出去。",
        effect_description="你该轮次所有列的当前的进度回退一格",
        achievement="悲伤的小画家",
    ),

    13: TrapDef(
        id=13,
        name="中空格子",
        description="脚下的格子竟然是中空的？！！你一脚踩空快速下落，想要抓住边缘爬上来却始终无法成功。",
        effect_description="暂停2回合（消耗2回合积分）",
        achievement="玩家一败涂地",
    ),

    14: TrapDef(
        id=14,
        name="OAS阿卡利亚",
        description="你越玩越觉得这场真人游戏出现了太多奇怪的地方：不符合常理的装置、奇怪的音响、天气突然变化…当你停下来观察这一切的时候，你隔着一个个玻璃屏仿佛看到了若隐若现的，成百上千个摄像头正对着你…你忍不住再次思考这一切，道心破碎。",
        effect_description="积分减1/4",
        achievement="接近的真相",
    ),

    15: TrapDef(
        id=15,
        name="魔女的小屋",
        description=""哎呀...好忙，好忙啊...要是能有人来搭把手就好了..." 厨房中悬浮的厨刀不断处理着各种食材，就像是有隐形的人在操控着一样。透明的厨师似乎察觉到了你的靠近。 "哎呀，有人来了...你能来帮帮忙吗？"",
        effect_description="当然啦，凑上前帮忙：当前纵列的临时标记被清除。拒绝，沉默地离开：下次移动标记时，必须移动该纵列的临时标记，否则清除当前纵列的临时标记",
        achievement="留了一手/冷漠无情",
        has_choice=True,
        choices=[
            {"type": "help", "effect": "clear_temp_marker", "achievement": "留了一手"},
            {"type": "refuse", "effect": "force_move_marker", "achievement": "冷漠无情"},
        ],
    ),

    17: TrapDef(
        id=17,
        name="滴答滴答",
        description="……这是哪里，密室逃亡吗？你掉入了一个古怪的寂静小镇，褪色一般古老的欧式镇子里仅你一人。在作为背景音不断流逝的滴答声中你在镇子里来回奔走，耗费了不知道多少的时间后，终于打开了通往大钟的门。当你爬上了钟楼顶，你只见到了一个发光的瓶子，正细数着你的时间。【你的时间我就收下了（wink）】你只觉得口袋似乎一轻，有什么东西伴随着你流逝的时间一起消失了。",
        effect_description="随机失去一样现有道具（不包含隐藏道具）。若现在未持有道具，则积分-100",
    ),

    18: TrapDef(
        id=18,
        name="非请勿入",
        description="在你踏入小屋的一瞬间，小屋就活过来了……花瓶冒出头发，壁画兀自哭泣，衣帽架搔首弄姿，菜刀咯咯作响……哪里是出去的路？！门毫无意外地锁着，你不得不在小屋里躲藏逃窜直到它们玩腻。",
        effect_description="（现实时间）5d4+4个小时不能进行打卡和游玩",
    ),

    19: TrapDef(
        id=19,
        name="没有空军",
        description="当你回神时已经和一位胡子花白的老人对着膝盖坐在一艘渔船上，他胡子底下掩映的笑意来自于手里紧绷的鱼线。"看她多有劲！"他絮絮叨叨着，而你无法阻止他收起那枚使你的潜意识警铃大作的鱼钩。漆黑的影子迅速抬升在小船底下蔓延开来，与头顶漆黑的天空互相倾轧，你们的小船在其中大小只不过一枚粟米……终于，祂露出了海面。",
        effect_description="你的理智流失，陷入不定性疯狂。失去控制两回合（消耗20积分）并随机倒退一格临时棋子",
    ),

    20: TrapDef(
        id=20,
        name="LUCKY DAY！",
        description="貌似并没有人询问你的意愿，但在你踏入这个黑漆漆的屋子那一瞬间，游戏就将你加入了玩家的行列。昏暗光源下长桌对面的庄家没有多解释什么，将桌上展示的几枚双色弹填进了猎枪弹槽。枪口抬起，接下来，就是赌命的时候了。……剧痛像钩子一样勾住你的脑仁，将你从黑漆漆的梦境里拉出。有什么代替你的脑浆泼洒在了那间屋子里……你已经难以记起具体的过程，但是显然从一开始这个游戏就没有公平可言。",
        effect_description="下回合只投掷四个骰子，并两两分组。在完成此惩罚前不得主动结束当前轮次",
    ),
}


def get_trap_by_id(trap_id: int) -> Optional[TrapDef]:
    """通过ID获取陷阱定义"""
    return ALL_TRAPS.get(trap_id)


def get_trap_by_name(name: str) -> Optional[TrapDef]:
    """通过名称获取陷阱定义"""
    for trap in ALL_TRAPS.values():
        if trap.name == name:
            return trap
    return None


def format_trap_info(trap_id: int) -> str:
    """格式化陷阱信息显示"""
    trap = get_trap_by_id(trap_id)
    if not trap:
        return f"未知陷阱: {trap_id}"

    info = f"🕳️ {trap.name}\n\n"
    info += f"📖 {trap.description}\n\n"
    info += f"⚡ 效果:\n{trap.effect_description}\n\n"

    if trap.achievement:
        info += f"🏆 成就: {trap.achievement}\n"

    if trap.has_choice:
        info += "\n💡 此陷阱需要做出选择！\n"

    return info


class TrapEffectExecutor:
    """陷阱效果执行器"""

    @staticmethod
    def execute_trap_effect(trap_id: int, context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        执行陷阱效果

        Args:
            trap_id: 陷阱ID
            context: 执行上下文(包含玩家信息、游戏状态、选择等)

        Returns:
            (success, message, extra_data)
        """
        trap = get_trap_by_id(trap_id)
        if not trap:
            return False, f"未知陷阱: {trap_id}", {}

        player_id = context.get("player_id")
        choice = context.get("choice")  # 玩家选择（如果有）

        # 根据不同陷阱执行不同效果
        if trap_id == 1:  # 小小火球术
            return TrapEffectExecutor._effect_fireball(context)
        elif trap_id == 2:  # "不要回头"
            return TrapEffectExecutor._effect_dont_look_back(context)
        elif trap_id == 3:  # 婚戒…？
            return TrapEffectExecutor._effect_ring(context)
        elif trap_id == 4:  # 白色天○钩
            return TrapEffectExecutor._effect_white_hook(context)
        elif trap_id == 5:  # 紧闭的大门
            return TrapEffectExecutor._effect_closed_door(context)
        elif trap_id == 6:  # 奇变偶不变
            return TrapEffectExecutor._effect_odd_even(context)
        elif trap_id == 7:  # 雷电法王
            return TrapEffectExecutor._effect_thunder_king(context)
        elif trap_id == 8:  # 中门对狙
            return TrapEffectExecutor._effect_sniper_duel(context)
        elif trap_id == 9:  # 传送门
            return TrapEffectExecutor._effect_portal(context)
        elif trap_id == 10:  # 刺儿扎扎
            return TrapEffectExecutor._effect_spikes(context)
        elif trap_id == 11:  # 犹豫就会败北
            return TrapEffectExecutor._effect_hesitation(context)
        elif trap_id == 12:  # 七色章鱼
            return TrapEffectExecutor._effect_octopus(context)
        elif trap_id == 13:  # 中空格子
            return TrapEffectExecutor._effect_hollow_tile(context)
        elif trap_id == 14:  # OAS阿卡利亚
            return TrapEffectExecutor._effect_oas(context)
        elif trap_id == 15:  # 魔女的小屋
            return TrapEffectExecutor._effect_witch_house(context)
        elif trap_id == 17:  # 滴答滴答
            return TrapEffectExecutor._effect_tick_tock(context)
        elif trap_id == 18:  # 非请勿入
            return TrapEffectExecutor._effect_no_entry(context)
        elif trap_id == 19:  # 没有空军
            return TrapEffectExecutor._effect_no_airforce(context)
        elif trap_id == 20:  # LUCKY DAY！
            return TrapEffectExecutor._effect_lucky_day(context)

        return True, f"陷阱 {trap.name} 已触发（效果待实现）", {}

    @staticmethod
    def _effect_fireball(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """小小火球术效果"""
        return True, "触发小小火球术！停止一回合，下回合骰子结果自动变为（4，5，5，5，6，6）", {
            "pause_turns": 1,
            "forced_dice_next": [4, 5, 5, 5, 6, 6],
            "cannot_end_turn": True,
            "achievement": "火球术大师"
        }

    @staticmethod
    def _effect_dont_look_back(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """"不要回头"效果"""
        return True, "触发"不要回头"！当前列进度清空，回到上一个永久棋子位置或初始位置", {
            "clear_column_progress": True,
            "achievement": "好奇心害死猫"
        }

    @staticmethod
    def _effect_ring(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """婚戒效果"""
        has_contract = context.get("has_contract", False)
        if has_contract:
            return True, "你与契约者获得免费回合！", {
                "free_turns": 2,
                "achievement": "炽热的心"
            }
        else:
            return True, "你被困在原地！需要完成相关绘制才能继续", {
                "pause_for_drawing": True,
                "achievement": "冰冷的心"
            }

    @staticmethod
    def _effect_white_hook(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """白色天○钩效果"""
        return True, "触发白色天○钩！当前列进度回退两格", {
            "retreat": 2,
            "achievement": "血祭品"
        }

    @staticmethod
    def _effect_closed_door(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """紧闭的大门效果"""
        return True, "触发紧闭的大门！需要移动到相邻列", {
            "move_to_adjacent": True,
            "achievement": "探索家"
        }

    @staticmethod
    def _effect_odd_even(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """奇变偶不变效果 - 需要检查下回合骰子结果"""
        return True, "触发奇变偶不变！等待下回合投掷结果...", {
            "check_next_dice": "odd_count",
            "achievement": "数学大王/数学0蛋"
        }

    @staticmethod
    def _effect_thunder_king(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """雷电法王效果"""
        return True, "触发雷电法王！等待下回合投掷结果...", {
            "check_next_dice": "combination_count",
            "achievement": "哭哭做题家/进去吧你！"
        }

    @staticmethod
    def _effect_sniper_duel(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """中门对狙效果"""
        return True, "触发中门对狙！请选择一位玩家进行对决", {
            "requires_choice": "select_player",
            "achievement": "狙神/尸体/虚晃一枪"
        }

    @staticmethod
    def _effect_portal(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """传送门效果"""
        import random
        target_column = random.randint(3, 18)
        return True, f"触发传送门！传送到列{target_column}", {
            "teleport_to_column": target_column,
            "achievement": "旅行家"
        }

    @staticmethod
    def _effect_spikes(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """刺儿扎扎效果"""
        import random
        roll = random.randint(1, 20)
        if roll > 18:
            return True, f"投掷d20结果{roll}！灵巧规避，获得新鲜三文鱼一条", {
                "score_gain": 0,
                "hidden_item": "新鲜三文鱼",
                "achievement": "技术大师"
            }
        else:
            return True, f"投掷d20结果{roll}！被扎到，丢失20积分", {
                "score_loss": 20,
                "achievement": "新手噩梦"
            }

    @staticmethod
    def _effect_hesitation(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """犹豫就会败北效果"""
        return True, "触发犹豫就会败北！强制再进行两回合后才能结束该轮次", {
            "force_turns": 2,
            "achievement": "影逝二度"
        }

    @staticmethod
    def _effect_octopus(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """七色章鱼效果"""
        return True, "触发七色章鱼！该轮次所有列的当前进度回退一格", {
            "retreat_all_columns": 1,
            "achievement": "悲伤的小画家"
        }

    @staticmethod
    def _effect_hollow_tile(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """中空格子效果"""
        return True, "触发中空格子！暂停2回合", {
            "pause_turns": 2,
            "achievement": "玩家一败涂地"
        }

    @staticmethod
    def _effect_oas(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """OAS阿卡利亚效果"""
        current_score = context.get("current_score", 0)
        loss = current_score // 4
        return True, f"触发OAS阿卡利亚！积分减少1/4({loss}积分)", {
            "score_loss": loss,
            "achievement": "接近的真相"
        }

    @staticmethod
    def _effect_witch_house(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """魔女的小屋效果"""
        choice = context.get("choice")
        if choice == "help":
            return True, "你选择帮忙，但被魔女攻击！当前纵列的临时标记被清除", {
                "clear_temp_marker": True,
                "achievement": "留了一手"
            }
        else:
            return True, "你选择拒绝，魔女很生气！下次移动标记时必须移动该纵列的临时标记", {
                "force_move_this_column": True,
                "achievement": "冷漠无情"
            }

    @staticmethod
    def _effect_tick_tock(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """滴答滴答效果"""
        return True, "触发滴答滴答！随机失去一样道具或积分-100", {
            "lose_random_item": True,
            "fallback_score_loss": 100
        }

    @staticmethod
    def _effect_no_entry(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """非请勿入效果"""
        import random
        hours = sum(random.randint(1, 4) for _ in range(5)) + 4
        return True, f"触发非请勿入！{hours}小时内不能进行打卡和游玩", {
            "lockout_hours": hours
        }

    @staticmethod
    def _effect_no_airforce(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """没有空军效果"""
        return True, "触发没有空军！失去控制两回合并随机倒退一格临时棋子", {
            "pause_turns": 2,
            "score_loss": 20,
            "random_retreat": 1
        }

    @staticmethod
    def _effect_lucky_day(context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """LUCKY DAY！效果"""
        return True, "触发LUCKY DAY！下回合只投掷四个骰子并两两分组", {
            "forced_dice_count_next": 4,
            "forced_grouping": "2-2",
            "cannot_end_turn": True
        }
