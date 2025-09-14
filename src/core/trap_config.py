"""
陷阱配置系统 - 允许GM配置陷阱位置
"""

import json
import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from ..core.trap_system import TrapType


@dataclass
class TrapPositionConfig:
    """陷阱位置配置"""
    trap_type: TrapType
    columns: List[int]  # 陷阱可能出现的列
    positions: List[int]  # 陷阱可能出现的位置（如果为空则任意位置）
    probability: float = 1.0  # 出现概率 (0.0-1.0)
    max_instances: int = 1  # 最大实例数


class TrapConfigManager:
    """陷阱配置管理器"""

    def __init__(self, config_file: str = "config/trap_config.json"):
        self.config_file = config_file
        self.trap_configs: Dict[str, TrapPositionConfig] = {}
        self.generated_traps: Dict[str, str] = {}  # position_key -> trap_name
        self._init_default_configs()
        self.load_config()

    def _init_default_configs(self):
        """初始化默认陷阱配置"""
        self.trap_configs = {
            "小小火球术": TrapPositionConfig(
                trap_type=TrapType.FIREBALL,
                columns=[3, 4, 5, 6],  # 小数字列
                positions=[],  # 任意位置
                probability=0.3,  # 30%概率在每列出现
                max_instances=2  # 最多2个实例
            ),
            "不要回头": TrapPositionConfig(
                trap_type=TrapType.NO_LOOK_BACK,
                columns=[7, 15],
                positions=[3],
                probability=1.0,
                max_instances=2
            ),
            "河..土地神": TrapPositionConfig(
                trap_type=TrapType.RIVER_SPIRIT,
                columns=[8],
                positions=[4],
                probability=1.0,
                max_instances=1
            ),
            "花言巧语": TrapPositionConfig(
                trap_type=TrapType.SWEET_TALK,
                columns=[12],
                positions=[5],
                probability=1.0,
                max_instances=1
            )
        }

    def load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 支持新格式和旧格式的配置文件
                    if "trap_configs" in data:
                        # 新格式
                        self.generated_traps = data.get("generated_traps", {})
                        # 可以在这里加载trap_configs如果需要
                    else:
                        # 旧格式，保持向后兼容
                        # 暂时不处理旧格式的配置加载
                        pass

            except Exception as e:
                print(f"加载陷阱配置失败: {e}")

    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                "trap_configs": {},
                "generated_traps": self.generated_traps
            }

            for name, config in self.trap_configs.items():
                config_data["trap_configs"][name] = {
                    "trap_type": config.trap_type.value,
                    "columns": config.columns,
                    "positions": config.positions,
                    "probability": config.probability,
                    "max_instances": config.max_instances
                }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存陷阱配置失败: {e}")
            return False

    def generate_trap_positions(self) -> Dict[str, str]:
        """根据配置生成陷阱位置"""
        import random

        # 保留已经手动设置的陷阱
        generated = self.generated_traps.copy()

        for trap_name, config in self.trap_configs.items():
            instances_created = 0

            # 为每个配置的列生成陷阱
            for column in config.columns:
                if instances_created >= config.max_instances:
                    break

                # 检查概率
                if random.random() > config.probability:
                    continue

                # 确定位置
                if config.positions:
                    # 使用指定位置
                    for position in config.positions:
                        if instances_created >= config.max_instances:
                            break
                        position_key = f"{column}_{position}"
                        if position_key not in generated:
                            generated[position_key] = trap_name
                            instances_created += 1
                else:
                    # 在列的随机位置生成
                    # 获取列长度
                    column_lengths = {
                        3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
                        9: 9, 10: 10, 11: 10, 12: 9, 13: 8,
                        14: 7, 15: 6, 16: 5, 17: 4, 18: 3
                    }

                    max_position = column_lengths.get(column, 5)
                    position = random.randint(1, max_position)
                    position_key = f"{column}_{position}"

                    if position_key not in generated:
                        generated[position_key] = trap_name
                        instances_created += 1

        self.generated_traps = generated
        return generated

    def get_trap_for_position(self, column: int, position: int) -> Optional[str]:
        """获取指定位置的陷阱名称"""
        position_key = f"{column}_{position}"
        return self.generated_traps.get(position_key)

    def set_trap_config(self, trap_name: str, columns: List[int], positions: List[int] = None, probability: float = 1.0):
        """设置陷阱配置"""
        if trap_name not in self.trap_configs:
            return False, f"未知陷阱类型: {trap_name}"

        config = self.trap_configs[trap_name]
        config.columns = columns
        if positions is not None:
            config.positions = positions
        config.probability = probability

        return True, f"陷阱 {trap_name} 配置已更新"

    def set_manual_trap(self, trap_name: str, column: int, position: int):
        """手动设置单个陷阱位置"""
        position_key = f"{column}_{position}"
        self.generated_traps[position_key] = trap_name

        # 保存配置
        self.save_config()
        return True, f"在第{column}列-{position}位设置陷阱: {trap_name}"

    def remove_trap_at_position(self, column: int, position: int):
        """移除指定位置的陷阱"""
        position_key = f"{column}_{position}"
        if position_key in self.generated_traps:
            trap_name = self.generated_traps[position_key]
            del self.generated_traps[position_key]

            # 保存配置
            self.save_config()
            return True, f"已移除第{column}列-{position}位的陷阱: {trap_name}"
        else:
            return False, f"第{column}列-{position}位没有陷阱"

    def get_config_info(self) -> str:
        """获取当前配置信息"""
        info = "🕳️ 当前陷阱配置:\n\n"

        for trap_name, config in self.trap_configs.items():
            info += f"🎯 {trap_name}:\n"
            info += f"   列: {config.columns}\n"
            if config.positions:
                info += f"   位置: {config.positions}\n"
            else:
                info += f"   位置: 随机\n"
            info += f"   概率: {config.probability:.1%}\n"
            info += f"   最大数量: {config.max_instances}\n\n"

        if self.generated_traps:
            info += "📍 当前生成的陷阱位置:\n"
            for position, trap_name in self.generated_traps.items():
                column, pos = position.split('_')
                info += f"   {column}列-{pos}位: {trap_name}\n"

        return info