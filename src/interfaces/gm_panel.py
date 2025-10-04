"""
GM视角面板 - 游戏整体状态监控
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
        QTableWidgetItem, QGroupBox, QScrollArea, QFrame, QPushButton,
        QGridLayout, QTextEdit, QProgressBar, QHeaderView
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QFont, QColor
except ImportError:
    print("❌ 无法导入PySide6组件")
    exit(1)

import json
from typing import Dict, List, Any


class GMOverviewPanel(QWidget):
    """GM总览面板"""

    def __init__(self, game_service):
        super().__init__()
        self.game_service = game_service
        self.setup_ui()
        self.setup_auto_refresh()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("🎮 GM视角 - 游戏总览")
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

        # 统计信息区域
        stats_group = self.create_statistics_panel()
        layout.addWidget(stats_group)

        # 玩家列表区域
        players_group = self.create_players_panel()
        layout.addWidget(players_group)

        # 控制按钮区域
        controls_group = self.create_controls_panel()
        layout.addWidget(controls_group)

        # 详细信息区域
        details_group = self.create_details_panel()
        layout.addWidget(details_group)

    def create_statistics_panel(self) -> QGroupBox:
        """创建统计信息面板"""
        group = QGroupBox("📊 游戏统计")
        group.setStyleSheet("""
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
        """)

        layout = QGridLayout(group)

        # 创建统计标签
        self.stats_labels = {}
        stats_items = [
            ("total_players", "👥 总玩家数", "0"),
            ("active_games", "🎮 进行中游戏", "0"),
            ("total_turns", "🔄 总轮次数", "0"),
            ("total_dice_rolls", "🎲 总掷骰次数", "0"),
            ("achievements_unlocked", "🏆 已解锁成就", "0"),
            ("traps_triggered", "🕳️ 触发陷阱", "0")
        ]

        for i, (key, label_text, default_value) in enumerate(stats_items):
            row, col = divmod(i, 3)

            # 标签
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #555;")
            layout.addWidget(label, row * 2, col)

            # 数值
            value_label = QLabel(default_value)
            value_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c5aa0;
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 5px;
                    min-height: 20px;
                }
            """)
            layout.addWidget(value_label, row * 2 + 1, col)
            self.stats_labels[key] = value_label

        return group

    def create_players_panel(self) -> QGroupBox:
        """创建玩家列表面板"""
        group = QGroupBox("👥 玩家状态")
        group.setStyleSheet("""
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
        """)

        layout = QVBoxLayout(group)

        # 玩家表格
        self.players_table = QTableWidget(0, 7)
        self.players_table.setHorizontalHeaderLabels([
            "玩家名", "阵营", "状态", "积分", "游戏进度", "成就数", "掷骰次数"
        ])

        # 设置表格样式
        self.players_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

        # 设置表格属性
        self.players_table.setAlternatingRowColors(True)
        self.players_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.players_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.players_table)
        return group

    def create_controls_panel(self) -> QGroupBox:
        """创建控制面板"""
        group = QGroupBox("🎛️ 控制面板")
        group.setStyleSheet("""
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
        """)

        layout = QHBoxLayout(group)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 手动刷新")
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
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        # 导出数据按钮
        export_btn = QPushButton("📊 导出数据")
        export_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #155724;
            }
        """)
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)

        # 自动刷新状态
        self.auto_refresh_label = QLabel("⏱️ 自动刷新: 启用 (30秒)")
        self.auto_refresh_label.setStyleSheet("color: #28a745; font-weight: bold;")
        layout.addWidget(self.auto_refresh_label)

        layout.addStretch()
        return group

    def create_details_panel(self) -> QGroupBox:
        """创建详细信息面板"""
        group = QGroupBox("📋 详细信息")
        group.setStyleSheet("""
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
        """)

        layout = QVBoxLayout(group)

        self.details_text = QTextEdit()
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        self.details_text.setMaximumHeight(150)
        layout.addWidget(self.details_text)

        return group

    def setup_auto_refresh(self):
        """设置自动刷新"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 30秒刷新一次

    def refresh_data(self):
        """刷新数据"""
        try:
            # 获取GM总览数据
            overview = self.game_service.get_gm_overview()

            # 更新统计信息
            self.update_statistics(overview.get("game_statistics", {}))
            self.stats_labels["total_players"].setText(str(overview.get("total_players", 0)))
            self.stats_labels["active_games"].setText(str(overview.get("active_games", 0)))

            # 更新玩家表格
            self.update_players_table(overview.get("players", []))

            # 更新详细信息
            self.update_details(overview)

        except Exception as e:
            self.details_text.append(f"❌ 刷新数据失败: {str(e)}")

    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计信息"""
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(str(value))

    def update_players_table(self, players: List[Dict[str, Any]]):
        """更新玩家表格"""
        self.players_table.setRowCount(len(players))

        for i, player in enumerate(players):
            # 玩家名
            name_item = QTableWidgetItem(player.get("username", "未知"))
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.players_table.setItem(i, 0, name_item)

            # 阵营
            faction_item = QTableWidgetItem(player.get("faction", "未知"))
            faction_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 根据阵营设置颜色
            if player.get("faction") == "收养人":
                faction_item.setBackground(QColor("#e3f2fd"))
            elif player.get("faction") == "Aonreth":
                faction_item.setBackground(QColor("#fff3e0"))
            self.players_table.setItem(i, 1, faction_item)

            # 状态
            status_item = QTableWidgetItem(player.get("status", "未知"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 根据状态设置颜色
            if player.get("status") == "游戏中":
                status_item.setBackground(QColor("#c8e6c9"))
            else:
                status_item.setBackground(QColor("#ffecb3"))
            self.players_table.setItem(i, 2, status_item)

            # 积分
            points_item = QTableWidgetItem(str(player.get("points", 0)))
            points_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.players_table.setItem(i, 3, points_item)

            # 游戏进度
            progress_item = QTableWidgetItem(player.get("current_progress", "无"))
            progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.players_table.setItem(i, 4, progress_item)

            # 成就数
            achievements_item = QTableWidgetItem(str(player.get("achievements_count", 0)))
            achievements_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.players_table.setItem(i, 5, achievements_item)

            # 掷骰次数
            dice_item = QTableWidgetItem(str(player.get("dice_rolls", 0)))
            dice_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.players_table.setItem(i, 6, dice_item)

    def update_details(self, overview: Dict[str, Any]):
        """更新详细信息"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        details = f"""
=== GM视角详细信息 ===
更新时间: {current_time}

错误信息: {overview.get('error', '无')}

活跃玩家详情:
"""
        for player in overview.get("players", []):
            details += f"• {player.get('username', '未知')} ({player.get('faction', '未知')})\n"
            details += f"  状态: {player.get('status', '未知')}\n"
            if player.get("status") == "游戏中":
                details += f"  轮次状态: {player.get('turn_state', '未知')}\n"
                details += f"  进展列数: {player.get('columns_progressed', 0)}\n"
                details += f"  临时标记: {player.get('temporary_markers', 0)}\n"
                details += f"  永久标记: {player.get('permanent_markers', 0)}\n"
            details += "\n"

        self.details_text.setPlainText(details)

    def export_data(self):
        """导出数据到文件"""
        try:
            overview = self.game_service.get_gm_overview()

            import json
            from datetime import datetime

            filename = f"gm_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(overview, f, ensure_ascii=False, indent=2)

            self.details_text.append(f"✅ 数据已导出到: {filename}")

        except Exception as e:
            self.details_text.append(f"❌ 导出失败: {str(e)}")