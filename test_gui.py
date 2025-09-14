"""
测试GUI启动器
"""

import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置高DPI环境变量（必须在导入Qt之前）
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt

    # 设置高DPI策略（必须在创建QApplication之前）
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # 创建应用
    app = QApplication(sys.argv)

    # 导入和创建GUI
    from src.interfaces.gui import CantStopGUI
    window = CantStopGUI()
    window.show()

    # 运行
    sys.exit(app.exec())

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()