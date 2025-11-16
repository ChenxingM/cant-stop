"""
陷阱插件系统 - 支持动态扩展陷阱类型
向后兼容现有的陷阱系统
"""

import importlib
import os
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .trap_system import TrapSystem, TrapType, TrapEffect


class TrapPluginBase(ABC):
    """陷阱插件基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_character_quote(self) -> str:
        """获取角色台词"""
        pass

    @abstractmethod
    def apply_first_time_penalty(self, player_id: str, session_id: str) -> dict:
        """应用首次触发惩罚"""
        pass

    @abstractmethod
    def apply_repeat_penalty(self, player_id: str, session_id: str) -> dict:
        """应用重复触发惩罚"""
        pass

    def get_penalty_description(self) -> str:
        """获取惩罚描述"""
        return "特殊惩罚"

    def can_trigger(self, player_id: str, column: int, position: int) -> bool:
        """检查是否可以触发（可重写）"""
        return True


@dataclass
class TrapPluginConfig:
    """陷阱插件配置"""
    plugin_class: str
    name: str
    description: str
    character_quote: str
    penalty_description: str
    position_config: Dict[str, Any]
    enabled: bool = True


class EnhancedTrapSystem(TrapSystem):
    """增强的陷阱系统，支持插件机制"""

    def __init__(self):
        # 初始化父类
        super().__init__()

        # 插件相关
        self.plugins: Dict[str, TrapPluginBase] = {}
        self.plugin_configs: Dict[str, TrapPluginConfig] = {}

        # 加载插件配置
        self._load_plugin_configs()

        # 自动加载内置插件
        self._load_builtin_plugins()

    def _load_plugin_configs(self):
        """加载插件配置"""
        config_file = "config/trap_plugins.json"
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                for plugin_name, plugin_data in config.get("plugins", {}).items():
                    self.plugin_configs[plugin_name] = TrapPluginConfig(
                        plugin_class=plugin_data["plugin_class"],
                        name=plugin_data["name"],
                        description=plugin_data["description"],
                        character_quote=plugin_data["character_quote"],
                        penalty_description=plugin_data["penalty_description"],
                        position_config=plugin_data["position_config"],
                        enabled=plugin_data.get("enabled", True)
                    )
            except Exception as e:
                print(f"加载陷阱插件配置失败: {e}")

    def _load_builtin_plugins(self):
        """加载内置陷阱插件"""
        try:
            from .trap_plugins import TRAP_PLUGINS, create_trap_plugin

            for trap_name, plugin_class in TRAP_PLUGINS.items():
                if trap_name in self.plugin_configs:
                    plugin = create_trap_plugin(trap_name)
                    if plugin:
                        self.register_plugin(trap_name, plugin)
        except ImportError:
            print("警告：无法导入内置陷阱插件")
        except Exception as e:
            print(f"加载内置陷阱插件失败: {e}")

    def register_plugin(self, plugin_name: str, plugin: TrapPluginBase) -> bool:
        """注册陷阱插件"""
        try:
            self.plugins[plugin_name] = plugin
            return True
        except Exception as e:
            print(f"注册陷阱插件失败: {e}")
            return False

    def load_plugin_from_file(self, plugin_name: str, file_path: str) -> bool:
        """从文件加载插件"""
        try:
            # 动态导入插件模块
            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = getattr(module, plugin_name, None)
            if plugin_class and issubclass(plugin_class, TrapPluginBase):
                plugin_instance = plugin_class()
                return self.register_plugin(plugin_name, plugin_instance)

            return False
        except Exception as e:
            print(f"从文件加载陷阱插件失败: {e}")
            return False

    def get_trap_for_position(self, column: int, position: int) -> Optional[str]:
        """根据位置获取陷阱类型（增强版）"""
        # 首先检查插件陷阱
        for plugin_name, plugin in self.plugins.items():
            config = self.plugin_configs.get(plugin_name)
            if config and config.enabled:
                pos_config = config.position_config
                if self._check_position_match(column, position, pos_config):
                    return plugin_name

        # 然后检查原有陷阱
        original_trap = super().get_trap_for_position(column, position)
        return original_trap.value if original_trap else None

    def _check_position_match(self, column: int, position: int, pos_config: Dict[str, Any]) -> bool:
        """检查位置是否匹配配置"""
        allowed_columns = pos_config.get("columns", [])
        allowed_positions = pos_config.get("positions", [])

        column_match = not allowed_columns or column in allowed_columns
        position_match = not allowed_positions or position in allowed_positions

        return column_match and position_match

    def trigger_trap(self, player_id: str, trap_name: str) -> Tuple[bool, str, Optional[dict]]:
        """触发陷阱（增强版）"""
        # 检查是否是插件陷阱
        if trap_name in self.plugins:
            return self._trigger_plugin_trap(player_id, trap_name)

        # 检查是否是原有陷阱类型
        for trap_type in TrapType:
            if trap_type.value == trap_name:
                return super().trigger_trap(player_id, trap_type)

        return False, f"未知陷阱类型: {trap_name}", None

    def _trigger_plugin_trap(self, player_id: str, plugin_name: str) -> Tuple[bool, str, Optional[dict]]:
        """触发插件陷阱"""
        plugin = self.plugins.get(plugin_name)
        config = self.plugin_configs.get(plugin_name)

        if not plugin or not config:
            return False, f"插件陷阱 {plugin_name} 不存在", None

        # 检查是否是首次触发
        player_history = self.player_trap_history.get(player_id, [])
        is_first_time = plugin_name not in player_history

        # 记录触发历史
        if player_id not in self.player_trap_history:
            self.player_trap_history[player_id] = []
        self.player_trap_history[player_id].append(plugin_name)

        message = f"🕳️ 触发陷阱：{plugin_name}\n"
        message += f"📖 {config.description}\n"
        message += f"💬 \"{config.character_quote}\"\n\n"

        penalty_data = None

        if is_first_time:
            message += f"⚠️ 首次触发特殊惩罚：\n{config.penalty_description}"
            penalty_data = plugin.apply_first_time_penalty(player_id, "")
        else:
            penalty_data = plugin.apply_repeat_penalty(player_id, "")
            message += f"💰 重复触发惩罚：{penalty_data.get('description', '默认惩罚')}"

        return True, message, penalty_data

    def get_all_trap_names(self) -> List[str]:
        """获取所有陷阱名称（包括插件）"""
        original_traps = [trap.value for trap in TrapType]
        plugin_traps = list(self.plugins.keys())
        return original_traps + plugin_traps

    def add_trap_config(self, trap_name: str, config: TrapPluginConfig) -> bool:
        """添加陷阱配置"""
        try:
            self.plugin_configs[trap_name] = config
            return True
        except Exception as e:
            print(f"添加陷阱配置失败: {e}")
            return False

    def save_plugin_configs(self) -> bool:
        """保存插件配置到文件"""
        try:
            import json

            config_data = {"plugins": {}}
            for plugin_name, config in self.plugin_configs.items():
                config_data["plugins"][plugin_name] = {
                    "plugin_class": config.plugin_class,
                    "name": config.name,
                    "description": config.description,
                    "character_quote": config.character_quote,
                    "penalty_description": config.penalty_description,
                    "position_config": config.position_config,
                    "enabled": config.enabled
                }

            with open("config/trap_plugins.json", 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"保存插件配置失败: {e}")
            return False

    def is_enhanced_system(self) -> bool:
        """检查是否使用增强系统"""
        return True


# 向后兼容的陷阱管理器
class TrapManager:
    """陷阱管理器 - 提供向后兼容的接口"""

    def __init__(self, use_enhanced_system: bool = True):
        self.use_enhanced = use_enhanced_system

        if use_enhanced_system:
            self.system = EnhancedTrapSystem()
        else:
            self.system = TrapSystem()

    def get_trap_for_position(self, column: int, position: int):
        """获取位置陷阱（向后兼容）"""
        return self.system.get_trap_for_position(column, position)

    def trigger_trap(self, player_id: str, trap_identifier):
        """触发陷阱（向后兼容）"""
        # 如果是TrapType对象，转换为字符串
        if hasattr(trap_identifier, 'value'):
            trap_name = trap_identifier.value
        else:
            trap_name = str(trap_identifier)

        return self.system.trigger_trap(player_id, trap_name)

    def get_all_traps(self):
        """获取所有陷阱（向后兼容）"""
        if hasattr(self.system, 'get_all_trap_names'):
            # 增强系统
            names = self.system.get_all_trap_names()
            return [{"name": name} for name in names]
        else:
            # 原系统
            return self.system.get_all_traps()

    def register_plugin(self, plugin_name: str, plugin) -> bool:
        """注册插件（仅增强系统）"""
        if hasattr(self.system, 'register_plugin'):
            return self.system.register_plugin(plugin_name, plugin)
        return False