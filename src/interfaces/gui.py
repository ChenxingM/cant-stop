"""
Can't Stop游戏PySide6 GUI
"""

import sys
import os
from typing import Optional, List, Dict
import asyncio

# 确保导入路径正确
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QGridLayout,
        QGroupBox, QSpinBox, QMessageBox, QListWidget, QFrame, QSplitter,
        QScrollArea, QListWidgetItem, QMenu
    )
    from PySide6.QtCore import Qt, QTimer, QTime, Signal
    from PySide6.QtGui import QFont, QPalette, QColor, QAction
except ImportError as e:
    print(f"❌ 无法导入PySide6: {e}")
    print("请运行：pip install PySide6")
    sys.exit(1)

try:
    from ..services.game_service import GameService
    from ..services.message_processor import MessageProcessor, UserMessage
    from ..core.achievement_system import AchievementSystem, AchievementCategory
    from ..core.trap_system import TrapSystem
    from ..config.config_manager import get_config
except ImportError:
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.services.game_service import GameService
        from src.services.message_processor import MessageProcessor, UserMessage
        from src.core.achievement_system import AchievementSystem, AchievementCategory
        from src.core.trap_system import TrapSystem
    except ImportError as e:
        print(f"❌ 无法导入游戏服务: {e}")
        sys.exit(1)


class GameCell(QFrame):
    """游戏格子组件"""

    # 定义信号
    trap_changed = Signal(int, int, str)  # column, row, trap_name

    # 玩家颜色配置
    PLAYER_COLORS = {
        0: "#FF6B6B",  # 红色
        1: "#4ECDC4",  # 青色
        2: "#45B7D1",  # 蓝色
        3: "#96CEB4",  # 绿色
        4: "#FFEAA7",  # 黄色
        5: "#DDA0DD",  # 紫色
        6: "#FFB347",  # 橙色
        7: "#87CEEB",  # 天蓝色
    }

    def __init__(self, column: int, row: int, trap_system=None):
        super().__init__()
        self.column = column
        self.row = row
        self.players = []  # 在此格子的玩家列表 [(name, color_index, is_permanent), ...]
        self.player_color_map = {}  # 玩家名称到颜色索引的映射
        self.trap_system = trap_system
        self.trap_type = None

        # 检查是否是陷阱位置
        if trap_system:
            self.trap_type = trap_system.get_trap_for_position(column, row)

        self.setFixedSize(50, 40)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)  # 启用hover检测
        self.setProperty("class", "game-cell")

        # 如果是陷阱，设置提示
        if self.trap_type:
            trap_info = trap_system.traps[self.trap_type]
            self.setToolTip(f"🕳️ {self.trap_type.value}\n\n📖 {trap_info.description}\n\n💬 \"{trap_info.character_quote}\"\n\n⚠️ 首次触发:\n{trap_info.penalty_description}\n\n💰 重复触发: {trap_info.repeat_penalty}")

        # 简化布局
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # 玩家显示标签 - 主要显示区域
        self.player_label = QLabel("")
        self.player_label.setAlignment(Qt.AlignCenter)
        self.player_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(self.player_label)

        # 位置标记（小图标）
        self.position_label = QLabel("")
        self.position_label.setAlignment(Qt.AlignCenter)
        self.position_label.setFont(QFont("Arial", 8))
        layout.addWidget(self.position_label)

        self.setLayout(layout)

        # 设置默认样式
        self.set_empty()

        # 启用右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def set_empty(self):
        """设置为空格子"""
        if self.trap_type:
            # 陷阱格子显示特殊样式
            self.setStyleSheet("""
                QFrame[class="game-cell"] {
                    background: #2d1b3d;
                    border: 2px solid #8b0000;
                    border-radius: 4px;
                }
                QFrame[class="game-cell"]:hover {
                    background: #3d2b4d;
                    border: 2px solid #ff4444;
                }
            """)
            self.player_label.setText("")
            self.position_label.setText("🕳️")
            self.position_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        else:
            # 普通空格子样式
            self.setStyleSheet("""
                QFrame[class="game-cell"] {
                    background: #2a2a2a;
                    border: 1px solid #444444;
                    border-radius: 4px;
                }
                QFrame[class="game-cell"]:hover {
                    background: #3a3a3a;
                    border: 1px solid #666666;
                }
            """)
            self.player_label.setText("")
            self.position_label.setText("")
        self.players.clear()
        self.player_color_map.clear()

    def add_player(self, player_name: str, color_index: int, is_permanent: bool = False):
        """添加玩家到格子"""
        player_info = (player_name, color_index, is_permanent)

        # 移除该玩家之前的记录
        self.players = [p for p in self.players if p[0] != player_name]
        self.players.append(player_info)
        self.player_color_map[player_name] = color_index

        # 更新显示
        self._update_display()

    def _update_display(self):
        """更新格子显示"""
        if not self.players:
            self.set_empty()
            return

        # 现代化的玩家显示
        if len(self.players) == 1:
            player_name, color_index, is_permanent = self.players[0]
            color = self.PLAYER_COLORS.get(color_index, "#6c757d")

            # 清晰的视觉区分
            if is_permanent:
                border_color = "#dc3545"
                border_width = "2px"
                icon = "●"
            else:
                border_color = "#28a745"
                border_width = "2px"
                icon = "○"

            # 如果是陷阱位置，添加陷阱图标
            trap_icon = "🕳️" if self.trap_type else ""

            self.setStyleSheet(f"""
                QFrame[class="game-cell"] {{
                    background: {color};
                    border: {border_width} solid {border_color};
                    border-radius: 4px;
                }}
                QLabel {{
                    color: white;
                    font-weight: bold;
                }}
            """)

            self.player_label.setText(f"{trap_icon}{player_name[:2]}")
            self.position_label.setText(icon)

        else:
            # 多玩家简化显示
            colors = [self.PLAYER_COLORS.get(p[1], "#6c757d") for p in self.players]
            has_permanent = any(p[2] for p in self.players)

            primary_color = colors[0]
            border_color = "#dc3545" if has_permanent else "#28a745"

            # 如果是陷阱位置，添加陷阱图标
            trap_icon = "🕳️" if self.trap_type else ""

            self.setStyleSheet(f"""
                QFrame[class="game-cell"] {{
                    background: {primary_color};
                    border: 2px solid {border_color};
                    border-radius: 4px;
                }}
                QLabel {{
                    color: white;
                    font-weight: bold;
                }}
            """)

            self.player_label.setText(f"{trap_icon}{len(self.players)}")
            self.position_label.setText("●" if has_permanent else "○")

    def update_trap_status(self, trap_type, trap_tooltip=""):
        """更新陷阱状态"""
        self.trap_type = trap_type
        if trap_tooltip:
            self.setToolTip(trap_tooltip)
        else:
            self.setToolTip("")
        # 重新应用显示
        self._update_display()

    def show_context_menu(self, position):
        """显示右键上下文菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                background: transparent;
                padding: 6px 12px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background: #3a3a3a;
            }
            QMenu::separator {
                height: 1px;
                background: #444444;
                margin: 2px 0;
            }
        """)

        # 陷阱设置子菜单
        trap_menu = QMenu("🕳️ 设置陷阱", self)
        trap_menu.setStyleSheet(menu.styleSheet())

        # 添加各种陷阱选项
        trap_options = [
            ("小小火球术", "🔥", "停止一回合并强制骰子结果"),
            ("不要回头", "🔄", "扣除积分，可能清空标记"),
            ("河..土地神", "🌊", "二选一：失去行动权或标记后退"),
            ("花言巧语", "💬", "必须改变标记移动方向")
        ]

        for trap_name, icon, description in trap_options:
            action = QAction(f"{icon} {trap_name}", self)
            action.setToolTip(description)
            action.triggered.connect(lambda checked, name=trap_name: self.set_trap(name))
            trap_menu.addAction(action)

        # 清除陷阱选项
        clear_action = QAction("❌ 清除陷阱", self)
        clear_action.triggered.connect(lambda: self.set_trap(""))

        # 添加到主菜单
        menu.addMenu(trap_menu)
        menu.addSeparator()
        menu.addAction(clear_action)

        # 添加位置信息
        menu.addSeparator()
        info_action = QAction(f"📍 位置: 第{self.column}列-{self.row}位", self)
        info_action.setEnabled(False)
        menu.addAction(info_action)

        # 如果当前有陷阱，显示当前陷阱信息
        if self.trap_type:
            if hasattr(self.trap_type, 'value'):
                current_text = f"🕳️ 当前: {self.trap_type.value}"
            else:
                current_text = f"🕳️ 当前: {self.trap_type}"
            current_action = QAction(current_text, self)
            current_action.setEnabled(False)
            menu.insertAction(info_action, current_action)
        else:
            empty_action = QAction("⭕ 当前: 无陷阱", self)
            empty_action.setEnabled(False)
            menu.insertAction(info_action, empty_action)

        # 显示菜单
        menu.exec(self.mapToGlobal(position))

    def set_trap(self, trap_name: str):
        """设置陷阱"""
        # 发射信号通知GameBoard更新
        self.trap_changed.emit(self.column, self.row, trap_name)

    def remove_player(self, player_name: str):
        """从格子移除玩家"""
        self.players = [p for p in self.players if p[0] != player_name]
        if player_name in self.player_color_map:
            del self.player_color_map[player_name]

        self._update_display()


class AchievementPanel(QWidget):
    """成就显示面板"""

    def __init__(self):
        super().__init__()
        self.achievement_system = AchievementSystem()
        self.init_ui()

    def init_ui(self):
        """初始化成就面板UI"""
        layout = QVBoxLayout()

        # 标题
        title = QLabel("🏆 成就系统")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff; padding: 5px;")
        layout.addWidget(title)

        # 成就统计
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #adb5bd; font-size: 10px; padding: 2px;")
        layout.addWidget(self.stats_label)

        # 成就列表（滚动区域）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("QScrollArea { background: #343a40; border: 1px solid #495057; }")

        self.achievement_widget = QWidget()
        self.achievement_widget.setStyleSheet("QWidget { background: #343a40; }")
        self.achievement_layout = QVBoxLayout()
        self.achievement_widget.setLayout(self.achievement_layout)

        scroll_area.setWidget(self.achievement_widget)
        layout.addWidget(scroll_area)

        self.setLayout(layout)
        self.refresh_achievements()

    def refresh_achievements(self):
        """刷新成就显示"""
        # 清空现有成就
        for i in reversed(range(self.achievement_layout.count())):
            self.achievement_layout.itemAt(i).widget().setParent(None)

        all_achievements = self.achievement_system.get_all_achievements()
        unlocked = self.achievement_system.get_unlocked_achievements()
        locked = self.achievement_system.get_locked_achievements()

        # 更新统计
        self.stats_label.setText(f"已解锁: {len(unlocked)} / {len(all_achievements)}")

        # 按分类显示成就
        for category in AchievementCategory:
            category_achievements = self.achievement_system.get_achievement_by_category(category)
            if not category_achievements:
                continue

            # 分类标题
            category_label = QLabel(f"📂 {category.value}")
            category_label.setFont(QFont("Arial", 10, QFont.Bold))
            category_label.setStyleSheet("color: #ffffff; margin-top: 10px;")
            self.achievement_layout.addWidget(category_label)

            # 该分类下的成就
            for achievement in category_achievements:
                achievement_item = self.create_achievement_item(achievement)
                self.achievement_layout.addWidget(achievement_item)

    def create_achievement_item(self, achievement) -> QWidget:
        """创建紧凑的成就项目"""
        item = QFrame()
        item.setMaximumHeight(35)
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # 成就图标
        icon_label = QLabel("🏆" if achievement.is_unlocked else "🔒")
        icon_label.setFont(QFont("Arial", 12))
        icon_label.setFixedSize(20, 20)
        layout.addWidget(icon_label)

        # 成就名称
        name_label = QLabel(achievement.name)
        name_label.setFont(QFont("Arial", 8, QFont.Bold))

        if achievement.is_unlocked:
            name_label.setStyleSheet("color: #28a745;")
            item.setStyleSheet("""
                QFrame {
                    background: #1e3a2b;
                    border: 1px solid #28a745;
                    border-radius: 3px;
                    margin: 1px;
                }
            """)
        else:
            name_label.setStyleSheet("color: #6c757d;")
            item.setStyleSheet("""
                QFrame {
                    background: #343a40;
                    border: 1px solid #495057;
                    border-radius: 3px;
                    margin: 1px;
                }
            """)

        layout.addWidget(name_label, 1)  # 拉伸

        item.setLayout(layout)
        return item


class GameBoard(QWidget):
    """游戏棋盘显示组件"""

    def __init__(self, trap_system=None, game_service=None):
        super().__init__()
        self.cells: Dict[str, GameCell] = {}  # 格子字典，key: "column_row"
        self.player_colors: Dict[str, int] = {}  # 玩家颜色分配
        self.color_counter = 0  # 颜色计数器
        self.trap_system = trap_system
        self.game_service = game_service  # 添加游戏服务引用以获取动态陷阱配置
        self.init_ui()

    def init_ui(self):
        """初始化棋盘UI"""
        layout = QGridLayout()
        layout.setSpacing(1)

        # 列长度配置
        column_lengths = {
            3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
            9: 9, 10: 10, 11: 10, 12: 9, 13: 8,
            14: 7, 15: 6, 16: 5, 17: 4, 18: 3
        }

        # 创建格子（翻转棋盘：底部到顶部）
        max_length = 10  # 最长列的长度

        # 先添加列数字标签（在最下方）
        for col in range(3, 19):
            col_label = QLabel(str(col))
            col_label.setAlignment(Qt.AlignCenter)
            col_label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
            col_label.setStyleSheet("color: #ffffff; font-weight: bold; background: #333; padding: 2px; border-radius: 2px; max-height: 18px;")
            col_label.setFixedHeight(18)
            layout.addWidget(col_label, max_length + 1, col - 3)  # 在最下方

        for col in range(3, 19):
            length = column_lengths[col]

            # 为每列创建格子（从底部到顶部，翻转显示）
            for row in range(1, length + 1):  # 从1开始，不包括列号
                # 计算翻转后的行位置
                flipped_row = max_length - row + 1
                cell = GameCell(col, row, None)  # 暂时不传入trap_system
                cell.trap_changed.connect(self.on_trap_changed)  # 连接陷阱变更信号
                self.cells[f"{col}_{row}"] = cell
                layout.addWidget(cell, flipped_row, col - 3)

        self.setLayout(layout)

        # 初始化完成后更新陷阱显示
        if self.game_service:
            self.update_trap_tooltips()

    def assign_player_color(self, player_name: str) -> int:
        """为玩家分配颜色"""
        if player_name not in self.player_colors:
            self.player_colors[player_name] = self.color_counter % len(GameCell.PLAYER_COLORS)
            self.color_counter += 1
        return self.player_colors[player_name]

    def clear_board(self):
        """清空棋盘"""
        for cell in self.cells.values():
            cell.set_empty()

    def update_trap_tooltips(self):
        """更新陷阱工具提示和视觉效果"""
        if not self.trap_system or not self.game_service:
            return

        for cell in self.cells.values():
            # 重新检查陷阱位置 - 从游戏引擎的陷阱配置获取最新信息
            try:
                trap_name = self.game_service.engine.trap_config.get_trap_for_position(cell.column, cell.row)

                if trap_name:
                    # 根据陷阱名称获取陷阱类型
                    trap_type = self.trap_system.get_trap_by_name(trap_name)
                    if trap_type:
                        trap_info = self.trap_system.traps[trap_type]
                        # 创建详细的陷阱工具提示
                        tooltip = f"🕳️ {trap_type.value}\n\n📖 {trap_info.description}\n\n💬 \"{trap_info.character_quote}\"\n\n⚠️ 首次触发:\n{trap_info.penalty_description}\n\n💰 重复触发: {trap_info.repeat_penalty}"
                        cell.update_trap_status(trap_type, tooltip)
                    else:
                        # 未知陷阱类型
                        cell.update_trap_status(True, f"🕳️ {trap_name}")
                else:
                    # 清空陷阱显示
                    cell.update_trap_status(None, "")

            except Exception as e:
                # 如果获取失败，清空提示
                cell.update_trap_status(None, "")
                print(f"更新陷阱显示失败: {e}")  # 调试用

    def update_player_positions(self, all_players_data: List[Dict]):
        """更新所有玩家位置"""
        # 先清空棋盘
        self.clear_board()

        # 添加所有玩家位置
        for player_data in all_players_data:
            player_name = player_data.get('username', 'Unknown')
            color_index = self.assign_player_color(player_name)

            # 永久进度
            permanent_progress = player_data.get('permanent_progress', {})
            for column, progress in permanent_progress.items():
                if progress > 0:
                    cell_key = f"{column}_{progress}"
                    if cell_key in self.cells:
                        self.cells[cell_key].add_player(player_name, color_index, is_permanent=True)

            # 临时标记
            temporary_markers = player_data.get('temporary_markers', [])
            for marker in temporary_markers:
                column = marker.get('column')
                position = marker.get('position')

                # 计算总位置（永久进度 + 临时位置）
                permanent = permanent_progress.get(column, 0)
                total_position = permanent + position

                cell_key = f"{column}_{total_position}"
                if cell_key in self.cells:
                    self.cells[cell_key].add_player(player_name, color_index, is_permanent=False)

        # 更新完玩家位置后，重新应用陷阱显示
        self.update_trap_tooltips()

    def on_trap_changed(self, column: int, row: int, trap_name: str):
        """处理陷阱变更信号"""
        if not self.game_service:
            return

        try:
            if trap_name:
                # 手动设置单个陷阱位置
                success, message = self.game_service.set_manual_trap(trap_name, column, row)
                if success:
                    # 更新陷阱显示
                    self.update_trap_tooltips()
                    # 通知用户
                    print(f"✅ {message}")
                else:
                    print(f"❌ 设置陷阱失败: {message}")
            else:
                # 清除陷阱
                success, message = self.game_service.remove_trap_at_position(column, row)
                if success:
                    # 更新陷阱显示
                    self.update_trap_tooltips()
                    print(f"✅ {message}")
                else:
                    print(f"ℹ️ {message}")

        except Exception as e:
            print(f"❌ 陷阱操作失败: {str(e)}")

class PlayerListWidget(QWidget):
    """玩家列表组件"""

    def __init__(self, game_service):
        super().__init__()
        self.game_service = game_service
        self.current_player = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 标题
        title = QLabel("玩家列表")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        # 玩家列表
        self.player_list = QListWidget()
        self.player_list.itemClicked.connect(self.on_player_selected)
        layout.addWidget(self.player_list)

        # 刷新按钮
        refresh_btn = QPushButton("刷新玩家列表")
        refresh_btn.clicked.connect(self.refresh_players)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)

        # 定时刷新
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_players)
        self.timer.start(5000)  # 每5秒刷新一次

        # 初始刷新
        self.refresh_players()

    def refresh_players(self):
        """刷新玩家列表"""
        try:
            # 获取排行榜来获取玩家列表
            success, leaderboard = self.game_service.get_leaderboard(50)
            if not success:
                return

            # 解析排行榜数据
            lines = leaderboard.split('\n')
            players = []
            for line in lines:
                if '|' in line or line.strip().startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            rank = parts[0]
                            username = parts[1]
                            if username != '玩家' and username != '排名':  # 过滤标题行
                                players.append(username)
                        except:
                            continue

            # 更新列表
            self.player_list.clear()
            for player in players:
                item = QListWidgetItem(player)
                self.player_list.addItem(item)

        except Exception as e:
            print(f"刷新玩家列表失败: {e}")

    def on_player_selected(self, item):
        """玩家被选中"""
        self.current_player = item.text()
        # 发出信号给主窗口
        parent = self.parent()
        while parent and not hasattr(parent, 'on_player_switched'):
            parent = parent.parent()
        if parent and hasattr(parent, 'on_player_switched'):
            parent.on_player_switched(self.current_player)


class CantStopGUI(QMainWindow):
    """Can't Stop GUI主界面"""

    def __init__(self):
        super().__init__()
        self.game_service = GameService()
        self.message_processor = MessageProcessor()
        self.achievement_system = AchievementSystem()
        self.trap_system = TrapSystem()

        self.current_player_id: Optional[str] = None
        self.current_username: Optional[str] = None
        self.achievement_panel = None

        self.init_ui()
        self.apply_global_styles()

    def init_ui(self):
        """初始化用户界面"""
        window_title = get_config("game_config", "ui.window_title", "Can't Stop 贪骰无厌游戏")
        window_width = get_config("game_config", "ui.window_size.width", 1200)
        window_height = get_config("game_config", "ui.window_size.height", 800)

        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, window_width, window_height)

        # 高DPI优化
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局 - 水平分割
        main_layout = QHBoxLayout(central_widget)

        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # 中间棋盘
        board_panel = self.create_board_panel()
        main_layout.addWidget(board_panel, 2)

        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)

    def apply_global_styles(self):
        """应用优化的全局QSS样式 - Dark Mode"""
        style = """
        /* 主窗口 - Dark Mode */
        QMainWindow {
            background: #1e1e1e;
            color: #ffffff;
            font-family: "Segoe UI", "微软雅黑", Arial, sans-serif;
        }

        /* 按钮基础样式 - Dark Mode */
        QPushButton {
            background: #495057;
            color: #ffffff;
            border: 1px solid #6c757d;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            min-height: 28px;
        }
        QPushButton:hover {
            background: #6c757d;
            border-color: #adb5bd;
            color: #ffffff;
        }
        QPushButton:pressed {
            background: #343a40;
        }
        QPushButton:disabled {
            background: #343a40;
            color: #6c757d;
            border-color: #495057;
        }

        /* 主要按钮 - 蓝色 */
        QPushButton[class="primary"] {
            background: #0d6efd;
            border-color: #0d6efd;
        }
        QPushButton[class="primary"]:hover {
            background: #0b5ed7;
            border-color: #0a58ca;
        }

        /* 成功按钮 - 绿色 */
        QPushButton[class="success"] {
            background: #198754;
            border-color: #198754;
        }
        QPushButton[class="success"]:hover {
            background: #157347;
            border-color: #146c43;
        }

        /* 警告按钮 - 橙色 */
        QPushButton[class="warning"] {
            background: #fd7e14;
            border-color: #fd7e14;
            color: #ffffff;
        }
        QPushButton[class="warning"]:hover {
            background: #e85d04;
            border-color: #dc5502;
        }

        /* 危险按钮 - 红色 */
        QPushButton[class="danger"] {
            background: #dc3545;
            border-color: #dc3545;
        }
        QPushButton[class="danger"]:hover {
            background: #bb2d3b;
            border-color: #b02a37;
        }

        /* Info按钮 - 青色 */
        QPushButton[class="info"] {
            background: #17a2b8;
            border-color: #17a2b8;
        }
        QPushButton[class="info"]:hover {
            background: #138496;
            border-color: #117a8b;
        }

        /* 数字按钮 - 紫色，小尺寸 */
        QPushButton[class="number"] {
            background: #6f42c1;
            border-color: #6f42c1;
            min-width: 32px;
            max-width: 32px;
            min-height: 32px;
            max-height: 32px;
            font-size: 11px;
            font-weight: bold;
            border-radius: 16px;
            padding: 0px;
        }
        QPushButton[class="number"]:hover {
            background: #5a32a3;
            border-color: #5a32a3;
        }

        /* 小按钮样式 */
        QPushButton[class="small"] {
            padding: 4px 10px;
            font-size: 10px;
            min-height: 22px;
        }

        /* 输入框 - Dark Mode */
        QLineEdit {
            border: 1px solid #495057;
            border-radius: 4px;
            padding: 8px 10px;
            font-size: 11px;
            background: #343a40;
            color: #ffffff;
            min-height: 16px;
        }
        QLineEdit:focus {
            border-color: #0d6efd;
            background: #495057;
        }

        /* 组合框 */
        QComboBox {
            border: 1px solid #495057;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 10px;
            background: #343a40;
            color: #ffffff;
            min-height: 20px;
        }
        QComboBox:focus {
            border-color: #0d6efd;
        }
        QComboBox::drop-down {
            border: none;
            background: #495057;
        }
        QComboBox::down-arrow {
            image: none;
            border-style: solid;
            border-width: 4px 4px 0 4px;
            border-color: #ffffff transparent transparent transparent;
        }

        /* 分组框 - Dark Mode */
        QGroupBox {
            font-weight: 600;
            font-size: 12px;
            border: 1px solid #495057;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
            background: #343a40;
            color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 8px;
            color: #ffffff;
            background: #343a40;
        }

        /* 文本区域 - Dark Mode */
        QTextEdit {
            border: 1px solid #495057;
            border-radius: 4px;
            padding: 6px;
            background: #212529;
            color: #ffffff;
            font-family: "Consolas", monospace;
            font-size: 12px;
            line-height: 1.4;
        }

        /* 列表 - Dark Mode */
        QListWidget {
            border: 1px solid #495057;
            border-radius: 4px;
            background: #343a40;
            color: #ffffff;
            font-size: 10px;
        }
        QListWidget::item {
            padding: 4px 8px;
            border-bottom: 1px solid #495057;
        }
        QListWidget::item:selected {
            background: #0d6efd;
            color: #ffffff;
        }
        QListWidget::item:hover {
            background: #495057;
            color: #ffffff;
        }

        /* 滚动条 - Dark Mode */
        QScrollBar:vertical {
            background: #343a40;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #6c757d;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #adb5bd;
        }

        /* 标签 - Dark Mode */
        QLabel {
            color: #ffffff;
        }

        /* 游戏格子特殊样式 - Dark Mode */
        QFrame[class="game-cell"] {
            border: 1px solid #495057;
            border-radius: 3px;
            background: #343a40;
        }
        QFrame[class="game-cell"]:hover {
            border: 2px solid #6c757d;
            background: #495057;
        }

        /* 面板背景 - Dark Mode */
        QWidget {
            background: #1e1e1e;
        }
        """
        self.setStyleSheet(style)

        self.show_message("🎲 欢迎来到Can't Stop游戏！请先注册或选择玩家。\n💡 提示: 鼠标悬停在地图上的🕳️陷阱图标可查看陷阱详情")

    def create_left_panel(self):
        """创建优化的左侧控制面板"""
        panel = QWidget()
        panel.setMaximumWidth(320)
        panel.setStyleSheet("QWidget { background: #1e1e1e; }")
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # 玩家管理 - 紧凑布局
        player_group = QGroupBox("👤 玩家管理")
        player_layout = QVBoxLayout()
        player_layout.setSpacing(6)

        # 注册区域 - 垂直布局更紧凑
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("玩家名称")
        player_layout.addWidget(self.username_input)

        register_row = QHBoxLayout()
        register_row.setSpacing(4)

        self.faction_combo = QComboBox()
        self.faction_combo.addItems(["收养人", "Aonreth"])
        register_row.addWidget(self.faction_combo)

        self.register_btn = QPushButton("注册")
        self.register_btn.setProperty("class", "success")
        self.register_btn.clicked.connect(self.register_player)
        register_row.addWidget(self.register_btn)

        player_layout.addLayout(register_row)

        # 当前玩家显示 - Dark Mode样式
        self.current_player_label = QLabel("当前玩家：未选择")
        self.current_player_label.setStyleSheet("""
            QLabel {
                background: #1e3a5f;
                border: 1px solid #0d6efd;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
                color: #ffffff;
            }
        """)
        player_layout.addWidget(self.current_player_label)

        # 当前积分显示
        self.current_score_label = QLabel("当前积分：0")
        self.current_score_label.setStyleSheet("""
            QLabel {
                background: #1a5c2e;
                border: 1px solid #28a745;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
                color: #ffffff;
            }
        """)
        player_layout.addWidget(self.current_score_label)

        player_group.setLayout(player_layout)
        layout.addWidget(player_group)

        # 游戏控制 - 紧凑横向布局
        control_group = QGroupBox("🎮 游戏控制")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(4)

        self.start_game_btn = QPushButton("开始")
        self.start_game_btn.setProperty("class", "success")
        self.start_game_btn.clicked.connect(self.start_game)
        self.start_game_btn.setEnabled(False)
        control_layout.addWidget(self.start_game_btn)

        self.resume_game_btn = QPushButton("恢复")
        self.resume_game_btn.setProperty("class", "warning")
        self.resume_game_btn.clicked.connect(self.resume_game)
        self.resume_game_btn.setEnabled(False)
        control_layout.addWidget(self.resume_game_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 基础操作 - 紧凑网格
        basic_group = QGroupBox("🎯 基础操作")
        basic_layout = QGridLayout()
        basic_layout.setSpacing(3)

        basic_commands = [
            ("🎲 掷骰", "掷骰", "primary"),
            ("📊 进度", "查看当前进度", "primary"),
            ("🏁 结束", "替换永久棋子", "success"),
            ("✅ 打卡", "打卡完毕", "success"),
            ("▶️ 继续", "continue", "warning"),
            ("📈 排行", "排行榜", "primary"),
        ]

        self.quick_buttons = {}
        for i, (text, command, btn_type) in enumerate(basic_commands):
            btn = QPushButton(text)
            btn.setProperty("class", f"{btn_type} small")
            btn.clicked.connect(self._create_command_handler(command))
            btn.setEnabled(False)
            basic_layout.addWidget(btn, i // 3, i % 3)
            self.quick_buttons[command] = btn

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 数字选择区
        numbers_group = QGroupBox("🔢 列号选择")
        numbers_layout = QGridLayout()
        numbers_layout.setSpacing(2)

        for col in range(3, 19):
            btn = QPushButton(str(col))
            btn.setProperty("class", "number")
            btn.clicked.connect(lambda checked, cmd=str(col): self.quick_command(cmd))
            btn.setEnabled(False)
            numbers_layout.addWidget(btn, 0 if col <= 10 else 1, (col - 3) % 8)
            self.quick_buttons[str(col)] = btn

        numbers_group.setLayout(numbers_layout)
        layout.addWidget(numbers_group)

        # 积分奖励 - 紧凑布局
        reward_group = QGroupBox("🎨 积分奖励")
        reward_layout = QGridLayout()
        reward_layout.setSpacing(3)

        rewards = [
            ("草图", "领取草图奖励1", "success"),
            ("小图", "领取精致小图奖励1", "success"),
            ("大图", "领取精致大图奖励1", "success"),
            ("满意", "我超级满意这张图1", "success"),
        ]

        for i, (text, command, btn_type) in enumerate(rewards):
            btn = QPushButton(text)
            btn.setProperty("class", f"{btn_type} small")
            btn.clicked.connect(self._create_command_handler(command))
            btn.setEnabled(False)
            reward_layout.addWidget(btn, i // 2, i % 2)
            self.quick_buttons[command] = btn

        reward_group.setLayout(reward_layout)
        layout.addWidget(reward_group)

        # GM管理面板
        gm_group = QGroupBox("🛠️ GM管理")
        gm_layout = QGridLayout()
        gm_layout.setSpacing(3)

        gm_commands = [
            ("重置数据", "reset_all_data", "danger"),
            ("陷阱配置", "trap_config", "info"),
            ("重生陷阱", "regenerate_traps", "warning"),
        ]

        for i, (text, command, btn_type) in enumerate(gm_commands):
            btn = QPushButton(text)
            btn.setProperty("class", f"{btn_type} small")
            # 使用更安全的连接方式
            btn.clicked.connect(self._create_gm_command_handler(command))
            gm_layout.addWidget(btn, i // 2, i % 2)
            self.quick_buttons[command] = btn

        gm_group.setLayout(gm_layout)
        layout.addWidget(gm_group)

        # 陷阱设置区域
        trap_group = QGroupBox("🕳️ 陷阱设置")
        trap_layout = QVBoxLayout()
        trap_layout.setSpacing(4)

        # 陷阱选择
        trap_select_layout = QHBoxLayout()
        self.trap_name_combo = QComboBox()
        self.trap_name_combo.addItems(["小小火球术", "不要回头", "河..土地神", "花言巧语"])
        trap_select_layout.addWidget(QLabel("陷阱:"))
        trap_select_layout.addWidget(self.trap_name_combo)

        # 列号输入
        self.trap_columns_input = QLineEdit()
        self.trap_columns_input.setPlaceholderText("列号,如: 3,4,5")
        trap_select_layout.addWidget(QLabel("列:"))
        trap_select_layout.addWidget(self.trap_columns_input)

        trap_layout.addLayout(trap_select_layout)

        # 设置按钮
        set_trap_btn = QPushButton("设置陷阱")
        set_trap_btn.setProperty("class", "warning small")
        set_trap_btn.clicked.connect(self.set_trap_config)
        trap_layout.addWidget(set_trap_btn)

        trap_group.setLayout(trap_layout)
        layout.addWidget(trap_group)

        # 指令输入框
        input_group = QGroupBox("📝 自定义指令")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(4)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("输入指令，如：8,13")
        self.command_input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.command_input)

        self.execute_btn = QPushButton("执行")
        self.execute_btn.setProperty("class", "primary small")
        self.execute_btn.clicked.connect(self.execute_command)
        self.execute_btn.setEnabled(False)
        input_layout.addWidget(self.execute_btn)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 添加弹性空间，将所有控件推到顶部
        layout.addStretch()
        return panel

    def create_board_panel(self):
        """创建中间棋盘面板"""
        panel = QWidget()
        panel.setStyleSheet("QWidget { background: #1e1e1e; }")
        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("游戏棋盘")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        # 棋盘滚动区域
        scroll = QScrollArea()
        scroll.setStyleSheet("QScrollArea { background: #1e1e1e; border: none; }")
        self.game_board = GameBoard(self.trap_system, self.game_service)
        self.game_board.setStyleSheet("QWidget { background: #1e1e1e; }")
        scroll.setWidget(self.game_board)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return panel

    def create_right_panel(self):
        """创建右侧信息面板"""
        panel = QWidget()
        panel.setStyleSheet("QWidget { background: #1e1e1e; }")
        layout = QVBoxLayout(panel)

        # 玩家列表
        self.player_list_widget = PlayerListWidget(self.game_service)
        layout.addWidget(self.player_list_widget)

        # 游戏消息区域
        message_group = QGroupBox("游戏消息")
        message_layout = QVBoxLayout()

        self.message_area = QTextEdit()
        self.message_area.setMaximumHeight(300)
        self.message_area.setReadOnly(True)
        message_layout.addWidget(self.message_area)

        # 显示所有玩家状态按钮
        self.show_all_status_btn = QPushButton("📊 显示所有玩家状态")
        self.show_all_status_btn.setProperty("class", "primary")
        self.show_all_status_btn.clicked.connect(self.show_all_players_status)
        message_layout.addWidget(self.show_all_status_btn)

        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # 成就系统面板
        self.achievement_panel = AchievementPanel()
        layout.addWidget(self.achievement_panel)

        return panel

    def show_message(self, message: str):
        """显示消息"""
        current_time = QTime.currentTime().toString()
        self.message_area.append(f"[{current_time}] {message}")
        # 滚动到底部
        self.message_area.verticalScrollBar().setValue(
            self.message_area.verticalScrollBar().maximum()
        )

    def register_player(self):
        """注册玩家"""
        username = self.username_input.text().strip()
        faction = self.faction_combo.currentText()

        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名")
            return

        # 先尝试登录
        player = self.game_service.db.get_player(username)
        if player:
            self.current_player_id = username
            self.current_username = player.username
            self.show_message(f"✅ 登录成功！欢迎回来，{player.username}")
        else:
            # 注册新玩家
            success, message = self.game_service.register_player(username, username, faction)
            self.show_message(f"{'✅' if success else '❌'} {message}")

            if success:
                self.current_player_id = username
                self.current_username = username

        # 更新UI状态
        if self.current_player_id:
            self.update_ui_for_player()

    def update_ui_for_player(self):
        """为当前玩家更新UI状态"""
        if self.current_player_id:
            self.current_player_label.setText(f"当前玩家：{self.current_username}")

            # 更新积分显示
            try:
                player = self.game_service.db.get_player(self.current_player_id)
                if player:
                    self.current_score_label.setText(f"当前积分：{player.current_score}")
                else:
                    self.current_score_label.setText("当前积分：未知")
            except:
                self.current_score_label.setText("当前积分：0")

            # 启用按钮
            self.start_game_btn.setEnabled(True)
            self.resume_game_btn.setEnabled(True)
            self.execute_btn.setEnabled(True)

            # 启用所有快捷按钮
            for btn in self.quick_buttons.values():
                btn.setEnabled(True)


    def on_player_switched(self, player_name: str):
        """切换玩家"""
        self.current_player_id = player_name
        self.current_username = player_name
        self.show_message(f"🔄 切换到玩家：{player_name}")
        self.update_ui_for_player()
        self.refresh_board()

    def start_game(self):
        """开始游戏"""
        if not self.current_player_id:
            return

        success, message = self.game_service.start_new_game(self.current_player_id)
        self.show_message(f"{'✅' if success else '❌'} {message}")

        if success:
            self.refresh_board()

    def resume_game(self):
        """恢复游戏"""
        if not self.current_player_id:
            return

        success, message = self.game_service.resume_game(self.current_player_id)
        self.show_message(f"{'✅' if success else '❌'} {message}")

        if success:
            self.refresh_board()

    def quick_command(self, command: str):
        """快捷指令"""
        self.command_input.setText(command)
        self.execute_command()

    def _create_gm_command_handler(self, command):
        """创建GM命令处理器"""
        def handler():
            self.gm_command(command)
        return handler

    def _create_command_handler(self, command):
        """创建常规命令处理器"""
        def handler():
            self.quick_command(command)
        return handler

    def gm_command(self, command: str):
        """GM管理指令"""
        if command == "reset_all_data":
            reply = QMessageBox.question(
                self, "确认重置",
                "⚠️ 即将重置所有玩家的游戏数据，是否确认？\n\n📝 将保留：玩家名称、阵营\n🗑️ 将清除：积分、进度、游戏会话、临时标记",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.game_service.reset_all_game_data()
                self.show_message(f"{'✅' if success else '❌'} {message}")
                if success:
                    self.player_list_widget.refresh_players()
                    self.game_board.clear_board()

        elif command == "trap_config":
            success, message = self.game_service.get_trap_config_info()
            self.show_message(message)

        elif command == "regenerate_traps":
            success, message = self.game_service.regenerate_traps()
            self.show_message(f"{'✅' if success else '❌'} {message}")
            if success:
                # 重新生成陷阱后更新棋盘
                self.game_board.update_trap_tooltips()

    def set_trap_config(self):
        """设置陷阱配置"""
        trap_name = self.trap_name_combo.currentText()
        columns_text = self.trap_columns_input.text().strip()

        if not columns_text:
            self.show_message("❌ 请输入列号")
            return

        try:
            # 解析列号
            if ',' in columns_text:
                columns = [int(x.strip()) for x in columns_text.split(',')]
            else:
                columns = [int(columns_text)]

            # 验证列号范围
            for col in columns:
                if col < 3 or col > 18:
                    self.show_message("❌ 列号必须在3-18之间")
                    return

            success, message = self.game_service.set_trap_config(trap_name, columns)
            self.show_message(f"{'✅' if success else '❌'} {message}")

            if success:
                self.trap_columns_input.clear()
                # 重新设置陷阱配置后更新棋盘
                self.game_board.update_trap_tooltips()

        except ValueError:
            self.show_message("❌ 列号格式错误！使用数字和逗号分隔（如：3,4,5）")

    def execute_command(self):
        """执行指令"""
        if not self.current_player_id:
            self.show_message("❌ 请先选择玩家")
            return

        command = self.command_input.text().strip()
        if not command:
            return

        # 使用消息处理器处理指令
        try:
            import asyncio

            async def process_command():
                from ..services.message_processor import UserMessage
                user_message = UserMessage(
                    user_id=self.current_player_id,
                    username=self.current_username,
                    content=command
                )

                response = await self.message_processor.process_message(user_message)
                return response.content

            # 在新事件循环中运行
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(process_command())

            self.show_message(f"💬 {command}")
            self.show_message(f"🤖 {result}")

            # 清空输入框
            self.command_input.clear()

            # 刷新棋盘和UI
            self.refresh_board()
            self.update_ui_for_player()  # 更新积分显示

        except Exception as e:
            self.show_message(f"❌ 执行指令失败：{str(e)}")


    def refresh_board(self):
        """刷新棋盘显示"""
        try:
            # 获取所有玩家数据
            success, leaderboard = self.game_service.get_leaderboard(50)
            if not success:
                return

            all_players_data = []

            # 解析排行榜获取玩家列表
            lines = leaderboard.split('\n')
            player_names = []
            for line in lines:
                if line.strip() and not line.startswith('-') and not 'rank' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            rank = parts[0]
                            username = parts[1]
                            if username != '玩家' and username != '排名':
                                player_names.append(username)
                        except:
                            continue

            # 获取每个玩家的详细状态
            for player_name in player_names[:10]:  # 限制最多显示10个玩家
                try:
                    success, status = self.game_service.get_game_status(player_name)
                    if success:
                        # 解析状态信息
                        player_data = {
                            'username': player_name,
                            'permanent_progress': {},
                            'temporary_markers': []
                        }

                        # 从数据库直接获取数据
                        player = self.game_service.db.get_player(player_name)
                        session = self.game_service.db.get_player_active_session(player_name)

                        if player:
                            player_data['permanent_progress'] = player.progress.permanent_progress

                        if session:
                            player_data['temporary_markers'] = [
                                {'column': m.column, 'position': m.position}
                                for m in session.temporary_markers
                            ]

                        all_players_data.append(player_data)

                except Exception as e:
                    continue

            # 更新棋盘
            self.game_board.update_player_positions(all_players_data)

        except Exception as e:
            print(f"刷新棋盘失败: {e}")

    def show_all_players_status(self):
        """显示所有玩家的当前状态"""
        try:
            # 获取所有玩家数据
            success, leaderboard = self.game_service.get_leaderboard(50)
            if not success:
                self.show_message("❌ 获取玩家列表失败")
                return

            # 解析排行榜获取玩家列表
            lines = leaderboard.split('\n')
            player_names = []
            for line in lines:
                if line.strip() and not line.startswith('-') and not 'rank' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            rank = parts[0]
                            username = parts[1]
                            if username != '玩家' and username != '排名':
                                player_names.append(username)
                        except:
                            continue

            self.show_message("\n📊 ===== 所有玩家状态 =====\n")

            for i, player_name in enumerate(player_names[:8], 1):  # 最多显示8个玩家
                try:
                    # 获取玩家详细信息
                    player = self.game_service.db.get_player(player_name)
                    session = self.game_service.db.get_player_active_session(player_name)

                    status_info = f"{i}. 👤 {player_name}\n"

                    if player:
                        # 永久进度
                        permanent = player.progress.permanent_progress
                        if permanent:
                            progress_str = ", ".join([f"{col}列:{pos}格" for col, pos in permanent.items() if pos > 0])
                            status_info += f"   🏁 永久进度: {progress_str}\n"
                        else:
                            status_info += f"   🏁 永久进度: 无\n"

                        status_info += f"   💰 积分: {player.current_score}\n"

                    if session:
                        # 临时标记
                        temp_markers = session.temporary_markers
                        if temp_markers:
                            temp_str = ", ".join([f"{m.column}列+{m.position}" for m in temp_markers])
                            status_info += f"   🎯 临时标记: {temp_str}\n"
                        else:
                            status_info += f"   🎯 临时标记: 无\n"

                        status_info += f"   🎲 当前轮次: {session.turn_number}\n"
                    else:
                        status_info += f"   ⏸️ 未在游戏中\n"

                    self.show_message(status_info)

                except Exception as e:
                    self.show_message(f"   ❌ 获取 {player_name} 状态失败: {e}\n")
                    continue

            self.show_message("\n========================\n")

        except Exception as e:
            self.show_message(f"❌ 显示玩家状态失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        event.accept()

    def run(self):
        """运行GUI应用（已弃用，请使用main.py启动）"""
        print("请使用 'python main.py --interface gui' 启动GUI界面")
        return False