"""
遭遇配置系统 - 允许GM配置遭遇位置
"""

import json
import os
from typing import Dict, Optional


class EncounterConfigManager:
    """遭遇配置管理器"""

    def __init__(self, config_file: str = "config/encounter_config.json"):
        self.config_file = config_file
        self.generated_encounters: Dict[str, str] = {}  # position_key -> encounter_name
        self.load_config()

    def load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.generated_encounters = data.get("generated_encounters", {})
            except Exception as e:
                print(f"加载遭遇配置失败: {e}")

    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                "generated_encounters": self.generated_encounters
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存遭遇配置失败: {e}")
            return False

    def get_encounter_for_position(self, column: int, position: int) -> Optional[str]:
        """获取指定位置的遭遇名称"""
        position_key = f"{column}_{position}"
        return self.generated_encounters.get(position_key)

    def set_manual_encounter(self, encounter_name: str, column: int, position: int):
        """手动设置单个遭遇位置"""
        position_key = f"{column}_{position}"
        self.generated_encounters[position_key] = encounter_name

        # 保存配置
        self.save_config()
        return True, f"在第{column}列-{position}位设置遭遇: {encounter_name}"

    def remove_encounter_at_position(self, column: int, position: int):
        """移除指定位置的遭遇"""
        position_key = f"{column}_{position}"
        if position_key in self.generated_encounters:
            encounter_name = self.generated_encounters[position_key]
            del self.generated_encounters[position_key]

            # 保存配置
            self.save_config()
            return True, f"已移除第{column}列-{position}位的遭遇: {encounter_name}"
        else:
            return False, f"第{column}列-{position}位没有遭遇"

    def get_all_positions(self) -> Dict[str, str]:
        """获取所有遭遇位置"""
        return self.generated_encounters.copy()

    def clear_all(self):
        """清除所有遭遇"""
        self.generated_encounters.clear()
        self.save_config()
        return True, "已清除所有遭遇位置"
