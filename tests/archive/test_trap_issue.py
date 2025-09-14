"""
测试陷阱触发问题
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_trap_issue():
    """测试陷阱触发问题"""
    try:
        from src.services.game_service import GameService

        print("=== 测试陷阱触发问题 ===")

        # 重置数据库
        import src.database.database as db_module
        db_module.db_manager = None

        game_service = GameService()
        game_service.db.drop_tables()
        game_service.db.create_tables()

        # 注册玩家
        game_service.register_player("mcx", "mcx", "收养人")
        game_service.add_score("mcx", 200, "测试积分")
        game_service.start_new_game("mcx")

        print("1. 当前陷阱配置:")
        for pos, trap_name in game_service.engine.trap_config.generated_traps.items():
            print(f"   {pos}: {trap_name}")

        # 检查第10列的陷阱
        trap_10_3 = game_service.engine.trap_config.get_trap_for_position(10, 3)
        print(f"   第10列第3位陷阱: {trap_10_3}")

        # 模拟玩家移动到第10列第2位
        print("\n2. 模拟游戏进程:")

        # 第一次掷骰，移动到8列和10列
        print("   掷骰并移动到第8列和第10列...")
        success, message, combinations = game_service.roll_dice("mcx")
        print(f"   掷骰结果: {success}")

        # 强制移动到第8列和第10列
        if success:
            # 直接调用移动方法
            success, move_message = game_service.move_markers("mcx", [8, 10])
            print(f"   移动到8,10列: {success}")

            if success:
                # 检查当前临时标记状态
                session = game_service.db.get_player_active_session("mcx")
                if session:
                    print(f"   临时标记数量: {len(session.temporary_markers)}")
                    for marker in session.temporary_markers:
                        print(f"     第{marker.column}列-位置{marker.position}")

        # 第二次掷骰，移动第10列到位置2
        print("   第二次掷骰...")
        success, message, combinations = game_service.roll_dice("mcx")
        if success:
            # 强制移动第10列
            success, move_message = game_service.move_markers("mcx", [10, 16])  # 假设16列存在
            print(f"   移动到10,16列: {success}")

            if success:
                session = game_service.db.get_player_active_session("mcx")
                if session:
                    print(f"   临时标记数量: {len(session.temporary_markers)}")
                    for marker in session.temporary_markers:
                        player = game_service.db.get_player("mcx")
                        total_pos = player.progress.get_progress(marker.column) + marker.position
                        print(f"     第{marker.column}列-位置{marker.position}(总位置{total_pos})")

        print("\n3. 结束回合(替换永久棋子)...")
        success, end_message = game_service.end_turn("mcx")
        print(f"   结束回合: {success}")
        print(f"   消息: {repr(end_message)}")

        # 检查永久进度
        player = game_service.db.get_player("mcx")
        if player:
            print(f"   永久进度:")
            for col, progress in player.progress.permanent_progress.items():
                if progress > 0:
                    print(f"     第{col}列: 进度{progress}")

        print("\n4. 完成打卡...")
        success, checkin_message = game_service.complete_checkin("mcx")
        print(f"   打卡结果: {success}")
        print(f"   打卡消息: {repr(checkin_message)}")

        # 再次检查永久进度
        player = game_service.db.get_player("mcx")
        if player:
            print(f"   打卡后永久进度:")
            for col, progress in player.progress.permanent_progress.items():
                if progress > 0:
                    print(f"     第{col}列: 进度{progress}")

        print("\n5. 问题分析:")
        if player:
            col_10_progress = player.progress.get_progress(10)
            print(f"   第10列进度: {col_10_progress}")
            if col_10_progress == 0:
                print("   ERROR: 第10列进度被错误清除！")
            else:
                print("   OK: 第10列进度正常")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trap_issue()