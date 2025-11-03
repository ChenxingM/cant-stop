#!/usr/bin/env python3
"""
CantStop 机器人统一启动入口
支持多平台机器人配置和启动
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bots.launchers.unified_launcher import UnifiedLauncher


def main():
    parser = argparse.ArgumentParser(
        description='CantStop 机器人启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置启动（Lagrange）
  python start_bot.py

  # 使用指定配置文件
  python start_bot.py --config config/lagrange_bot_config.json

  # 创建示例配置文件
  python start_bot.py --create-example
        """
    )

    parser.add_argument(
        '--config', '-c',
        default='config/bot_config.json',
        help='机器人配置文件路径 (默认: config/bot_config.json)'
    )

    parser.add_argument(
        '--create-example',
        action='store_true',
        help='创建示例配置文件'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🤖 CantStop 贪骰无厌 - 机器人启动器")
    print("=" * 60)

    if args.create_example:
        print("\n📝 创建示例配置文件...")
    else:
        print(f"\n📂 配置文件: {args.config}")
        print("🚀 正在启动机器人...")

    print("-" * 60)

    try:
        launcher = UnifiedLauncher()
        launcher.run(
            config_path=args.config,
            create_example=args.create_example
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，机器人已停止")
    except Exception as e:
        print(f"\n\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
