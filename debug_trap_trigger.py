"""
调试陷阱触发问题
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService
    from src.models.game_models import Faction

    print("=== 调试陷阱触发问题 ===")

    game_service = GameService()

    # 1. 注册玩家
    print("1. 注册玩家...")
    success, message = game_service.register_player("debug_player", "调试玩家", "收养人")
    print(f"   注册结果: {success}")

    # 2. 开始游戏
    print("2. 开始游戏...")
    success, message = game_service.start_new_game("debug_player")
    print(f"   游戏开始结果: {success}")

    # 3. 手动设置陷阱
    print("3. 手动设置陷阱在第5列-第1位...")
    success, message = game_service.set_manual_trap("小小火球术", 5, 1)
    print(f"   设置陷阱结果: {success}, {message}")

    # 4. 检查陷阱配置
    print("4. 检查陷阱配置...")
    trap_name = game_service.engine.trap_config.get_trap_for_position(5, 1)
    print(f"   第5列-第1位的陷阱: {trap_name}")

    # 5. 检查游戏引擎中的map_events
    print("5. 检查游戏引擎map_events...")
    position_key = "5_1"
    events_exist = position_key in game_service.engine.map_events
    print(f"   位置{position_key}是否有事件: {events_exist}")

    if events_exist:
        events = game_service.engine.map_events[position_key]
        print(f"   事件数量: {len(events)}")
        for i, event in enumerate(events):
            print(f"     事件{i+1}: 名称='{event.name}', 类型={event.event_type}, ID={event.event_id}")

    # 6. 模拟玩家移动触发
    print("6. 尝试移动玩家标记到陷阱位置...")

    # 首先给玩家一些积分用于掷骰
    success, message = game_service.add_score("debug_player", 100, "测试积分")
    print(f"   添加积分结果: {success}")

    # 掷骰子
    success, message, combinations = game_service.roll_dice("debug_player")
    print(f"   掷骰结果: {success}")
    if success and combinations:
        print(f"   可用组合: {combinations}")

    # 尝试移动到目标列
    print(f"   尝试移动到第5列...")
    success, message = game_service.move_markers("debug_player", [5])
    print(f"   移动结果: {success}")
    print(f"   移动消息: {message}")

    # 7. 检查玩家当前位置
    print("7. 检查玩家当前状态...")
    player = game_service.db.get_player("debug_player")
    session = game_service.db.get_player_active_session("debug_player")

    if session:
        print("   临时标记:")
        for marker in session.temporary_markers:
            total_pos = player.progress.get_progress(marker.column) + marker.position
            print(f"     第{marker.column}列: 临时位置{marker.position}, 总位置{total_pos}")

    # 8. 直接测试事件触发
    print("8. 直接测试事件触发...")
    if events_exist and len(game_service.engine.map_events[position_key]) > 0:
        event = game_service.engine.map_events[position_key][0]
        print(f"   测试事件: {event.name}")

        # 获取会话ID
        active_session = game_service.db.get_player_active_session("debug_player")
        if active_session:
            session_id = active_session.session_id
            print(f"   会话ID: {session_id}")

            # 直接调用事件触发
            try:
                trap_message = game_service.engine._trigger_event(session_id, event)
                print(f"   触发结果: '{trap_message}'")
            except Exception as e:
                print(f"   触发失败: {e}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()