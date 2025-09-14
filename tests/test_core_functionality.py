"""
核心功能测试套件
包含游戏引擎、陷阱系统、持久化等核心功能的测试
"""

import sys
import os
import time
import asyncio

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.game_service import GameService
from src.services.message_processor import MessageProcessor, UserMessage


class CoreFunctionalityTests:
    """核心功能测试类"""

    def __init__(self):
        self.game_service = None
        self.message_processor = None

    def setup(self):
        """测试设置"""
        # 重置数据库管理器
        import src.database.database as db_module
        db_module.db_manager = None

        self.game_service = GameService()
        self.message_processor = MessageProcessor()

        # 确保测试环境干净
        self.game_service.db.drop_tables()
        self.game_service.db.create_tables()

    def test_basic_game_flow(self):
        """测试基本游戏流程"""
        print("测试基本游戏流程...")

        # 注册玩家
        success, msg = self.game_service.register_player("test", "测试玩家", "收养人")
        assert success, f"注册失败: {msg}"

        # 添加积分
        success, msg = self.game_service.add_score("test", 100, "测试积分")
        assert success, f"添加积分失败: {msg}"

        # 开始游戏
        success, msg = self.game_service.start_new_game("test")
        assert success, f"开始游戏失败: {msg}"

        # 掷骰子
        success, msg, combinations = self.game_service.roll_dice("test")
        assert success, f"掷骰失败: {msg}"
        assert combinations, "没有获得骰子组合"

        print("基本游戏流程测试通过")
        return True

    def test_trap_system(self):
        """测试陷阱系统"""
        print("测试陷阱系统...")

        # 设置陷阱
        success, msg = self.game_service.set_manual_trap("小小火球术", 5, 1)
        assert success, f"设置陷阱失败: {msg}"

        # 验证陷阱配置
        trap_name = self.game_service.engine.trap_config.get_trap_for_position(5, 1)
        assert trap_name == "小小火球术", f"陷阱配置错误: {trap_name}"

        # 验证陷阱在map_events中
        trap_key = "5_1"
        assert trap_key in self.game_service.engine.map_events, "陷阱未加载到事件系统"

        print("陷阱系统测试通过")
        return True

    def test_persistence(self):
        """测试数据持久化"""
        print("测试数据持久化...")

        # 创建初始状态
        self.game_service.register_player("persist_test", "持久化测试", "Aonreth")
        self.game_service.add_score("persist_test", 150, "测试积分")
        self.game_service.start_new_game("persist_test")
        self.game_service.set_manual_trap("不要回头", 7, 2)

        # 记录状态
        player = self.game_service.db.get_player("persist_test")
        original_score = player.current_score
        original_faction = player.faction.value

        # 模拟重启
        del self.game_service
        import src.database.database as db_module
        db_module.db_manager = None

        time.sleep(0.1)
        self.game_service = GameService()

        # 验证状态恢复
        player_restored = self.game_service.db.get_player("persist_test")
        assert player_restored is not None, "玩家数据未恢复"
        assert player_restored.current_score == original_score, f"积分未恢复: {player_restored.current_score} != {original_score}"
        assert player_restored.faction.value == original_faction, f"阵营未恢复: {player_restored.faction.value} != {original_faction}"

        # 验证陷阱配置恢复
        trap_name = self.game_service.engine.trap_config.get_trap_for_position(7, 2)
        assert trap_name == "不要回头", f"陷阱配置未恢复: {trap_name}"

        print("数据持久化测试通过")
        return True

    async def test_message_processing(self):
        """测试消息处理"""
        print("测试消息处理...")

        # 测试基本指令
        test_cases = [
            ("帮助", "游戏指令帮助"),
            ("排行榜", "排行榜"),
            ("1", "土地神"),  # 陷阱选择（1不是有效列号，会被识别为陷阱选择）
            ("我没掉", "土地神"),  # 陷阱选择文字
        ]

        for input_text, expected_keyword in test_cases:
            message = UserMessage(
                user_id="test",
                username="测试",
                content=input_text
            )

            response = await self.message_processor.process_message(message)
            assert expected_keyword in response.content, f"指令 '{input_text}' 处理失败，期望包含 '{expected_keyword}'"

        print("消息处理测试通过")
        return True

    def run_all_tests(self):
        """运行所有测试"""
        print("=== 核心功能测试套件 ===\n")

        self.setup()

        tests = [
            ("基本游戏流程", self.test_basic_game_flow),
            ("陷阱系统", self.test_trap_system),
            ("数据持久化", self.test_persistence),
            ("消息处理", lambda: asyncio.run(self.test_message_processing())),
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

        print(f"=== 测试完成 ===")
        print(f"通过: {passed}/{total}")

        if passed == total:
            print("所有核心功能测试通过！")
            return True
        else:
            print("X 部分测试失败")
            return False


if __name__ == "__main__":
    test_suite = CoreFunctionalityTests()
    test_suite.run_all_tests()