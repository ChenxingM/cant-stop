"""
调试错误
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService

    print("尝试创建GameService...")
    game_service = GameService()

    print("尝试重置数据...")
    result = game_service.reset_all_game_data()
    print(f"重置结果: {result}")

    print("尝试注册玩家...")
    result = game_service.register_player("test", "测试玩家", "收养人")
    print(f"注册结果: {result}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()