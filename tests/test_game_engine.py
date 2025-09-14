"""
游戏引擎测试
"""

import pytest
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.game_engine import GameEngine
from src.models.game_models import Faction, Player, GameSession, DiceRoll
from src.utils.exceptions import *


class TestGameEngine:
    """游戏引擎测试类"""

    def setup_method(self):
        """测试前设置"""
        self.engine = GameEngine()

    def test_create_player(self):
        """测试创建玩家"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )

        assert player.player_id == "test_player"
        assert player.username == "测试玩家"
        assert player.faction == Faction.ADOPTER
        assert player.current_score == 0

    def test_create_duplicate_player(self):
        """测试创建重复玩家"""
        self.engine.create_player("test_player", "测试玩家", Faction.ADOPTER)

        with pytest.raises(ValueError):
            self.engine.create_player("test_player", "另一个玩家", Faction.AONRETH)

    def test_create_game_session(self):
        """测试创建游戏会话"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        session = self.engine.create_game_session("test_player")

        assert session.player_id == "test_player"
        assert session.turn_number == 1
        assert session.first_turn is True
        assert len(session.temporary_markers) == 0

    def test_roll_dice(self):
        """测试掷骰"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        player.add_score(20, "测试")  # 添加积分

        session = self.engine.create_game_session("test_player")
        dice_roll = self.engine.roll_dice(session.session_id)

        assert len(dice_roll.results) == 6
        assert all(1 <= r <= 6 for r in dice_roll.results)
        assert player.current_score == 10  # 消耗了10积分

    def test_roll_dice_insufficient_score(self):
        """测试积分不足时掷骰"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        session = self.engine.create_game_session("test_player")

        with pytest.raises(ValueError, match="积分不足"):
            self.engine.roll_dice(session.session_id)

    def test_dice_combinations(self):
        """测试骰子组合"""
        dice_roll = DiceRoll(results=[1, 2, 3, 4, 5, 6])
        combinations = dice_roll.get_possible_combinations()

        # 检查是否包含预期的组合
        assert len(combinations) > 0
        assert all(isinstance(combo, tuple) for combo in combinations)
        assert all(len(combo) == 2 for combo in combinations)

    def test_move_markers_valid(self):
        """测试有效的标记移动"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        player.add_score(20, "测试")

        session = self.engine.create_game_session("test_player")

        # 模拟特定的骰子结果
        dice_roll = DiceRoll(results=[1, 2, 3, 4, 5, 6])
        session.current_dice = dice_roll

        # 测试移动标记
        combinations = dice_roll.get_possible_combinations()
        if combinations:
            first_combo = list(combinations[0])
            success, message = self.engine.move_markers(session.session_id, first_combo)
            assert success

    def test_move_markers_invalid_combination(self):
        """测试无效的骰子组合移动"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        session = self.engine.create_game_session("test_player")

        # 设置特定骰子结果
        dice_roll = DiceRoll(results=[1, 1, 1, 1, 1, 1])
        session.current_dice = dice_roll

        # 尝试移动无效组合
        can_move, message = self.engine.can_move_markers(session.session_id, [10, 15])
        assert not can_move

    def test_end_turn_actively(self):
        """测试主动结束轮次"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        player.add_score(20, "测试")

        session = self.engine.create_game_session("test_player")

        # 添加一些临时标记
        session.add_temporary_marker(7, 2)
        session.add_temporary_marker(10, 3)

        success, message = self.engine.end_turn_actively(session.session_id)
        assert success
        assert session.needs_checkin is True

        # 检查进度是否被保存
        assert player.progress.get_progress(7) == 2
        assert player.progress.get_progress(10) == 3

    def test_complete_checkin(self):
        """测试完成打卡"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        session = self.engine.create_game_session("test_player")

        # 设置需要打卡状态
        session.needs_checkin = True

        success = self.engine.complete_checkin(session.session_id)
        assert success
        assert session.needs_checkin is False

    def test_winning_condition(self):
        """测试获胜条件"""
        player = self.engine.create_player(
            "test_player", "测试玩家", Faction.ADOPTER
        )
        session = self.engine.create_game_session("test_player")

        # 设置三列完成状态
        player.progress.set_progress(3, 3)  # 第3列完成
        player.progress.set_progress(4, 4)  # 第4列完成
        player.progress.set_progress(5, 5)  # 第5列完成

        assert player.progress.is_winner()
        assert player.progress.get_completed_count() == 3


class TestDiceRoll:
    """骰子测试类"""

    def test_valid_dice_roll(self):
        """测试有效的骰子投掷"""
        dice_roll = DiceRoll(results=[1, 2, 3, 4, 5, 6])
        assert len(dice_roll.results) == 6
        assert all(1 <= r <= 6 for r in dice_roll.results)

    def test_invalid_dice_count(self):
        """测试无效的骰子数量"""
        with pytest.raises(ValueError, match="骰子结果必须是6个数字"):
            DiceRoll(results=[1, 2, 3])

    def test_invalid_dice_values(self):
        """测试无效的骰子值"""
        with pytest.raises(ValueError, match="每个骰子结果必须在1-6之间"):
            DiceRoll(results=[0, 1, 2, 3, 4, 5])

    def test_combinations_generation(self):
        """测试组合生成"""
        dice_roll = DiceRoll(results=[1, 1, 1, 6, 6, 6])
        combinations = dice_roll.get_possible_combinations()

        # 应该包含 (3,18) 和 (9,12) 等组合
        combo_sums = set(combinations)
        assert (3, 18) in combo_sums  # 1+1+1=3, 6+6+6=18


class TestMapConfig:
    """地图配置测试类"""

    def test_column_lengths(self):
        """测试列长度配置"""
        from src.models.game_models import MapConfig

        config = MapConfig()

        # 测试一些已知的列长度
        assert config.get_column_length(3) == 3
        assert config.get_column_length(10) == 10
        assert config.get_column_length(11) == 10
        assert config.get_column_length(18) == 3

    def test_valid_columns(self):
        """测试有效列号"""
        from src.models.game_models import MapConfig

        config = MapConfig()

        # 有效列号
        for col in range(3, 19):
            assert config.is_valid_column(col)

        # 无效列号
        assert not config.is_valid_column(2)
        assert not config.is_valid_column(19)
        assert not config.is_valid_column(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])