"""
测试陷阱触发机制
"""

import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService
    from src.models.game_models import Faction

    print("创建游戏服务...")
    game_service = GameService()

    print("注册测试玩家...")
    success, message = game_service.register_player("test_player", "测试玩家", "收养人")
    print(f"注册结果: {success}, {message}")

    print("开始新游戏...")
    success, message = game_service.start_new_game("test_player")
    print(f"开始游戏结果: {success}, {message}")

    print("手动设置陷阱 - 小小火球术 在第5列-第2位...")
    success, message = game_service.set_manual_trap("小小火球术", 5, 2)
    print(f"设置陷阱结果: {success}, {message}")

    print("检查陷阱配置...")
    trap_name = game_service.engine.trap_config.get_trap_for_position(5, 2)
    print(f"第5列-第2位的陷阱: {trap_name}")

    print("检查游戏引擎中的map_events...")
    position_key = "5_2"
    if position_key in game_service.engine.map_events:
        events = game_service.engine.map_events[position_key]
        print(f"位置 {position_key} 的事件数量: {len(events)}")
        for event in events:
            print(f"  事件: {event.name}, 类型: {event.event_type}")
    else:
        print(f"位置 {position_key} 没有事件")

    print("模拟玩家移动到陷阱位置...")
    # 这里我们不实际移动，但可以检查事件触发机制
    if position_key in game_service.engine.map_events:
        for event in game_service.engine.map_events[position_key]:
            if event.event_type.name == "TRAP":
                print(f"模拟触发陷阱: {event.name}")
                # 这里可以调用事件处理方法进行测试
                session_id = "test_session"
                # 注意：实际游戏中这需要有效的session，这里只是概念验证

    print("\n测试完成！")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()