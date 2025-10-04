"""
上帝模式GUI - 游戏的唯一管理界面
具有完全的游戏控制和监控能力
"""

import sys
import os
from typing import Optional, List, Dict, Any
import asyncio

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QGridLayout,
        QGroupBox, QSpinBox, QMessageBox, QListWidget, QFrame, QSplitter,
        QScrollArea, QListWidgetItem, QMenu, QTabWidget, QTableWidget,
        QTableWidgetItem, QHeaderView, QProgressBar, QCheckBox
    )
    from PySide6.QtCore import Qt, QTimer, QTime, Signal
    from PySide6.QtGui import QFont, QPalette, QColor, QAction
except ImportError as e:
    print(f"❌ 无法导入PySide6: {e}")
    sys.exit(1)

try:
    from ..services.game_service import GameService
    from ..services.message_processor import MessageProcessor, UserMessage
    from ..core.achievement_system import AchievementSystem
    from ..core.trap_system import TrapSystem
    from .gm_panel import GMOverviewPanel
    from .gui import GameBoard, GameCell
except ImportError:
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.services.game_service import GameService
        from src.services.message_processor import MessageProcessor, UserMessage
        from src.core.achievement_system import AchievementSystem
        from src.core.trap_system import TrapSystem
        from src.interfaces.gm_panel import GMOverviewPanel
        from src.interfaces.gui import GameBoard, GameCell
    except ImportError as e:
        print(f"❌ 无法导入游戏服务: {e}")
        sys.exit(1)


class PlayerManagementPanel(QWidget):
    """玩家管理面板"""

    def __init__(self, game_service):
        super().__init__()
        self.game_service = game_service
        self.setup_ui()
        self.refresh_players()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("👥 玩家管理")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c5aa0;
                padding: 10px;
                background: #f0f8ff;
                border: 2px solid #2c5aa0;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)

        # 新增玩家区域
        add_group = QGroupBox("➕ 添加新玩家")
        add_layout = QGridLayout(add_group)

        self.new_player_id = QLineEdit()
        self.new_player_id.setPlaceholderText("玩家ID")
        add_layout.addWidget(QLabel("玩家ID:"), 0, 0)
        add_layout.addWidget(self.new_player_id, 0, 1)

        self.new_player_name = QLineEdit()
        self.new_player_name.setPlaceholderText("玩家名称")
        add_layout.addWidget(QLabel("玩家名称:"), 1, 0)
        add_layout.addWidget(self.new_player_name, 1, 1)

        self.new_player_faction = QComboBox()
        self.new_player_faction.addItems(["收养人", "Aonreth"])
        add_layout.addWidget(QLabel("阵营:"), 2, 0)
        add_layout.addWidget(self.new_player_faction, 2, 1)

        self.add_player_btn = QPushButton("✅ 添加玩家")
        self.add_player_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        self.add_player_btn.clicked.connect(self.add_player)
        add_layout.addWidget(self.add_player_btn, 3, 0, 1, 2)

        layout.addWidget(add_group)

        # 玩家列表
        players_group = QGroupBox("👥 现有玩家")
        players_layout = QVBoxLayout(players_group)

        self.players_table = QTableWidget(0, 6)
        self.players_table.setHorizontalHeaderLabels([
            "玩家ID", "玩家名称", "阵营", "积分", "状态", "操作"
        ])
        self.players_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.players_table.setAlternatingRowColors(True)

        players_layout.addWidget(self.players_table)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新玩家列表")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_players)
        players_layout.addWidget(refresh_btn)

        layout.addWidget(players_group)

    def add_player(self):
        """添加新玩家"""
        player_id = self.new_player_id.text().strip()
        player_name = self.new_player_name.text().strip()
        faction = self.new_player_faction.currentText()

        if not player_id or not player_name:
            QMessageBox.warning(self, "警告", "请填写完整的玩家信息")
            return

        try:
            success, message = self.game_service.register_player(player_id, player_name, faction)
            if success:
                QMessageBox.information(self, "成功", f"玩家添加成功: {player_name}")
                self.new_player_id.clear()
                self.new_player_name.clear()
                self.refresh_players()
            else:
                QMessageBox.warning(self, "失败", f"添加失败: {message}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加玩家时发生错误: {str(e)}")

    def refresh_players(self):
        """刷新玩家列表"""
        try:
            success, players = self.game_service.get_all_players()
            if not success:
                return

            self.players_table.setRowCount(len(players))

            for i, player in enumerate(players):
                # 玩家ID
                id_item = QTableWidgetItem(player.get("player_id", ""))
                self.players_table.setItem(i, 0, id_item)

                # 玩家名称
                name_item = QTableWidgetItem(player.get("username", ""))
                self.players_table.setItem(i, 1, name_item)

                # 阵营
                faction_item = QTableWidgetItem(player.get("faction", ""))
                self.players_table.setItem(i, 2, faction_item)

                # 积分
                score_item = QTableWidgetItem(str(player.get("current_score", 0)))
                self.players_table.setItem(i, 3, score_item)

                # 状态
                status_item = QTableWidgetItem(player.get("status", "空闲"))
                self.players_table.setItem(i, 4, status_item)

                # 操作按钮
                action_btn = QPushButton("🎮 进入游戏")
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #17a2b8;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #117a8b;
                    }
                """)
                player_id = player.get("player_id", "")
                action_btn.clicked.connect(lambda checked, pid=player_id: self.enter_game(pid))
                self.players_table.setCellWidget(i, 5, action_btn)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新玩家列表失败: {str(e)}")

    def enter_game(self, player_id: str):
        """进入指定玩家的游戏"""
        try:
            # 通知主窗口切换到指定玩家
            parent = self.parent()
            while parent and not hasattr(parent, 'switch_to_player'):
                parent = parent.parent()

            if parent:
                parent.switch_to_player(player_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"进入游戏失败: {str(e)}")


class GameControlPanel(QWidget):
    """游戏控制面板"""

    def __init__(self, game_service, main_window=None):
        super().__init__()
        self.game_service = game_service
        self.main_window = main_window  # 保存主窗口引用
        self.current_player_id = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 当前玩家信息
        current_group = QGroupBox("🎯 当前玩家")
        current_layout = QVBoxLayout(current_group)

        self.current_player_label = QLabel("未选择玩家")
        self.current_player_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #dc3545;
                padding: 10px;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
            }
        """)
        current_layout.addWidget(self.current_player_label)

        layout.addWidget(current_group)

        # 游戏控制
        control_group = QGroupBox("🎮 游戏控制")
        control_layout = QGridLayout(control_group)

        # 开始游戏
        self.start_game_btn = QPushButton("🎯 开始新游戏")
        self.start_game_btn.clicked.connect(self.start_game)
        control_layout.addWidget(self.start_game_btn, 0, 0)

        # 掷骰子
        self.roll_dice_btn = QPushButton("🎲 掷骰子")
        self.roll_dice_btn.clicked.connect(self.roll_dice)
        control_layout.addWidget(self.roll_dice_btn, 0, 1)

        # 结束轮次
        self.end_turn_btn = QPushButton("⏹️ 结束轮次")
        self.end_turn_btn.clicked.connect(self.end_turn)
        control_layout.addWidget(self.end_turn_btn, 1, 0)

        # 查看状态
        self.status_btn = QPushButton("📊 查看状态")
        self.status_btn.clicked.connect(self.view_status)
        control_layout.addWidget(self.status_btn, 1, 1)

        # 添加积分
        points_layout = QHBoxLayout()
        self.points_input = QSpinBox()
        self.points_input.setRange(-999, 999)
        self.points_input.setValue(10)
        points_layout.addWidget(QLabel("积分:"))
        points_layout.addWidget(self.points_input)

        self.add_points_btn = QPushButton("💰 修改积分")
        self.add_points_btn.clicked.connect(self.modify_points)
        points_layout.addWidget(self.add_points_btn)

        control_layout.addLayout(points_layout, 2, 0, 1, 2)

        # 快捷积分奖励
        rewards_layout = QHBoxLayout()
        rewards_label = QLabel("快捷奖励:")
        rewards_layout.addWidget(rewards_label)

        sketch_btn = QPushButton("🎨 草图(+20)")
        sketch_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        sketch_btn.clicked.connect(lambda: self.award_points("草图"))
        rewards_layout.addWidget(sketch_btn)

        small_btn = QPushButton("🇺 精致小图(+80)")
        small_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        small_btn.clicked.connect(lambda: self.award_points("精致小图"))
        rewards_layout.addWidget(small_btn)

        large_btn = QPushButton("🎭 精致大图(+150)")
        large_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        large_btn.clicked.connect(lambda: self.award_points("精致大图"))
        rewards_layout.addWidget(large_btn)

        control_layout.addLayout(rewards_layout, 3, 0, 1, 2)

        layout.addWidget(control_group)

        # 游戏输出
        output_group = QGroupBox("📋 游戏输出")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setMaximumHeight(200)
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        output_layout.addWidget(self.output_text)

        layout.addWidget(output_group)

        # 初始状态下禁用按钮
        self.set_controls_enabled(False)
        # 保存奖励按钮引用
        self.reward_buttons = [sketch_btn, small_btn, large_btn]

    def set_current_player(self, player_id: str, player_name: str):
        """设置当前玩家"""
        self.current_player_id = player_id
        self.current_player_label.setText(f"当前玩家: {player_name} (ID: {player_id})")
        self.current_player_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #155724;
                padding: 10px;
                background: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
            }
        """)
        self.set_controls_enabled(True)
        self.add_output(f"🔄 切换到玩家: {player_name}")

    def set_controls_enabled(self, enabled: bool):
        """启用/禁用控制按钮"""
        self.start_game_btn.setEnabled(enabled)
        self.roll_dice_btn.setEnabled(enabled)
        self.end_turn_btn.setEnabled(enabled)
        self.status_btn.setEnabled(enabled)
        self.add_points_btn.setEnabled(enabled)
        # 启用/禁用奖励按钮
        for btn in getattr(self, 'reward_buttons', []):
            btn.setEnabled(enabled)

    def add_output(self, message: str):
        """添加输出消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_text.append(f"[{timestamp}] {message}")
        # 自动滚动到最新消息
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)

    def start_game(self):
        """开始游戏"""
        if not self.current_player_id:
            return

        try:
            success, message = self.game_service.start_new_game(self.current_player_id)
            self.add_output(f"{'✅' if success else '❌'} 开始游戏: {message}")
        except Exception as e:
            self.add_output(f"❌ 开始游戏失败: {str(e)}")

    def roll_dice(self):
        """掷骰子"""
        if not self.current_player_id:
            return

        try:
            success, message = self.game_service.roll_dice(self.current_player_id)
            self.add_output(f"{'✅' if success else '❌'} 掷骰: {message}")
        except Exception as e:
            self.add_output(f"❌ 掷骰失败: {str(e)}")

    def end_turn(self):
        """结束轮次"""
        if not self.current_player_id:
            return

        try:
            success, message = self.game_service.end_turn(self.current_player_id)
            self.add_output(f"{'✅' if success else '❌'} 结束轮次: {message}")
        except Exception as e:
            self.add_output(f"❌ 结束轮次失败: {str(e)}")

    def view_status(self):
        """查看状态"""
        if not self.current_player_id:
            return

        try:
            success, message = self.game_service.get_game_status(self.current_player_id)
            self.add_output(f"📊 游戏状态:")
            self.add_output(message)
        except Exception as e:
            self.add_output(f"❌ 获取状态失败: {str(e)}")

    def modify_points(self):
        """修改积分"""
        if not self.current_player_id:
            return

        try:
            points = self.points_input.value()
            # 使用GameService的add_score方法
            success, message = self.game_service.add_score(self.current_player_id, points, "管理员操作")
            if success:
                self.add_output(f"💰 {message}")
                # 刷新玩家列表以显示更新后的积分
                if self.main_window and hasattr(self.main_window, 'player_panel'):
                    self.main_window.player_panel.refresh_players()
            else:
                self.add_output(f"❌ 修改积分失败: {message}")
        except Exception as e:
            self.add_output(f"❌ 修改积分失败: {str(e)}")

    def award_points(self, award_type: str):
        """奖励积分"""
        if not self.current_player_id:
            self.add_output("❌ 请先选择玩家")
            return

        try:
            # 使用GameService的add_score方法，它会根据作品类型自动设置积分
            success, message = self.game_service.add_score(self.current_player_id, 0, award_type)
            if success:
                self.add_output(f"🎆 {message}")
                # 刷新玩家列表以显示更新后的积分
                if self.main_window and hasattr(self.main_window, 'player_panel'):
                    self.main_window.player_panel.refresh_players()
            else:
                self.add_output(f"❌ 奖励失败: {message}")
        except Exception as e:
            self.add_output(f"❌ 奖励失败: {str(e)}")


class GodModeGUI(QMainWindow):
    """上帝模式GUI主界面"""

    def __init__(self):
        super().__init__()
        # 确保使用统一的数据库配置
        from ..utils.config import get_config
        config = get_config()

        self.game_service = GameService()
        self.message_processor = MessageProcessor()
        self.achievement_system = AchievementSystem()
        self.trap_system = TrapSystem()

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("CantStop - 上帝模式控制台")
        self.setGeometry(100, 100, 1400, 900)

        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧面板 - 玩家管理 (较窄)
        left_panel = PlayerManagementPanel(self.game_service)
        main_layout.addWidget(left_panel, 2)

        # 中间面板 - 游戏地图和控制 (较宽)
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)

        # 游戏地图面板 (放在中间顶部)
        map_group = QGroupBox("🗺️ 游戏地图")
        map_layout = QVBoxLayout(map_group)

        # 创建游戏地图
        self.game_board = GameBoard(self.trap_system, self.game_service)

        # 添加滚动区域以支持地图缩放
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.game_board)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        scroll_area.setMaximumHeight(500)

        map_layout.addWidget(scroll_area)
        middle_layout.addWidget(map_group, 2)

        # 游戏控制面板 (在地图下方)
        control_panel = GameControlPanel(self.game_service, self)
        middle_layout.addWidget(control_panel, 1)

        main_layout.addWidget(middle_widget, 4)

        # 右侧面板 - GM总览 (较窄)
        gm_overview = GMOverviewPanel(self.game_service)
        main_layout.addWidget(gm_overview, 2)

        # 保存引用以便后续使用
        self.player_panel = left_panel
        self.control_panel = control_panel
        self.gm_panel = gm_overview

        # 设置实时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(2000)  # 每2秒刷新一次所有数据

        # 设置地图刷新
        self.map_refresh_timer = QTimer()
        self.map_refresh_timer.timeout.connect(self.refresh_game_map)
        self.map_refresh_timer.start(1000)  # 每1秒刷新一次地图

    def switch_to_player(self, player_id: str):
        """切换到指定玩家"""
        try:
            # 获取玩家信息
            player = self.game_service.db.get_player(player_id)
            if player:
                self.control_panel.set_current_player(player_id, player.username)
                QMessageBox.information(self, "成功", f"已切换到玩家: {player.username}")
            else:
                QMessageBox.warning(self, "错误", "玩家不存在")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换玩家失败: {str(e)}")

    def refresh_all_data(self):
        """刷新所有数据"""
        try:
            # 刷新玩家列表
            if hasattr(self, 'player_panel'):
                self.player_panel.refresh_players()

            # 刷新GM总览
            if hasattr(self, 'gm_panel'):
                self.gm_panel.refresh_data()

        except Exception as e:
            print(f"刷新数据失败: {e}")

    def refresh_game_map(self):
        """刷新游戏地图显示"""
        try:
            # 获取所有玩家的游戏状态
            success, players = self.game_service.get_all_players()
            if success:
                # 清空地图
                for cell in self.game_board.cells.values():
                    cell.set_empty()

                # 更新每个玩家的位置
                for i, player in enumerate(players):
                    player_name = player.get('username', '')
                    player_id = player.get('player_id', '')

                    # 获取玩家的游戏会话
                    db_player = self.game_service.db.get_player(player_id)
                    if db_player and hasattr(db_player, 'progress_records'):
                        # 永久标记
                        for progress in db_player.progress_records:
                            if progress.is_completed:
                                column = progress.column
                                max_row = 13 - abs(7 - column)  # 计算最大行数
                                cell_key = f"{column}_{max_row}"
                                if cell_key in self.game_board.cells:
                                    self.game_board.cells[cell_key].add_player(player_name, i % 8, is_permanent=True)

                    # 获取临时标记
                    session = self.game_service.db.get_player_active_session(player_id)
                    if session and hasattr(session, 'temporary_markers'):
                        for marker in session.temporary_markers:
                            column = marker.column
                            position = marker.position  # TemporaryMarker使用position而不是row
                            cell_key = f"{column}_{position}"
                            if cell_key in self.game_board.cells:
                                self.game_board.cells[cell_key].add_player(player_name, i % 8, is_permanent=False)

        except Exception as e:
            print(f"刷新地图失败: {e}")

    def apply_styles(self):
        """应用样式"""
        style = """
        QMainWindow {
            background: #f5f5f5;
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
        }
        QPushButton {
            background-color: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #545b62;
        }
        QPushButton:disabled {
            background-color: #e9ecef;
            color: #6c757d;
        }
        QLineEdit, QSpinBox, QComboBox {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
        }
        QTableWidget {
            gridline-color: #dee2e6;
            background-color: white;
            alternate-background-color: #f8f9fa;
        }
        QTableWidget::item {
            padding: 8px;
        }
        QHeaderView::section {
            background-color: #e9ecef;
            padding: 8px;
            border: 1px solid #dee2e6;
            font-weight: bold;
        }
        """
        self.setStyleSheet(style)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("CantStop God Mode")

    window = GodModeGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()