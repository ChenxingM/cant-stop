"""
Can't Stop游戏CLI界面
"""

import click
from typing import Optional, List
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.game_service import GameService
from src.config.config_manager import get_config


class CantStopCLI:
    """Can't Stop CLI游戏界面"""

    def __init__(self):
        self.game_service = GameService()
        self.current_player_id: Optional[str] = None
        self.current_username: Optional[str] = None

    def welcome(self):
        """显示欢迎信息"""
        print("=" * 50)
        print("欢迎来到Can't Stop贪骰无厌游戏！")
        print("=" * 50)
        print("输入 'help' 查看帮助")
        print("输入 'quit' 退出游戏")
        print()

    def show_help(self):
        """显示帮助信息"""
        dice_cost = get_config("game_config", "game.dice_cost", 10)
        help_text = f"""
游戏指令帮助
================

玩家管理
-----------
register <用户名> <阵营>  - 注册新玩家（阵营：收养人/Aonreth）
login <用户ID>           - 登录已存在的玩家
status                   - 查看当前玩家状态

游戏操作
-----------
start                    - 开始新游戏
roll / 掷骰             - 掷骰子
move <数字1,数字2>       - 移动标记（如：move 8,13）
move <数字>             - 移动单个标记（如：move 8）
end / 替换永久棋子       - 主动结束回合
continue                 - 继续当前回合
checkin / 打卡完毕       - 完成打卡

信息查询
-----------
progress / 查看当前进度  - 查看游戏进度
leaderboard / 排行榜     - 查看排行榜

积分管理
-----------
add_score <类型>         - 添加积分
                          类型：草图/精致小图/精草大图/精致大图/超常发挥

GM管理
-----------
reset_all                - 重置所有玩家游戏数据（保留用户名和阵营）
trap_config              - 查看当前陷阱配置
set_trap <陷阱名> <列号>  - 设置陷阱位置（如：set_trap 小小火球术 3,4,5）
regenerate_traps         - 重新生成陷阱位置

游戏规则提示
===============
- 每回合消耗{dice_cost}积分掷骰
- 将6个骰子分成两组，每组3个
- 最多同时放置3个临时标记
- 在3列登顶即可获胜
- 主动结束回合后需要打卡才能继续

输入 'quit' 退出游戏
        """
        print(help_text)

    def parse_move_command(self, command: str) -> Optional[List[int]]:
        """解析移动指令"""
        try:
            # 移除move前缀
            if command.startswith('move '):
                numbers_str = command[5:].strip()
            else:
                numbers_str = command.strip()

            # 解析数字
            if ',' in numbers_str:
                # 双数字
                parts = numbers_str.split(',')
                if len(parts) == 2:
                    return [int(parts[0].strip()), int(parts[1].strip())]
            else:
                # 单数字
                return [int(numbers_str)]

            return None
        except ValueError:
            return None

    def run_command(self, command: str) -> bool:
        """运行单个指令"""
        command = command.strip().lower()

        if not command:
            return True

        if command == 'quit' or command == 'exit':
            print("再见！感谢游玩Can't Stop！")
            return False

        elif command == 'help':
            self.show_help()

        elif command.startswith('register '):
            parts = command.split()
            if len(parts) >= 3:
                username = parts[1]
                faction = parts[2]
                if faction not in ['收养人', 'aonreth']:
                    faction = '收养人' if faction == '收养人' else 'Aonreth'

                # 使用用户名作为ID
                success, message = self.game_service.register_player(username, username, faction)
                print(f"{'OK' if success else 'ERROR'} {message}")

                if success:
                    self.current_player_id = username
                    self.current_username = username
            else:
                print("❌ 格式错误！使用：register <用户名> <阵营>")

        elif command.startswith('login '):
            parts = command.split()
            if len(parts) >= 2:
                player_id = parts[1]
                player = self.game_service.db.get_player(player_id)
                if player:
                    self.current_player_id = player_id
                    self.current_username = player.username
                    print(f"✅ 登录成功！欢迎回来，{player.username}")
                else:
                    print("❌ 玩家不存在")
            else:
                print("❌ 格式错误！使用：login <用户ID>")

        elif command in ['start', '轮次开始']:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.start_new_game(self.current_player_id)
            print(f"{'OK' if success else 'ERROR'} {message}")

        elif command in ['roll', '掷骰', '.r6d6']:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message, combinations = self.game_service.roll_dice(self.current_player_id)
            print(f"{'DICE' if success else 'ERROR'} {message}")

        elif command.startswith('move ') or command.replace(',', '').isdigit():
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            target_columns = self.parse_move_command(command)
            if target_columns:
                success, message = self.game_service.move_markers(self.current_player_id, target_columns)
                print(f"{'OK' if success else 'ERROR'} {message}")
            else:
                print("❌ 格式错误！使用：move 8,13 或 move 8")

        elif command in ['end', '替换永久棋子']:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.end_turn(self.current_player_id)
            print(f"{'OK' if success else 'ERROR'} {message}")

        elif command in ['continue', '继续']:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.continue_turn(self.current_player_id)
            print(f"{'OK' if success else 'ERROR'} {message}")

        elif command in ['checkin', '打卡完毕']:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.complete_checkin(self.current_player_id)
            print(f"{'OK' if success else 'ERROR'} {message}")

        elif command in ['status', 'progress', '查看当前进度']:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.get_game_status(self.current_player_id)
            print(message)

        elif command in ['leaderboard', '排行榜']:
            success, message = self.game_service.get_leaderboard()
            print(message)

        elif command.startswith('add_score '):
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            parts = command.split(' ', 1)
            if len(parts) >= 2:
                score_type = parts[1]
                success, message = self.game_service.add_score(self.current_player_id, 0, score_type)
                print(f"{'OK' if success else 'ERROR'} {message}")
            else:
                print("❌ 格式错误！使用：add_score <类型>")

        elif command == 'reset_all':
            print("⚠️  即将重置所有玩家的游戏数据，是否确认？(y/N): ", end='')
            confirm = input().strip().lower()
            if confirm == 'y' or confirm == 'yes':
                success, message = self.game_service.reset_all_game_data()
                print(f"{'OK' if success else 'ERROR'} {message}")
            else:
                print("❌ 操作已取消")

        elif command == 'trap_config':
            success, message = self.game_service.get_trap_config_info()
            print(message)

        elif command.startswith('set_trap '):
            parts = command.split(' ', 2)
            if len(parts) >= 3:
                trap_name = parts[1]
                columns_str = parts[2]
                try:
                    # 解析列号
                    if ',' in columns_str:
                        columns = [int(x.strip()) for x in columns_str.split(',')]
                    else:
                        columns = [int(columns_str.strip())]

                    success, message = self.game_service.set_trap_config(trap_name, columns)
                    print(f"{'OK' if success else 'ERROR'} {message}")
                except ValueError:
                    print("❌ 列号格式错误！使用数字和逗号分隔（如：3,4,5）")
            else:
                print("❌ 格式错误！使用：set_trap <陷阱名> <列号>")

        elif command == 'regenerate_traps':
            success, message = self.game_service.regenerate_traps()
            print(f"{'OK' if success else 'ERROR'} {message}")

        else:
            # 尝试解析为纯数字组合
            if ',' in command or command.isdigit():
                target_columns = self.parse_move_command(command)
                if target_columns and self.current_player_id:
                    success, message = self.game_service.move_markers(self.current_player_id, target_columns)
                    print(f"{'OK' if success else 'ERROR'} {message}")
                else:
                    print("❌ 未知指令！输入 'help' 查看帮助")
            else:
                print("❌ 未知指令！输入 'help' 查看帮助")

        return True

    def run(self):
        """运行CLI主循环"""
        self.welcome()

        try:
            while True:
                # 显示当前玩家信息
                prompt = f"[{self.current_username or '未登录'}] > "
                command = input(prompt)

                if not self.run_command(command):
                    break

        except KeyboardInterrupt:
            print("\n游戏退出！")
        except EOFError:
            print("\n游戏退出！")


@click.command()
@click.option('--demo', is_flag=True, help='运行演示模式')
def main(demo):
    """Can't Stop游戏CLI入口"""
    cli = CantStopCLI()

    if demo:
        print("🎮 演示模式")
        print("-" * 30)

        # 演示注册和游戏流程
        demo_commands = [
            "register 测试玩家 收养人",
            "start",
            "roll",
            "help"
        ]

        for cmd in demo_commands:
            print(f"> {cmd}")
            cli.run_command(cmd)
            print()

        print("演示结束，输入任意键继续...")
        input()

    cli.run()


if __name__ == "__main__":
    main()