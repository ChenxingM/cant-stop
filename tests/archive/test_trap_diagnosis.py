"""
完整的陷阱触发诊断测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService

    print("=== 陷阱触发诊断测试 ===")

    game_service = GameService()

    # 1. 清理环境并注册玩家
    print("1. 设置测试环境...")
    try:
        game_service.register_player("test", "测试玩家", "收养人")
    except:
        pass  # 玩家可能已存在

    game_service.start_new_game("test")

    # 2. 设置陷阱在一个明确的位置
    target_column = 5
    target_position = 1
    print(f"2. 设置陷阱在第{target_column}列-第{target_position}位...")
    success, message = game_service.set_manual_trap("小小火球术", target_column, target_position)
    print(f"   设置结果: {success}, {message}")

    # 3. 检查陷阱配置
    print("3. 检查陷阱配置...")
    trap_key = f"{target_column}_{target_position}"

    # 检查trap_config
    trap_name = game_service.engine.trap_config.get_trap_for_position(target_column, target_position)
    print(f"   陷阱配置中第{target_column}列-第{target_position}位: {trap_name}")

    # 检查generated_traps
    generated_trap = game_service.engine.trap_config.generated_traps.get(trap_key)
    print(f"   generated_traps中{trap_key}: {generated_trap}")

    # 检查map_events
    has_event = trap_key in game_service.engine.map_events
    print(f"   map_events中是否有{trap_key}: {has_event}")

    if has_event:
        events = game_service.engine.map_events[trap_key]
        print(f"   事件数量: {len(events)}")
        for i, event in enumerate(events):
            print(f"     事件{i+1}: 名称='{event.name}', 类型={event.event_type}")

    # 4. 给玩家积分并开始游戏流程
    print("4. 给玩家积分...")
    game_service.add_score("test", 100, "测试积分")

    # 5. 掷骰子并检查
    print("5. 掷骰子...")
    success, message, combinations = game_service.roll_dice("test")
    print(f"   掷骰成功: {success}")
    if success and combinations:
        print(f"   可用组合: {combinations}")

        # 寻找包含目标列的组合
        target_combo = None
        for combo in combinations:
            if target_column in combo:
                target_combo = combo
                break

        if target_combo:
            print(f"   选择组合: {target_combo}")

            # 6. 检查移动前的状态
            print("6. 检查移动前的玩家状态...")
            player = game_service.db.get_player("test")
            session = game_service.db.get_player_active_session("test")

            permanent_progress = player.progress.get_progress(target_column)
            print(f"   第{target_column}列永久进度: {permanent_progress}")

            existing_marker = session.get_temporary_marker(target_column) if session else None
            if existing_marker:
                print(f"   第{target_column}列已有临时标记在位置: {existing_marker.position}")
                expected_new_position = permanent_progress + existing_marker.position + 1
            else:
                print(f"   第{target_column}列无临时标记")
                expected_new_position = permanent_progress + 1

            print(f"   移动后预期总位置: {expected_new_position}")
            print(f"   陷阱位置: {target_position}")
            print(f"   位置是否匹配: {expected_new_position == target_position}")

            # 7. 执行移动
            print("7. 执行移动...")
            success, move_message = game_service.move_markers("test", [target_column])
            print(f"   移动成功: {success}")
            print("   移动消息:")
            print(f"   {repr(move_message)}")  # 使用repr避免编码问题

            # 检查是否包含陷阱关键词
            trap_keywords = ["陷阱", "火球", "🕳️", "小小火球术"]
            contains_trap = any(keyword in move_message for keyword in trap_keywords)
            print(f"   消息是否包含陷阱关键词: {contains_trap}")

            # 8. 检查移动后的状态
            print("8. 检查移动后的状态...")
            player = game_service.db.get_player("test")  # 重新加载
            session = game_service.db.get_player_active_session("test")

            if session:
                marker = session.get_temporary_marker(target_column)
                if marker:
                    actual_total_pos = player.progress.get_progress(target_column) + marker.position
                    print(f"   实际总位置: {actual_total_pos}")
                    print(f"   是否在陷阱位置: {actual_total_pos == target_position}")
                else:
                    print("   移动后无临时标记（可能被陷阱清除）")

        else:
            print(f"   没有找到包含第{target_column}列的组合")
            print("   尝试使用其他测试方法...")

            # 直接测试事件触发
            if has_event:
                print("   直接测试事件触发...")
                event = game_service.engine.map_events[trap_key][0]
                session = game_service.db.get_player_active_session("test")
                if session:
                    try:
                        trap_message = game_service.engine._trigger_event(session.session_id, event)
                        print(f"   直接触发结果: {repr(trap_message)}")
                    except Exception as e:
                        print(f"   直接触发失败: {e}")
    else:
        print(f"   掷骰失败: {message}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()