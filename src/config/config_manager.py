"""
配置管理器
统一管理所有游戏配置
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self._configs = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """加载所有配置文件"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            return

        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                config_name = filename[:-5]  # 移除 .json 扩展名
                file_path = os.path.join(self.config_dir, filename)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._configs[config_name] = json.load(f)
                except Exception as e:
                    print(f"警告：无法加载配置文件 {filename}: {e}")

    def get(self, config_name: str, key_path: str = None, default=None):
        """
        获取配置值

        Args:
            config_name: 配置文件名（不含.json）
            key_path: 配置键路径，用.分隔（如 "database.url"）
            default: 默认值
        """
        if config_name not in self._configs:
            return default

        config = self._configs[config_name]

        if key_path is None:
            return config

        keys = key_path.split('.')
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def set(self, config_name: str, key_path: str, value: Any):
        """
        设置配置值并保存到文件

        Args:
            config_name: 配置文件名（不含.json）
            key_path: 配置键路径，用.分隔
            value: 配置值
        """
        if config_name not in self._configs:
            self._configs[config_name] = {}

        config = self._configs[config_name]
        keys = key_path.split('.')
        current = config

        # 导航到目标位置，创建中间字典
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 设置最终值
        current[keys[-1]] = value

        # 保存到文件
        self._save_config(config_name)

    def _save_config(self, config_name: str):
        """保存配置到文件"""
        if config_name not in self._configs:
            return

        file_path = os.path.join(self.config_dir, f"{config_name}.json")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._configs[config_name], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"错误：无法保存配置文件 {config_name}.json: {e}")

    def reload(self):
        """重新加载所有配置"""
        self._configs.clear()
        self._load_all_configs()

    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._configs.copy()


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(config_name: str, key_path: str = None, default=None):
    """快速获取配置值"""
    return get_config_manager().get(config_name, key_path, default)