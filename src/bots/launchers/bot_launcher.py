"""
机器人启动器 - 统一管理QQ机器人的启动和配置
"""

import asyncio
import logging
import json
import signal
import sys
from typing import Dict, List, Optional
from pathlib import Path

from ..platforms.qq_bot import QQBot
from ..adapters.qq_message_adapter import QQMessageAdapter, MessageStyle


class BotConfig:
    """机器人配置"""

    def __init__(self, config_file: str = "config/qq_bot_config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "onebot": {
                "url": "http://127.0.0.1:3001",
                "timeout": 30
            },
            "bot": {
                "listen_host": "127.0.0.1",
                "listen_port": 8080,
                "allowed_groups": [],
                "admin_users": [],
                "auto_register": True
            },
            "message": {
                "use_emoji": True,
                "max_length": 1000,
                "compact_mode": False,
                "mention_user": False,
                "welcome_new_users": True
            },
            "game": {
                "auto_help": True,
                "command_prefix": "",
                "rate_limit": {
                    "enabled": True,
                    "max_commands_per_minute": 10
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/qq_bot.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }

        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    default_config.update(loaded_config)
            else:
                # 如果配置文件不存在，创建默认配置文件
                self._save_config(default_config)

        except Exception as e:
            print(f"加载配置文件失败，使用默认配置: {e}")

        return default_config

    def _save_config(self, config: Dict):
        """保存配置文件"""
        try:
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, section: str, key: str = None, default=None):
        """获取配置值"""
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value):
        """设置配置值"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._save_config(self.config)


class BotLauncher:
    """机器人启动器"""

    def __init__(self, config_file: str = "config/qq_bot_config.json"):
        self.config = BotConfig(config_file)
        self.bot: Optional[QQBot] = None
        self.message_adapter: Optional[QQMessageAdapter] = None
        self.logger = self._setup_logging()
        self.running = False

    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('qq_bot')
        logger.setLevel(getattr(logging, self.config.get('logging', 'level', 'INFO')))

        # 清除已有的处理器
        logger.handlers.clear()

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 文件处理器
        log_file = self.config.get('logging', 'file', 'logs/qq_bot.log')
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建日志文件: {e}")

        return logger

    def create_bot(self) -> QQBot:
        """创建机器人实例"""
        onebot_url = self.config.get('onebot', 'url')
        listen_host = self.config.get('bot', 'listen_host')
        listen_port = self.config.get('bot', 'listen_port')

        bot = QQBot(onebot_url, listen_host, listen_port)

        # 配置允许的群和管理员
        allowed_groups = self.config.get('bot', 'allowed_groups', [])
        admin_users = self.config.get('bot', 'admin_users', [])

        if allowed_groups:
            bot.set_allowed_groups(allowed_groups)
            self.logger.info(f"限制群聊: {allowed_groups}")

        if admin_users:
            bot.set_admin_users(admin_users)
            self.logger.info(f"管理员用户: {admin_users}")

        return bot

    def create_message_adapter(self) -> QQMessageAdapter:
        """创建消息适配器"""
        style = MessageStyle(
            use_emoji=self.config.get('message', 'use_emoji', True),
            max_length=self.config.get('message', 'max_length', 1000),
            compact_mode=self.config.get('message', 'compact_mode', False),
            mention_user=self.config.get('message', 'mention_user', False)
        )
        return QQMessageAdapter(style)

    async def start_bot(self):
        """启动机器人"""
        try:
            self.logger.info("正在启动QQ机器人...")

            # 创建机器人和适配器
            self.bot = self.create_bot()
            self.message_adapter = self.create_message_adapter()

            # 启动机器人
            await self.bot.start()

            self.running = True
            self.logger.info("QQ机器人启动成功！")

            # 设置信号处理器
            def signal_handler(signum, frame):
                self.logger.info(f"收到信号 {signum}，正在关闭机器人...")
                asyncio.create_task(self.stop_bot())

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # 保持运行
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"启动机器人失败: {e}")
            raise

    async def stop_bot(self):
        """停止机器人"""
        if self.bot:
            self.logger.info("正在停止机器人...")
            await self.bot.stop()
            self.running = False
            self.logger.info("机器人已停止")

    def run(self):
        """运行机器人（主函数）"""
        try:
            asyncio.run(self.start_bot())
        except KeyboardInterrupt:
            self.logger.info("用户中断，正在退出...")
        except Exception as e:
            self.logger.error(f"机器人运行错误: {e}")
            sys.exit(1)

    def print_status(self):
        """打印机器人状态"""
        print("🤖 CantStop QQ机器人状态")
        print("=" * 40)
        print(f"OneBot地址: {self.config.get('onebot', 'url')}")
        print(f"监听地址: {self.config.get('bot', 'listen_host')}:{self.config.get('bot', 'listen_port')}")

        allowed_groups = self.config.get('bot', 'allowed_groups', [])
        if allowed_groups:
            print(f"允许的群: {', '.join(allowed_groups)}")
        else:
            print("允许的群: 所有群")

        admin_users = self.config.get('bot', 'admin_users', [])
        if admin_users:
            print(f"管理员: {', '.join(admin_users)}")

        print(f"消息适配: emoji={self.config.get('message', 'use_emoji')}, "
              f"紧凑模式={self.config.get('message', 'compact_mode')}")
        print("=" * 40)

    def create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "onebot": {
                "url": "http://127.0.0.1:3001",
                "timeout": 30
            },
            "bot": {
                "listen_host": "127.0.0.1",
                "listen_port": 8080,
                "allowed_groups": [],
                "admin_users": [],
                "auto_register": True
            },
            "message": {
                "use_emoji": True,
                "max_length": 1000,
                "compact_mode": False,
                "mention_user": False,
                "welcome_new_users": True
            },
            "game": {
                "auto_help": True,
                "command_prefix": "",
                "rate_limit": {
                    "enabled": True,
                    "max_commands_per_minute": 10
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/qq_bot.log"
            }
        }

        self.config._save_config(default_config)
        print(f"已创建默认配置文件: {self.config.config_file}")
        return default_config


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='CantStop QQ机器人')
    parser.add_argument('--config', '-c', default='config/qq_bot_config.json',
                        help='配置文件路径')
    parser.add_argument('--create-config', action='store_true',
                        help='创建默认配置文件')
    parser.add_argument('--status', action='store_true',
                        help='显示机器人状态')

    args = parser.parse_args()

    launcher = BotLauncher(args.config)

    if args.create_config:
        launcher.create_default_config()
        return

    if args.status:
        launcher.print_status()
        return

    # 启动机器人
    print("🚀 启动CantStop QQ机器人...")
    launcher.print_status()
    launcher.run()


if __name__ == "__main__":
    main()