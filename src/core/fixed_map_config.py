"""
固定地图配置系统 - 从陷阱道具遭遇配置.md加载固定的地图布局
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MapElementType(Enum):
    """地图元素类型"""
    TRAP = "陷阱"
    ITEM = "道具"
    ENCOUNTER = "遭遇"


@dataclass
class MapElement:
    """地图元素"""
    element_type: MapElementType
    element_id: int  # 编号
    name: str
    column: int
    position: int

    def get_key(self) -> str:
        """获取位置键"""
        return f"{self.column}_{self.position}"


class FixedMapConfigLoader:
    """固定地图配置加载器"""

    def __init__(self):
        self.map_elements: Dict[str, MapElement] = {}
        self._load_fixed_config()

    def _load_fixed_config(self):
        """加载固定配置 - 根据陷阱道具遭遇配置.md"""

        # 固定配置数据 - 从陷阱道具遭遇配置.md转换而来
        fixed_layout = {
            # 列 3
            3: [
                (1, MapElementType.ENCOUNTER, 3, "河…土地神"),
                (2, MapElementType.ITEM, 10, ":）（通用）"),
                (3, MapElementType.TRAP, 13, "中空格子"),
            ],
            # 列 4
            4: [
                (1, MapElementType.ENCOUNTER, 5, "小花"),
                (2, MapElementType.ITEM, 16, "The Room（通用）"),
                (3, MapElementType.TRAP, 14, "OAS阿卡利亚"),
                (4, MapElementType.ENCOUNTER, 57, "初次见面"),
            ],
            # 列 5
            5: [
                (1, MapElementType.ENCOUNTER, 7, "多多益善~"),
                (2, MapElementType.TRAP, 19, "没有空军"),
                (3, MapElementType.ITEM, 8, "中门对狙"),
                (4, MapElementType.ENCOUNTER, 23, '"bika"'),
                (5, MapElementType.ENCOUNTER, 45, "AeAe少女"),
            ],
            # 列 6
            6: [
                (1, MapElementType.ENCOUNTER, 8, "一些手"),
                (2, MapElementType.ENCOUNTER, 26, "嘴"),
                (3, MapElementType.TRAP, 1, "小小火球术"),
                (4, MapElementType.ITEM, 17, "我的地图（通用）"),
                (5, MapElementType.ENCOUNTER, 36, "清理大师"),
                (6, MapElementType.ENCOUNTER, 58, "冥府之路"),
            ],
            # 列 7
            7: [
                (1, MapElementType.ENCOUNTER, 19, "自助问答"),
                (2, MapElementType.ENCOUNTER, 43, "节奏大师"),
                (3, MapElementType.ENCOUNTER, 15, "豆腐脑"),
                (4, MapElementType.TRAP, 3, "婚戒…？"),
                (5, MapElementType.ITEM, 1, "败者○尘（通用）"),
                (6, MapElementType.ITEM, 22, "火人雕像（ae专用）"),
                (7, MapElementType.ENCOUNTER, 52, "循环往复"),
            ],
            # 列 8
            8: [
                (1, MapElementType.ITEM, 15, "一斤鸭梨！（通用）"),
                (2, MapElementType.ENCOUNTER, 22, "人才市场？"),
                (3, MapElementType.ENCOUNTER, 10, "突击检查！"),
                (4, MapElementType.TRAP, 18, "非请勿入"),
                (5, MapElementType.ITEM, 4, "揍击派对（通用）"),
                (6, MapElementType.ENCOUNTER, 25, "房产中介"),
                (7, MapElementType.ENCOUNTER, 37, "饥寒交迫"),
                (8, MapElementType.ENCOUNTER, 56, "真实的经历"),
            ],
            # 列 9
            9: [
                (1, MapElementType.ENCOUNTER, 38, "法庭"),
                (2, MapElementType.ITEM, 11, "闹Ae魔镜（收养人专用）"),
                (3, MapElementType.ENCOUNTER, 18, "积木"),
                (4, MapElementType.ENCOUNTER, 16, "神奇小药丸"),
                (5, MapElementType.ENCOUNTER, 21, "葡萄蔷薇紫苑"),
                (6, MapElementType.ENCOUNTER, 53, "回廊"),
                (7, MapElementType.TRAP, 9, "传送门"),
                (8, MapElementType.ITEM, 20, "Biango Meow （通用）"),
                (9, MapElementType.TRAP, 17, "滴答滴答"),
            ],
            # 列 10
            10: [
                (1, MapElementType.ENCOUNTER, 48, "故事书"),
                (2, MapElementType.ENCOUNTER, 30, "💃💃💃"),
                (3, MapElementType.ITEM, 5, "沉重的巨剑（ae专用）"),
                (4, MapElementType.TRAP, 8, "中门对狙"),
                (5, MapElementType.ENCOUNTER, 1, "喵"),
                (6, MapElementType.ITEM, 9, "超级大炮（通用）"),
                (7, MapElementType.TRAP, 4, "白色天○钩"),
                (8, MapElementType.ENCOUNTER, 33, "骰之歌"),
                (9, MapElementType.ENCOUNTER, 50, "身影"),
                (10, MapElementType.ENCOUNTER, 46, "咦？！来真的？！"),
            ],
            # 列 11
            11: [
                (1, MapElementType.ENCOUNTER, 39, "谁要走？！"),
                (2, MapElementType.TRAP, 11, "犹豫就会败北"),
                (3, MapElementType.ITEM, 6, "女巫的魔法伎俩（收养人专用）"),
                (4, MapElementType.ENCOUNTER, 44, "解约厨房"),
                (5, MapElementType.ENCOUNTER, 20, "恭喜你"),
                (6, MapElementType.TRAP, 2, '"不要回头"'),
                (7, MapElementType.ENCOUNTER, 51, "这就是狂野！"),
                (8, MapElementType.ENCOUNTER, 59, "名字"),
                (9, MapElementType.ENCOUNTER, 4, "财神福利"),
                (10, MapElementType.ITEM, 18, "五彩宝石（通用）"),
            ],
            # 列 12
            12: [
                (1, MapElementType.ENCOUNTER, 55, "欢迎参观美术展"),
                (2, MapElementType.ENCOUNTER, 14, "那么，代价是什么？"),
                (3, MapElementType.ENCOUNTER, 35, "面具"),
                (4, MapElementType.TRAP, 5, "紧闭的大门"),
                (5, MapElementType.ITEM, 2, "放飞小○！（通用）"),
                (6, MapElementType.ENCOUNTER, 31, "双人成列"),
                (7, MapElementType.TRAP, 15, "魔女的小屋"),
                (8, MapElementType.ENCOUNTER, 49, "一千零一"),
                (9, MapElementType.ITEM, 24, "灵魂之叶"),
            ],
            # 列 13
            13: [
                (1, MapElementType.ENCOUNTER, 27, "奇异的菜肴"),
                (2, MapElementType.ENCOUNTER, 9, "螂的诱惑"),
                (3, MapElementType.ENCOUNTER, 34, "⚠️警报⚠️"),
                (4, MapElementType.TRAP, 6, "奇变偶不变"),
                (5, MapElementType.ENCOUNTER, 24, "保护好你的脑子！"),
                (6, MapElementType.ITEM, 3, "花言巧语（通用）"),
                (7, MapElementType.ENCOUNTER, 54, "天下无程序员"),
                (8, MapElementType.ITEM, 23, "冰人雕像（收养人专用）"),
            ],
            # 列 14
            14: [
                (1, MapElementType.ENCOUNTER, 40, "黄金薯片"),
                (2, MapElementType.ITEM, 12, "小女孩娃娃（ae专用）"),
                (3, MapElementType.TRAP, 7, "雷电法王"),
                (4, MapElementType.ENCOUNTER, 32, "广场舞"),
                (5, MapElementType.ENCOUNTER, 12, "信仰之跃"),
                (6, MapElementType.ITEM, 21, "黑喵 （通用）"),
                (7, MapElementType.ENCOUNTER, 60, "浓雾之中"),
            ],
            # 列 15
            15: [
                (1, MapElementType.ENCOUNTER, 41, "我吗？"),
                (2, MapElementType.ENCOUNTER, 6, "一位绅士"),
                (3, MapElementType.TRAP, 12, "七色章鱼"),
                (4, MapElementType.ENCOUNTER, 11, "大撒币！"),
                (5, MapElementType.ITEM, 14, "阈限空间（通用）"),
                (6, MapElementType.ENCOUNTER, 47, "魔女的藏书室"),
            ],
            # 列 16
            16: [
                (1, MapElementType.ENCOUNTER, 28, "钓鱼大赛"),
                (2, MapElementType.ENCOUNTER, 13, "卡布奇诺"),
                (3, MapElementType.ITEM, 7, "变大蘑菇（ae专用）"),
                (4, MapElementType.TRAP, 20, "LUCKY DAY！"),
                (5, MapElementType.ENCOUNTER, 42, "新衣服"),
            ],
            # 列 17
            17: [
                (1, MapElementType.ENCOUNTER, 17, "造大桥？"),
                (2, MapElementType.ENCOUNTER, 29, "冷笑话"),
                (3, MapElementType.TRAP, 17, "滴答滴答"),
                (4, MapElementType.ITEM, 19, "购物卡（通用）"),
            ],
            # 列 18
            18: [
                (1, MapElementType.ENCOUNTER, 2, "梦"),
                (2, MapElementType.ITEM, 13, "火堆（通用）"),
                (3, MapElementType.TRAP, 10, "刺儿扎扎"),
            ],
        }

        # 加载到字典中
        for column, elements in fixed_layout.items():
            for position, element_type, element_id, name in elements:
                element = MapElement(
                    element_type=element_type,
                    element_id=element_id,
                    name=name,
                    column=column,
                    position=position
                )
                self.map_elements[element.get_key()] = element

    def get_element_at_position(self, column: int, position: int) -> Optional[MapElement]:
        """获取指定位置的地图元素"""
        key = f"{column}_{position}"
        return self.map_elements.get(key)

    def get_elements_by_type(self, element_type: MapElementType) -> List[MapElement]:
        """获取指定类型的所有元素"""
        return [elem for elem in self.map_elements.values() if elem.element_type == element_type]

    def get_elements_in_column(self, column: int) -> List[MapElement]:
        """获取指定列的所有元素"""
        elements = [elem for elem in self.map_elements.values() if elem.column == column]
        return sorted(elements, key=lambda x: x.position)

    def get_all_traps(self) -> Dict[str, MapElement]:
        """获取所有陷阱位置"""
        return {key: elem for key, elem in self.map_elements.items()
                if elem.element_type == MapElementType.TRAP}

    def get_all_items(self) -> Dict[str, MapElement]:
        """获取所有道具位置"""
        return {key: elem for key, elem in self.map_elements.items()
                if elem.element_type == MapElementType.ITEM}

    def get_all_encounters(self) -> Dict[str, MapElement]:
        """获取所有遭遇位置"""
        return {key: elem for key, elem in self.map_elements.items()
                if elem.element_type == MapElementType.ENCOUNTER}

    def get_map_summary(self) -> str:
        """获取地图摘要信息"""
        trap_count = len(self.get_all_traps())
        item_count = len(self.get_all_items())
        encounter_count = len(self.get_all_encounters())

        summary = "📍 固定地图配置摘要:\n\n"
        summary += f"🕳️ 陷阱数量: {trap_count}\n"
        summary += f"📦 道具数量: {item_count}\n"
        summary += f"🎭 遭遇数量: {encounter_count}\n"
        summary += f"📊 总计: {trap_count + item_count + encounter_count}\n"

        return summary
