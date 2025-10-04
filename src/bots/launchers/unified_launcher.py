"""
统一机器人启动器
支持多平台机器人的配置和启动
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path

from .config_manager import ConfigManager, BotConfig


class UnifiedLauncher:
    """统一启动器"""

    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    async def launch_bot(self, config: BotConfig):
        """根据配置启动机器人"""
        try:
            if config.platform == "lagrange":
                # 延迟导入Lagrange机器人
                from ..platforms.lagrange_bot import CantStopLagrangeBot
                bot = CantStopLagrangeBot(
                    ws_url=config.websocket.url,
                    allowed_groups=config.bot.allowed_groups,
                    admin_users=config.bot.admin_users
                )
                await bot.run()

            elif config.platform == "qq_http":
                # 延迟导入QQ机器人
                from ..platforms.qq_bot import QQBot
                bot = QQBot(
                    onebot_url=config.websocket.url,
                    listen_host="127.0.0.1",
                    listen_port=8080
                )
                await bot.run()

            else:
                raise ValueError(f"不支持的平台: {config.platform}")

        except Exception as e:
            self.logger.error(f"启动机器人失败: {e}")
            raise

    def run(self, config_path: str = None, create_example: bool = False):
        """运行启动器"""
        try:
            if create_example:
                self._create_example_config()
                return

            if not config_path:
                config_path = "config/bot_config.json"

            if not os.path.exists(config_path):
                self.logger.error(f"配置文件不存在: {config_path}")
                self.logger.info("使用 --create-example 创建示例配置文件")
                return

            config = ConfigManager.load_config(config_path)
            self.logger.info(f"加载配置: {config_path} (平台: {config.platform})")

            asyncio.run(self.launch_bot(config))

        except KeyboardInterrupt:
            self.logger.info("用户中断启动")
        except Exception as e:
            self.logger.error(f"启动失败: {e}")

    def _create_example_config(self):
        """创建示例配置文件"""
        configs = {
            "lagrange": ConfigManager.create_example_config("lagrange"),
            "qq_http": ConfigManager.create_example_config("qq_http")
        }

        os.makedirs("config", exist_ok=True)

        for platform, config in configs.items():
            config_path = f"config/{platform}_bot_config.json"
            ConfigManager.save_config(config, config_path)
            self.logger.info(f"创建示例配置: {config_path}")

        self.logger.info("示例配置文件已创建，请编辑后使用")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CantStop 统一机器人启动器")
    parser.add_argument("-c", "--config", help="配置文件路径")
    parser.add_argument("--create-example", action="store_true", help="创建示例配置文件")
    parser.add_argument("--platform", choices=["lagrange", "qq_http"], help="指定平台")

    args = parser.parse_args()

    launcher = UnifiedLauncher()

    if args.create_example:
        launcher._create_example_config()
    else:
        config_path = args.config
        if args.platform and not config_path:
            config_path = f"config/{args.platform}_bot_config.json"

        launcher.run(config_path)


if __name__ == "__main__":
    main()