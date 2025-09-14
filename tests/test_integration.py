"""
集成测试套件
测试完整的游戏场景和组件集成
"""

import sys
import os
import asyncio

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.game_service import GameService


class IntegrationTests:
    """集成测试类"""

    def __init__(self):
        self.game_service = None

    def setup(self):
        """测试设置"""
        import src.database.database as db_module
        db_module.db_manager = None

        self.game_service = GameService()
        self.game_service.db.drop_tables()
        self.game_service.db.create_tables()

    def test_complete_game_scenario(self):
        """测试完整游戏场景"""
        print("测试完整游戏场景...")

        try:
            # 场景1: 玩家注册和游戏开始
            success, msg = self.game_service.register_player("player1", "玩家一", "收养人")
            assert success, f"注册失败: {msg}"

            success, msg = self.game_service.add_score("player1", 200, "初始积分")
            assert success, f"添加积分失败: {msg}"

            success, msg = self.game_service.start_new_game("player1")
            assert success, f"开始游戏失败: {msg}"

            # 场景2: GM设置陷阱
            success, msg = self.game_service.set_manual_trap("小小火球术", 6, 1)
            assert success, f"设置陷阱失败: {msg}"

            # 场景3: 游戏循环
            for round_num in range(3):
                # 掷骰子
                success, msg, combinations = self.game_service.roll_dice("player1")
                if not success:
                    self.game_service.add_score("player1", 20, "补充积分")
                    continue

                assert combinations, f"第{round_num+1}轮没有获得骰子组合"

                # 选择并移动
                first_combo = combinations[0]
                success, move_msg = self.game_service.move_markers("player1", list(first_combo))

                # 移动可能因为陷阱或其他原因失败，这是正常的
                print(f"第{round_num+1}轮移动: {success}")

                if success:
                    # 检查状态
                    success, status = self.game_service.get_game_status("player1")
                    assert success, "获取状态失败"

                    # 可能需要结束回合
                    if "剩余可放置标记：0" in move_msg:
                        success, end_msg = self.game_service.end_turn("player1")
                        if success:
                            # 打卡
                            success, checkin_msg = self.game_service.complete_checkin("player1")

                self.game_service.add_score("player1", 15, "回合奖励")

            print("完整游戏场景测试通过")
            return True

        except Exception as e:
            print(f"完整游戏场景测试失败: {e}")
            return False

    def test_multi_player_scenario(self):
        """测试多玩家场景"""
        print("测试多玩家场景...")

        try:
            # 注册多个玩家
            players = [
                ("player1", "玩家一", "收养人"),
                ("player2", "玩家二", "Aonreth"),
                ("player3", "玩家三", "收养人")
            ]

            for player_id, username, faction in players:
                success, msg = self.game_service.register_player(player_id, username, faction)
                assert success, f"注册{username}失败: {msg}"

                success, msg = self.game_service.add_score(player_id, 100, "初始积分")
                assert success, f"给{username}添加积分失败: {msg}"

            # 检查排行榜
            success, leaderboard = self.game_service.get_leaderboard(10)
            assert success, "获取排行榜失败"
            assert "玩家一" in leaderboard, "排行榜中缺少玩家"

            # 测试每个玩家都能开始游戏
            for player_id, username, _ in players:
                success, msg = self.game_service.start_new_game(player_id)
                assert success, f"{username}开始游戏失败: {msg}"

                # 简单验证状态
                success, status = self.game_service.get_game_status(player_id)
                assert success, f"获取{username}状态失败"
                assert username in status, "状态中缺少玩家名称"

            print("多玩家场景测试通过")
            return True

        except Exception as e:
            print(f"多玩家场景测试失败: {e}")
            return False

    def test_trap_interaction_scenarios(self):
        """测试陷阱交互场景"""
        print("测试陷阱交互场景...")

        try:
            # 注册玩家
            self.game_service.register_player("trap_test", "陷阱测试", "收养人")
            self.game_service.add_score("trap_test", 300, "测试积分")
            self.game_service.start_new_game("trap_test")

            # 设置不同类型的陷阱
            trap_configs = [
                ("小小火球术", 5, 1),
                ("不要回头", 7, 2),
                ("河..土地神", 9, 1),
            ]

            for trap_name, column, position in trap_configs:
                success, msg = self.game_service.set_manual_trap(trap_name, column, position)
                assert success, f"设置陷阱{trap_name}失败: {msg}"

            # 验证陷阱清除功能
            success, msg = self.game_service.remove_trap_at_position(9, 1)
            assert success, f"清除陷阱失败: {msg}"

            # 验证陷阱重新生成
            success, msg = self.game_service.regenerate_traps()
            assert success, f"重新生成陷阱失败: {msg}"

            # 验证陷阱配置信息
            success, info = self.game_service.get_trap_config_info()
            assert success, f"获取陷阱配置信息失败: {info}"
            assert "陷阱配置" in info, "陷阱配置信息格式错误"

            print("陷阱交互场景测试通过")
            return True

        except Exception as e:
            print(f"陷阱交互场景测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有集成测试"""
        print("=== 集成测试套件 ===\n")

        self.setup()

        tests = [
            ("完整游戏场景", self.test_complete_game_scenario),
            ("多玩家场景", self.test_multi_player_scenario),
            ("陷阱交互场景", self.test_trap_interaction_scenarios),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                print(f"运行测试: {test_name}")
                result = test_func()
                if result:
                    passed += 1
                    print(f"+ {test_name} 通过\n")
                else:
                    print(f"- {test_name} 失败\n")
            except Exception as e:
                print(f"! {test_name} 异常: {e}\n")

        print(f"=== 集成测试完成 ===")
        print(f"通过: {passed}/{total}")

        if passed == total:
            print("所有集成测试通过！")
            return True
        else:
            print("X 部分集成测试失败")
            return False


if __name__ == "__main__":
    test_suite = IntegrationTests()
    test_suite.run_all_tests()