"""
Can't Stop游戏CLI界面
"""

import click
from typing import Optional, List
import sys
import os
import re

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
🤖 CantStop 机器人指令完整手册
====================================

🎮 游戏开始
-----------
选择阵营：xxx            - 选择游戏阵营（收养人/Aonreth）

🎲 游戏进行阶段
--------------
轮次开始                 - 开始新轮次
.r6d6                   - 掷骰子（消耗{dice_cost}积分）
a,b                     - 记录双数值（移动两个标记）
a                       - 记录单数值（移动一个标记）
替换永久棋子             - 主动结束轮次
查看当前进度             - 查看游戏状态
打卡完毕                 - 恢复游戏功能

🏆 奖励系统
----------
领取（类型）奖励n        - 普通打卡奖励
我超级满意这张图n        - 超常发挥奖励（+30积分）

🛒 道具商店系统
--------------
道具商店                 - 查看商店
购买丑喵玩偶             - 购买玩偶（150积分）
捏捏丑喵玩偶             - 使用玩偶（每天3次）
添加xxx到道具商店        - 上架道具

📊 查询功能
----------
排行榜                   - 查看玩家排行榜

🔧 系统管理（仅管理员）
-------------------
reset_all                - 重置所有游戏数据
trap_config              - 查看陷阱配置
set_trap <陷阱名> <列号>  - 设置陷阱
regenerate_traps         - 重新生成陷阱

⚠️ 重要提醒
-----------
• 输入指令时不要包含【】符号
• 指令必须完全按照格式输入
• 主动结束轮次后必须打卡才能继续
• 每轮最多在3列上使用临时标记

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

        elif command.startswith('选择阵营：'):
            faction_part = command[5:].strip()  # 移除"选择阵营："
            if faction_part in ['收养人', 'Aonreth']:
                # 如果没有当前用户，提示需要先注册
                if not self.current_player_id:
                    print("请先使用 register <用户名> 指令注册")
                    return True

                # 更新用户阵营
                success, message = self.game_service.register_player(self.current_player_id, self.current_username, faction_part)
                if success:
                    print(f"您已选择阵营：{faction_part}，祝您玩得开心～")
                else:
                    print(f"ERROR {message}")
            else:
                print("❌ 格式错误！请输入：选择阵营：收养人 或 选择阵营：Aonreth")

        elif command.startswith('register '):
            parts = command.split()
            if len(parts) >= 2:
                username = parts[1]
                # 默认阵营，用户后续可通过"选择阵营"指令修改
                success, message = self.game_service.register_player(username, username, "收养人")

                if success:
                    self.current_player_id = username
                    self.current_username = username
                    print(f"注册成功！用户：{username}")
                    print("请使用 \"选择阵营：收养人\" 或 \"选择阵营：Aonreth\" 选择阵营")
                else:
                    print(f"ERROR {message}")
            else:
                print("❌ 格式错误！使用：register <用户名>")

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

        elif command == '轮次开始':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.start_new_game(self.current_player_id)
            if success:
                print("新轮次已开启")
            else:
                print(f"ERROR {message}")

        elif command == 'start':  # 保留原有指令兼容性
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.start_new_game(self.current_player_id)
            print(f"{'OK' if success else 'ERROR'} {message}")

        elif command == '.r6d6':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message, combinations = self.game_service.roll_dice(self.current_player_id)
            if success:
                print("好了好了，我要摇了...")
                print(message)
                print("-还算可以吧")
            else:
                print(f"ERROR {message}")

        elif command in ['roll', '掷骰']:  # 保留兼容性
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message, combinations = self.game_service.roll_dice(self.current_player_id)
            print(f"{'DICE' if success else 'ERROR'} {message}")

        elif command.startswith('move '):
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            target_columns = self.parse_move_command(command)
            if target_columns:
                success, message = self.game_service.move_markers(self.current_player_id, target_columns)
                if success:
                    if len(target_columns) == 2:
                        print(f"玩家选择记录数值：{target_columns[0]},{target_columns[1]}")
                    else:
                        print(f"玩家选择记录数值：{target_columns[0]}")
                    print(f"当前位置：{message}")
                else:
                    print(f"ERROR {message}")
            else:
                print("❌ 格式错误！使用：move 8,13 或 move 8")

        elif command == '替换永久棋子':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.end_turn(self.current_player_id)
            if success:
                print("本轮次结束。")
                print(message)
                print("进度已锁定，请打卡后输入【打卡完毕】恢复开启新轮次功能")
            else:
                print(f"ERROR {message}")

        elif command == 'end':  # 保留兼容性
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

        elif command == '打卡完毕':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.complete_checkin(self.current_player_id)
            if success:
                print("您可以开始新的轮次了～")
            else:
                print(f"ERROR {message}")

        elif command == 'checkin':  # 保留兼容性
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.complete_checkin(self.current_player_id)
            print(f"{'OK' if success else 'ERROR'} {message}")

        elif command == '查看当前进度':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.get_game_status(self.current_player_id)
            print(message)  # 直接显示状态信息

        elif command in ['status', 'progress']:  # 保留兼容性
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.get_game_status(self.current_player_id)
            print(message)

        elif command == '排行榜':
            success, message = self.game_service.get_leaderboard()
            print(message)

        elif command == 'leaderboard':  # 保留兼容性
            success, message = self.game_service.get_leaderboard()
            print(message)

        elif command.startswith('领取') and '奖励' in command:
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            # 解析奖励类型和数量
            # 格式：领取（类型）奖励n
            match = re.match(r'领取[（(]?(.+?)[）)]?奖励(\d+)', command)
            if match:
                reward_type = match.group(1)
                reward_count = int(match.group(2))
                success, message = self.game_service.add_score(self.current_player_id, 0, f"{reward_type}_reward")
                if success:
                    print(f"您的积分+{message.split('+')[-1] if '+' in message else '10'}")
                else:
                    print(f"ERROR {message}")
            else:
                print("❌ 格式错误！使用：领取（类型）奖励n")

        elif command.startswith('我超级满意这张图'):
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            # 解析数量
            number_match = re.search(r'(\d+)', command)
            if number_match:
                count = int(number_match.group(1))
                success, message = self.game_service.add_score(self.current_player_id, 30 * count, "超常发挥奖励")
                if success:
                    print(f"您的积分+{30 * count}")
                else:
                    print(f"ERROR {message}")
            else:
                print("❌ 格式错误！请包含数字")

        elif command == '道具商店':
            success, message = self.game_service.get_shop_info()
            if success:
                print("🛒 道具商店")
                print("=" * 30)
                print("常驻道具：")
                print("［丑喵玩偶］150积分 - 每天可使用3次，随机获得奖励")
                print()
                print("地图解锁道具：")
                print(message if message else "暂无解锁道具")
            else:
                print(f"ERROR {message}")

        elif command == '购买丑喵玩偶':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.purchase_item(self.current_player_id, "丑喵玩偶", 150)
            if success:
                print("购买成功！您获得了丑喵玩偶")
            else:
                print(f"ERROR {message}")

        elif command == '捏捏丑喵玩偶':
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            success, message = self.game_service.use_doll(self.current_player_id)
            if success:
                if "获得" in message:
                    print("玩偶发出了呼噜呼噜的响声，似乎很高兴，你获得r3d6的积分")
                else:
                    print("玩偶发出了吱吱的响声，并从你手中滑了出去")
            else:
                print(f"ERROR {message}")

        elif command.startswith('添加') and command.endswith('到道具商店'):
            if not self.current_player_id:
                print("❌ 请先注册或登录")
                return True

            # 解析道具名称
            item_name = command[2:-5]  # 移除"添加"和"到道具商店"
            success, message = self.game_service.add_shop_item(self.current_player_id, item_name)
            if success:
                print(f"道具 [{item_name}] 已添加到商店")
            else:
                print(f"ERROR {message}")

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
            # 尝试解析为纯数字组合 - 支持 8,13 或 8 格式
            if ',' in command or command.isdigit():
                if not self.current_player_id:
                    print("❌ 请先注册或登录")
                    return True

                target_columns = self.parse_move_command(command)
                if target_columns:
                    success, message = self.game_service.move_markers(self.current_player_id, target_columns)
                    if success:
                        if len(target_columns) == 2:
                            print(f"玩家选择记录数值：{target_columns[0]},{target_columns[1]}")
                        else:
                            print(f"玩家选择记录数值：{target_columns[0]}")
                        print(f"当前位置：{message}")
                    else:
                        print(f"ERROR {message}")
                else:
                    print("❌ 格式错误！使用：8,13 或 8")
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
            "register 测试玩家",
            "选择阵营：收养人",
            "轮次开始",
            ".r6d6",
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