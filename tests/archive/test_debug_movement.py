"""
调试移动失败问题
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService

    print("=== 调试移动失败问题 ===")

    game_service = GameService()

    # 1. 重置并设置干净的测试环境
    print("1. 重置测试环境...")
    game_service.reset_all_game_data()

    success, message = game_service.register_player("test", "测试玩家", "收养人")
    print(f"   注册结果: {success} - {message}")

    success, message = game_service.start_new_game("test")
    print(f"   开始游戏结果: {success} - {message}")

    # 2. 检查玩家和会话状态
    print("2. 检查初始状态...")
    player = game_service.db.get_player("test")
    session = game_service.db.get_player_active_session("test")

    print(f"   玩家存在: {player is not None}")
    print(f"   会话存在: {session is not None}")
    if player:
        print(f"   玩家积分: {player.current_score}")
    if session:
        print(f"   会话状态: {session.state}")
        print(f"   会话ID: {session.session_id}")

    # 3. 给积分
    print("3. 添加积分...")
    success, message = game_service.add_score("test", 100, "测试积分")
    print(f"   添加积分结果: {success} - {message}")

    # 4. 掷骰子
    print("4. 掷骰子...")
    success, message, combinations = game_service.roll_dice("test")
    print(f"   掷骰结果: {success}")
    if success:
        print(f"   可用组合: {combinations}")
    else:
        print(f"   掷骰失败: {message}")

    # 5. 尝试移动
    if success and combinations:
        print("5. 尝试移动...")
        first_combo = combinations[0]
        print(f"   选择组合: {first_combo}")

        success, message = game_service.move_markers("test", list(first_combo))
        print(f"   移动结果: {success}")
        print(f"   移动消息: '{message}' (长度: {len(message)})")

        if not success:
            print("   移动失败，详细检查...")

            # 检查当前状态
            player = game_service.db.get_player("test")
            session = game_service.db.get_player_active_session("test")

            if session:
                print(f"   会话状态: {session.state}")
                print(f"   当前骰子: {session.current_dice is not None}")
                if session.current_dice:
                    print(f"   骰子结果: {session.current_dice.results}")
                print(f"   临时标记数量: {len(session.temporary_markers)}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()