#!/usr/bin/env python3
"""
上帝模式GUI启动器
唯一的游戏管理界面
"""

import sys
import os

# 设置环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt

    # 设置高DPI策略
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # 创建应用
    app = QApplication(sys.argv)

    # 导入上帝模式GUI
    from src.interfaces.god_mode_gui import GodModeGUI

    # 创建窗口
    window = GodModeGUI()
    window.show()

    print("CantStop God Mode GUI started successfully!")
    print("Features:")
    print("- Player Management")
    print("- Game Control")
    print("- GM Overview")
    print("- Complete game administration")

    # 运行
    sys.exit(app.exec())

except Exception as e:
    print(f"Launch failed: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")