"""
测试游戏状态持久化
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_persistence():
    """测试游戏状态持久化"""
    try:
        from src.services.game_service import GameService

        print("=== 游戏状态持久化测试 ===")

        print("\n1. 初始化第一个GameService实例...")
        game_service1 = GameService()

        # 创建测试数据
        print("2. 创建测试数据...")

        # 注册玩家
        success, msg = game_service1.register_player("player1", "测试玩家1", "收养人")
        print(f"   注册玩家1: {success}")

        success, msg = game_service1.register_player("player2", "测试玩家2", "Aonreth")
        print(f"   注册玩家2: {success}")

        # 给玩家添加积分
        game_service1.add_score("player1", 100, "测试积分")
        game_service1.add_score("player2", 150, "测试积分")

        # 开始游戏
        game_service1.start_new_game("player1")

        # 设置陷阱
        game_service1.set_manual_trap("小小火球术", 8, 2)
        game_service1.set_manual_trap("不要回头", 10, 3)

        print("3. 记录第一次的状态...")

        # 记录状态
        player1 = game_service1.db.get_player("player1")
        player2 = game_service1.db.get_player("player2")
        session1 = game_service1.db.get_player_active_session("player1")

        original_data = {
            "player1_score": player1.current_score if player1 else 0,
            "player1_faction": player1.faction.value if player1 else "",
            "player2_score": player2.current_score if player2 else 0,
            "player2_faction": player2.faction.value if player2 else "",
            "has_active_session": session1 is not None,
            "trap_8_2": game_service1.engine.trap_config.get_trap_for_position(8, 2),
            "trap_10_3": game_service1.engine.trap_config.get_trap_for_position(10, 3),
            "total_traps": len(game_service1.engine.trap_config.generated_traps)
        }

        print(f"   玩家1积分: {original_data['player1_score']}")
        print(f"   玩家1阵营: {original_data['player1_faction']}")
        print(f"   玩家2积分: {original_data['player2_score']}")
        print(f"   玩家2阵营: {original_data['player2_faction']}")
        print(f"   是否有活跃会话: {original_data['has_active_session']}")
        print(f"   8-2位置陷阱: {original_data['trap_8_2']}")
        print(f"   10-3位置陷阱: {original_data['trap_10_3']}")
        print(f"   总陷阱数量: {original_data['total_traps']}")

        # 销毁第一个实例
        del game_service1

        print("\n4. 等待一秒后创建新的GameService实例...")
        time.sleep(1)

        # 创建新的GameService实例
        game_service2 = GameService()

        print("5. 检查数据持久化...")

        # 验证数据
        player1_new = game_service2.db.get_player("player1")
        player2_new = game_service2.db.get_player("player2")
        session1_new = game_service2.db.get_player_active_session("player1")

        restored_data = {
            "player1_score": player1_new.current_score if player1_new else 0,
            "player1_faction": player1_new.faction.value if player1_new else "",
            "player2_score": player2_new.current_score if player2_new else 0,
            "player2_faction": player2_new.faction.value if player2_new else "",
            "has_active_session": session1_new is not None,
            "trap_8_2": game_service2.engine.trap_config.get_trap_for_position(8, 2),
            "trap_10_3": game_service2.engine.trap_config.get_trap_for_position(10, 3),
            "total_traps": len(game_service2.engine.trap_config.generated_traps)
        }

        print(f"   玩家1积分: {restored_data['player1_score']}")
        print(f"   玩家1阵营: {restored_data['player1_faction']}")
        print(f"   玩家2积分: {restored_data['player2_score']}")
        print(f"   玩家2阵营: {restored_data['player2_faction']}")
        print(f"   是否有活跃会话: {restored_data['has_active_session']}")
        print(f"   8-2位置陷阱: {restored_data['trap_8_2']}")
        print(f"   10-3位置陷阱: {restored_data['trap_10_3']}")
        print(f"   总陷阱数量: {restored_data['total_traps']}")

        # 比较结果
        print("\n6. 持久化验证结果:")
        all_match = True

        for key in original_data:
            if original_data[key] == restored_data[key]:
                print(f"   ✓ {key}: 匹配")
            else:
                print(f"   ✗ {key}: 不匹配 ({original_data[key]} != {restored_data[key]})")
                all_match = False

        if all_match:
            print("\n🎉 所有数据持久化测试通过！")
            print("   游戏在重启后能完全恢复之前的状态")
        else:
            print("\n❌ 部分数据持久化失败")

        return all_match

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_persistence()