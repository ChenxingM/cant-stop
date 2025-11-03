#!/usr/bin/env python3
"""
CantStop QQ机器人启动脚本
简单的机器人启动入口
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bots.launchers.bot_launcher import main

if __name__ == "__main__":
    print("🚀 CantStop QQ机器人")
    print("=" * 30)
    main()