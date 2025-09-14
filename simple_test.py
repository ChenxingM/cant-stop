"""
简单的GUI导入测试
"""

import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("测试导入游戏服务...")
    from src.services.game_service import GameService
    print("OK 游戏服务导入成功")

    print("测试导入陷阱系统...")
    from src.core.trap_system import TrapSystem
    print("OK 陷阱系统导入成功")

    print("测试创建游戏服务实例...")
    game_service = GameService()
    print("OK 游戏服务实例创建成功")

    print("测试陷阱配置...")
    trap_config = game_service.engine.trap_config
    print(f"OK 陷阱配置获取成功: {len(trap_config.trap_configs)} 个陷阱类型")

    print("测试手动陷阱设置...")
    success, message = game_service.set_manual_trap("小小火球术", 5, 3)
    print(f"OK 手动陷阱设置: {success}, {message}")

    print("\n所有测试通过！")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()