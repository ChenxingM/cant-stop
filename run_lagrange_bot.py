#!/usr/bin/env python3
"""
CantStop Lagrange机器人启动脚本
基于你现有的LagrangeClient实现
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bots.launchers.unified_launcher import main

if __name__ == "__main__":
    print("CantStop Lagrange Bot")
    print("WebSocket communication with Lagrange.OneBot")
    print("=" * 40)
    main()