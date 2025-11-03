"""
配置管理器
整合和简化机器人配置
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class WebSocketConfig:
    """WebSocket配置"""
    url: str = "ws://127.0.0.2:8081/onebot/v11/ws"
    access_token: Optional[str] = None
    reconnect: bool = True
    timeout: int = 30


@dataclass
class BotSettings:
    """机器人设置"""
    allowed_groups: List[int] = None
    admin_users: List[int] = None
    auto_register: bool = True
    default_faction: str = "收养人"


@dataclass
class BotConfig:
    """统一的机器人配置"""
    platform: str  # "lagrange" 或 "qq_http"
    websocket: WebSocketConfig = None
    bot: BotSettings = None

    def __post_init__(self):
        if self.websocket is None:
            self.websocket = WebSocketConfig()
        if self.bot is None:
            self.bot = BotSettings()


class ConfigManager:
    """配置管理器"""

    @staticmethod
    def load_config(config_path: str) -> BotConfig:
        """从文件加载配置"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return ConfigManager._dict_to_config(data)

    @staticmethod
    def save_config(config: BotConfig, config_path: str) -> None:
        """保存配置到文件"""
        data = ConfigManager._config_to_dict(config)

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def create_example_config(platform: str = "lagrange") -> BotConfig:
        """创建示例配置"""
        return BotConfig(
            platform=platform,
            websocket=WebSocketConfig(
                url="ws://127.0.0.2:8081/onebot/v11/ws",
                access_token=None,  # 如果服务器需要验证，填入token
                reconnect=True,
                timeout=30
            ),
            bot=BotSettings(
                allowed_groups=[541674420],  # 示例群号
                admin_users=[1234567890],    # 示例管理员
                auto_register=True,
                default_faction="收养人"
            )
        )

    @staticmethod
    def _dict_to_config(data: Dict[str, Any]) -> BotConfig:
        """字典转配置对象"""
        websocket_data = data.get("websocket", {})
        bot_data = data.get("bot", {})

        return BotConfig(
            platform=data.get("platform", "lagrange"),
            websocket=WebSocketConfig(**websocket_data),
            bot=BotSettings(**bot_data)
        )

    @staticmethod
    def _config_to_dict(config: BotConfig) -> Dict[str, Any]:
        """配置对象转字典"""
        return {
            "platform": config.platform,
            "websocket": asdict(config.websocket),
            "bot": asdict(config.bot)
        }