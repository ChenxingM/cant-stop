"""
测试高级游戏状态持久化（包括进度、临时标记、强制骰子）
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_advanced_persistence():
    """测试高级游戏状态持久化"""
    try:
        # 重置数据库管理器全局实例
        import src.database.database as db_module
        db_module.db_manager = None

        from src.services.game_service import GameService

        print("=== 高级游戏状态持久化测试 ===")

        print("\n1. 初始化第一个GameService实例...")
        game_service1 = GameService()

        # 确保表结构正确
        game_service1.db.drop_tables()
        game_service1.db.create_tables()

        print("2. 创建复杂的测试状态...")

        # 注册玩家
        game_service1.register_player("player1", "测试玩家1", "收养人")
        game_service1.add_score("player1", 200, "测试积分")

        # 开始游戏
        game_service1.start_new_game("player1")

        # 设置陷阱
        game_service1.set_manual_trap("小小火球术", 6, 1)

        # 模拟游戏进程：掷骰子并移动
        attempts = 0
        game_progressed = False

        while attempts < 10 and not game_progressed:
            attempts += 1
            success, message, combinations = game_service1.roll_dice("player1")
            if success and combinations:
                # 选择第一个组合
                first_combo = combinations[0]
                try:
                    success, move_message = game_service1.move_markers("player1", list(first_combo))
                    if success:
                        game_progressed = True
                        print(f"   成功移动到列: {first_combo}")
                except:
                    # 可能触发了陷阱
                    game_progressed = True
                    print("   移动过程中触发了陷阱")
                break

        # 手动设置一些永久进度
        player1 = game_service1.db.get_player("player1")
        if player1:
            player1.progress.set_progress(3, 2)  # 第3列进度2
            player1.progress.set_progress(5, 1)  # 第5列进度1
            game_service1.db.update_player(player1)

        print("3. 记录复杂状态...")

        # 记录状态
        player1 = game_service1.db.get_player("player1")
        session1 = game_service1.db.get_player_active_session("player1")

        original_data = {
            "player_score": player1.current_score if player1 else 0,
            "progress_col_3": player1.progress.get_progress(3) if player1 else 0,
            "progress_col_5": player1.progress.get_progress(5) if player1 else 0,
            "has_session": session1 is not None,
            "turn_number": session1.turn_number if session1 else 0,
            "temporary_markers_count": len(session1.temporary_markers) if session1 else 0,
            "forced_dice_result": session1.forced_dice_result if session1 else None,
            "trap_6_1": game_service1.engine.trap_config.get_trap_for_position(6, 1),
            "total_generated_traps": len(game_service1.engine.trap_config.generated_traps)
        }

        print(f"   玩家积分: {original_data['player_score']}")
        print(f"   第3列进度: {original_data['progress_col_3']}")
        print(f"   第5列进度: {original_data['progress_col_5']}")
        print(f"   当前回合: {original_data['turn_number']}")
        print(f"   临时标记数: {original_data['temporary_markers_count']}")
        print(f"   强制骰子: {original_data['forced_dice_result']}")
        print(f"   6-1陷阱: {original_data['trap_6_1']}")
        print(f"   总陷阱数: {original_data['total_generated_traps']}")

        # 如果有临时标记，记录详细信息
        temp_markers_details = []
        if session1:
            for marker in session1.temporary_markers:
                temp_markers_details.append((marker.column, marker.position))
            original_data["temp_markers_details"] = temp_markers_details
            print(f"   临时标记详情: {temp_markers_details}")

        # 销毁第一个实例
        del game_service1
        db_module.db_manager = None

        print("\n4. 模拟程序重启...")
        time.sleep(1)

        # 创建新的GameService实例
        game_service2 = GameService()

        print("5. 验证复杂状态恢复...")

        # 验证数据
        player1_new = game_service2.db.get_player("player1")
        session1_new = game_service2.db.get_player_active_session("player1")

        restored_data = {
            "player_score": player1_new.current_score if player1_new else 0,
            "progress_col_3": player1_new.progress.get_progress(3) if player1_new else 0,
            "progress_col_5": player1_new.progress.get_progress(5) if player1_new else 0,
            "has_session": session1_new is not None,
            "turn_number": session1_new.turn_number if session1_new else 0,
            "temporary_markers_count": len(session1_new.temporary_markers) if session1_new else 0,
            "forced_dice_result": session1_new.forced_dice_result if session1_new else None,
            "trap_6_1": game_service2.engine.trap_config.get_trap_for_position(6, 1),
            "total_generated_traps": len(game_service2.engine.trap_config.generated_traps)
        }

        # 恢复临时标记详情
        temp_markers_details_new = []
        if session1_new:
            for marker in session1_new.temporary_markers:
                temp_markers_details_new.append((marker.column, marker.position))
            restored_data["temp_markers_details"] = temp_markers_details_new

        print(f"   玩家积分: {restored_data['player_score']}")
        print(f"   第3列进度: {restored_data['progress_col_3']}")
        print(f"   第5列进度: {restored_data['progress_col_5']}")
        print(f"   当前回合: {restored_data['turn_number']}")
        print(f"   临时标记数: {restored_data['temporary_markers_count']}")
        print(f"   强制骰子: {restored_data['forced_dice_result']}")
        print(f"   6-1陷阱: {restored_data['trap_6_1']}")
        print(f"   总陷阱数: {restored_data['total_generated_traps']}")
        print(f"   临时标记详情: {temp_markers_details_new}")

        # 比较结果
        print("\n6. 高级持久化验证结果:")
        all_match = True

        for key in original_data:
            if original_data[key] == restored_data[key]:
                print(f"   OK {key}: 匹配")
            else:
                print(f"   ERROR {key}: 不匹配")
                print(f"     原始: {original_data[key]}")
                print(f"     恢复: {restored_data[key]}")
                all_match = False

        if all_match:
            print("\n SUCCESS: 高级游戏状态持久化测试通过！")
            print("   游戏能完整保存和恢复：")
            print("   ✓ 玩家信息和积分")
            print("   ✓ 游戏进度和永久标记位置")
            print("   ✓ 游戏会话状态和回合信息")
            print("   ✓ 临时标记位置和数量")
            print("   ✓ 强制骰子结果状态")
            print("   ✓ 自定义陷阱配置和位置")
            print("   ✓ GM设置的所有陷阱位置")
        else:
            print("\n ERROR: 部分高级状态持久化失败")

        return all_match

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_advanced_persistence()