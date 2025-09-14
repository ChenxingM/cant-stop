"""
Can't Stop游戏主入口
"""

import sys
import os
import argparse

# 设置编码
import locale
import io

# 设置控制台编码为UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def main():
    parser = argparse.ArgumentParser(description='Can\'t Stop 贪骰无厌游戏')
    parser.add_argument(
        '--interface',
        choices=['cli', 'gui'],
        default='cli',
        help='选择界面类型 (默认: cli)'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行演示模式'
    )

    args = parser.parse_args()

    if args.interface == 'cli':
        from src.interfaces.cli import CantStopCLI
        cli = CantStopCLI()

        if args.demo:
            print("CLI演示模式")
            print("-" * 30)

            demo_commands = [
                "register 演示玩家 收养人",
                "add_score 草图",
                "start",
                "status",
                "help"
            ]

            for cmd in demo_commands:
                print(f"> {cmd}")
                cli.run_command(cmd)
                print()

            print("演示结束，现在可以开始游戏！")
            print("输入 'help' 查看帮助，输入 'quit' 退出")

        cli.run()

    elif args.interface == 'gui':
        try:
            import sys
            import os
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from src.interfaces.gui import CantStopGUI

            # 启用高DPI支持（必须在创建QApplication之前设置）
            os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
            os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

            # 设置高DPI缩放策略（必须在创建QApplication实例之前调用）
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

            # 创建QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            # 创建GUI窗口
            window = CantStopGUI()
            window.show()

            # 运行应用
            sys.exit(app.exec())

        except ImportError as e:
            print("❌ GUI界面需要安装PySide6")
            print("请运行：pip install PySide6")
            print(f"详细错误: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()