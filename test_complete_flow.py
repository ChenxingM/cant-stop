"""
完整的陷阱触发流程测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService

    print("=== 完整陷阱触发流程测试 ===")

    game_service = GameService()

    # 1. 注册和开始游戏
    print("1. 设置游戏...")
    game_service.register_player("test", "测试", "收养人")
    game_service.start_new_game("test")

    # 2. 清理现有陷阱，设置测试陷阱
    print("2. 设置测试陷阱在第6列-第1位...")
    game_service.set_manual_trap("小小火球术", 6, 1)

    # 3. 给玩家积分
    game_service.add_score("test", 100, "测试")

    # 4. 掷骰子
    print("3. 掷骰子...")
    success, message, combinations = game_service.roll_dice("test")
    print(f"   掷骰结果: {success}")
    if success and combinations:
        print(f"   可用组合: {combinations}")

        # 找到包含6的组合
        target_combination = None
        for combo in combinations:
            if 6 in combo:
                target_combination = combo
                break

        if target_combination:
            print(f"   选择包含6的组合: {target_combination}")

            # 移动到第6列
            print("4. 移动到第6列...")
            success, message = game_service.move_markers("test", [6])
            print(f"   移动结果: {success}")
            print("   移动消息:")
            # 避免直接打印可能包含emoji的消息
            try:
                print(f"   {message}")
            except UnicodeEncodeError:
                print("   [消息包含特殊字符，可能是陷阱触发消息]")
                # 检查消息是否包含陷阱关键词
                if "陷阱" in message or "火球" in message:
                    print("   ✓ 检测到陷阱触发消息！")
                else:
                    print("   ✗ 未检测到陷阱触发")

        else:
            print("   没有找到包含6的组合，无法测试第6列的陷阱")

    else:
        print("   掷骰失败，无法继续测试")

except Exception as e:
    print(f"ERROR: {e}")
    try:
        print("   错误详情:")
        import traceback
        traceback.print_exc()
    except:
        print("   无法显示错误详情")

    # 尝试检查是否是编码问题
    if "codec" in str(e) and "encode" in str(e):
        print("   这是一个编码问题，可能是陷阱消息中的emoji字符导致的")