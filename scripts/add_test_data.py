#!/usr/bin/env python3
"""
添加测试数据脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.database.database import get_db_manager
from src.models.game_models import Faction, Player, GameSession, TemporaryMarker, TurnState, GameState
from datetime import datetime

def add_test_data():
    """添加测试数据"""
    try:
        db = get_db_manager()

        # 检查是否已有玩家
        existing_players = db.get_all_active_players()
        if existing_players:
            print(f"已有 {len(existing_players)} 个玩家")

            # 为第一个玩家添加一些测试进度
            test_player = existing_players[0]
            print(f"为玩家 {test_player.username} 添加测试进度...")

            # 添加永久进度
            test_player.progress.set_progress(7, 3)  # 第7列进度3
            test_player.progress.set_progress(8, 2)  # 第8列进度2

            # 创建游戏会话
            session = GameSession(
                session_id=f"test_session_{test_player.player_id}",
                player_id=test_player.player_id,
                state=GameState.ACTIVE,
                turn_state=TurnState.MOVE_MARKERS,
                turn_number=3
            )

            # 添加临时标记
            session.temporary_markers = [
                TemporaryMarker(column=9, position=1),
                TemporaryMarker(column=10, position=2),
                TemporaryMarker(column=6, position=1)
            ]

            # 保存到数据库
            db.update_player(test_player)
            db.save_game_session(session)

            print("测试数据添加完成！")
            print(f"- 永久进度: 列7位置3, 列8位置2")
            print(f"- 临时标记: 列9位置1, 列10位置2, 列6位置1")

        else:
            print("没有找到玩家，请先注册玩家")

    except Exception as e:
        print(f"添加测试数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_data()