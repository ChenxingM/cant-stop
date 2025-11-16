"""
增强的GUI面板组件
包含玩家详细信息、成就管理、道具管理等
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTextEdit, QListWidget,
    QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QLineEdit,
    QSpinBox, QComboBox, QGridLayout, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor

from typing import Optional, List, Dict


class PlayerDetailPanel(QWidget):
    """玩家详细信息面板"""

    def __init__(self, game_service):
        super().__init__()
        self.game_service = game_service
        self.current_player_id = None
        self.setup_ui()

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_player_info)
        self.refresh_timer.start(2000)  # 每2秒刷新

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        title = QLabel("👤 玩家详细信息")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #ffffff; padding: 8px;")
        layout.addWidget(title)

        # 标签页
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background: #2a2a2a;
            }
            QTabBar::tab {
                background: #3a3a3a;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #0d6efd;
            }
        """)

        # 基本信息标签页
        self.basic_info_widget = self.create_basic_info_tab()
        tab_widget.addTab(self.basic_info_widget, "📊 基本信息")

        # 棋盘状态标签页
        self.board_status_widget = self.create_board_status_tab()
        tab_widget.addTab(self.board_status_widget, "🎯 棋盘状态")

        # 成就标签页
        self.achievements_widget = self.create_achievements_tab()
        tab_widget.addTab(self.achievements_widget, "🏆 成就")

        # 背包标签页
        self.inventory_widget = self.create_inventory_tab()
        tab_widget.addTab(self.inventory_widget, "🎒 背包")

        layout.addWidget(tab_widget)

    def create_basic_info_tab(self):
        """创建基本信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 玩家名称
        self.player_name_label = QLabel("玩家: 未选择")
        self.player_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.player_name_label.setStyleSheet("""
            QLabel {
                background: #1e3a5f;
                border: 1px solid #0d6efd;
                border-radius: 4px;
                padding: 10px;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.player_name_label)

        # 积分信息
        score_group = QGroupBox("💰 积分信息")
        score_layout = QVBoxLayout()

        self.current_score_label = QLabel("当前积分: 0")
        self.current_score_label.setFont(QFont("Arial", 11))
        self.current_score_label.setStyleSheet("color: #28a745; font-weight: bold;")
        score_layout.addWidget(self.current_score_label)

        self.total_score_label = QLabel("总积分: 0")
        self.total_score_label.setFont(QFont("Arial", 10))
        self.total_score_label.setStyleSheet("color: #adb5bd;")
        score_layout.addWidget(self.total_score_label)

        score_group.setLayout(score_layout)
        layout.addWidget(score_group)

        # 游戏统计
        stats_group = QGroupBox("📈 游戏统计")
        stats_layout = QVBoxLayout()

        self.games_played_label = QLabel("游戏场次: 0")
        self.games_won_label = QLabel("获胜场次: 0")
        self.dice_rolls_label = QLabel("掷骰次数: 0")
        self.turns_played_label = QLabel("总轮次: 0")

        for label in [self.games_played_label, self.games_won_label,
                     self.dice_rolls_label, self.turns_played_label]:
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: #ffffff; padding: 4px;")
            stats_layout.addWidget(label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 阵营信息
        faction_group = QGroupBox("⚔️ 阵营")
        faction_layout = QVBoxLayout()

        self.faction_label = QLabel("阵营: 未知")
        self.faction_label.setFont(QFont("Arial", 10))
        self.faction_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        faction_layout.addWidget(self.faction_label)

        faction_group.setLayout(faction_layout)
        layout.addWidget(faction_group)

        layout.addStretch()
        return widget

    def create_board_status_tab(self):
        """创建棋盘状态标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 永久棋子
        permanent_group = QGroupBox("● 永久棋子位置")
        permanent_layout = QVBoxLayout()

        self.permanent_list = QListWidget()
        self.permanent_list.setStyleSheet("""
            QListWidget {
                background: #343a40;
                border: 1px solid #495057;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #495057;
            }
            QListWidget::item:selected {
                background: #dc3545;
            }
        """)
        permanent_layout.addWidget(self.permanent_list)

        permanent_group.setLayout(permanent_layout)
        layout.addWidget(permanent_group)

        # 临时棋子
        temporary_group = QGroupBox("○ 临时棋子位置")
        temporary_layout = QVBoxLayout()

        self.temporary_list = QListWidget()
        self.temporary_list.setStyleSheet("""
            QListWidget {
                background: #343a40;
                border: 1px solid #495057;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #495057;
            }
            QListWidget::item:selected {
                background: #28a745;
            }
        """)
        temporary_layout.addWidget(self.temporary_list)

        temporary_group.setLayout(temporary_layout)
        layout.addWidget(temporary_group)

        # 已登顶列
        completed_group = QGroupBox("🎯 已登顶")
        completed_layout = QVBoxLayout()

        self.completed_label = QLabel("已登顶: 0/3")
        self.completed_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.completed_label.setStyleSheet("color: #ffc107;")
        completed_layout.addWidget(self.completed_label)

        self.completed_columns_label = QLabel("列: 无")
        self.completed_columns_label.setStyleSheet("color: #adb5bd;")
        completed_layout.addWidget(self.completed_columns_label)

        completed_group.setLayout(completed_layout)
        layout.addWidget(completed_group)

        return widget

    def create_achievements_tab(self):
        """创建成就标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 成就统计
        stats_label = QLabel()
        stats_label.setFont(QFont("Arial", 10))
        stats_label.setStyleSheet("color: #adb5bd; padding: 8px;")
        layout.addWidget(stats_label)
        self.achievement_stats_label = stats_label

        # 成就列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: #343a40; border: 1px solid #495057; }")

        achievement_container = QWidget()
        self.achievement_layout = QVBoxLayout(achievement_container)
        scroll.setWidget(achievement_container)

        layout.addWidget(scroll)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新成就")
        refresh_btn.clicked.connect(self.refresh_achievements)
        layout.addWidget(refresh_btn)

        return widget

    def create_inventory_tab(self):
        """创建背包标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 道具列表
        self.inventory_table = QTableWidget(0, 4)
        self.inventory_table.setHorizontalHeaderLabels([
            "道具名称", "类型", "数量", "操作"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setStyleSheet("""
            QTableWidget {
                background: #343a40;
                color: #ffffff;
                border: 1px solid #495057;
                gridline-color: #495057;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #495057;
                color: #ffffff;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.inventory_table)

        # 操作按钮
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新背包")
        refresh_btn.clicked.connect(self.refresh_inventory)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        return widget

    def set_player(self, player_id: str):
        """设置当前玩家"""
        self.current_player_id = player_id
        self.refresh_player_info()

    def refresh_player_info(self):
        """刷新玩家信息"""
        if not self.current_player_id:
            return

        try:
            player = self.game_service.db.get_player(self.current_player_id)
            if not player:
                return

            # 更新基本信息
            self.player_name_label.setText(f"玩家: {player.username}")
            self.current_score_label.setText(f"当前积分: {player.current_score}")
            self.total_score_label.setText(f"总积分: {player.total_score}")
            self.games_played_label.setText(f"游戏场次: {player.games_played}")
            self.games_won_label.setText(f"获胜场次: {player.games_won}")
            self.dice_rolls_label.setText(f"掷骰次数: {getattr(player, 'total_dice_rolls', 0)}")
            self.turns_played_label.setText(f"总轮次: {getattr(player, 'total_turns', 0)}")

            faction_name = "收养人" if player.faction.value == "收养人" else "Aeonreth"
            self.faction_label.setText(f"阵营: {faction_name}")

            # 更新棋盘状态
            self.refresh_board_status(player)

        except Exception as e:
            print(f"刷新玩家信息失败: {e}")

    def refresh_board_status(self, player):
        """刷新棋盘状态"""
        try:
            # 永久棋子
            self.permanent_list.clear()
            if hasattr(player, 'progress') and player.progress:
                permanent_progress = player.progress.permanent_progress
                if permanent_progress:
                    for column, position in sorted(permanent_progress.items()):
                        if position > 0:
                            item = QListWidgetItem(f"第{column}列 - 位置{position}")
                            self.permanent_list.addItem(item)

                # 已登顶
                completed_count = len(player.progress.completed_columns) if player.progress.completed_columns else 0
                self.completed_label.setText(f"已登顶: {completed_count}/3")
                if player.progress.completed_columns:
                    columns_str = ", ".join(map(str, sorted(player.progress.completed_columns)))
                    self.completed_columns_label.setText(f"列: {columns_str}")
                else:
                    self.completed_columns_label.setText("列: 无")

            # 临时棋子
            self.temporary_list.clear()
            session = self.game_service.db.get_player_active_session(self.current_player_id)
            if session and hasattr(session, 'temporary_markers') and session.temporary_markers:
                for marker in session.temporary_markers:
                    # 计算总位置
                    permanent_pos = 0
                    if hasattr(player, 'progress') and player.progress:
                        permanent_pos = player.progress.get_progress(marker.column)
                    total_pos = permanent_pos + marker.position

                    item = QListWidgetItem(f"第{marker.column}列 - 位置{total_pos} (永久{permanent_pos}+临时{marker.position})")
                    self.temporary_list.addItem(item)

        except Exception as e:
            print(f"刷新棋盘状态失败: {e}")

    def refresh_achievements(self):
        """刷新成就列表"""
        if not self.current_player_id:
            return

        try:
            from ..core.achievement_manager import AchievementManager
            from ..core.achievement_system import AchievementCategory

            manager = AchievementManager()

            # 清空现有成就
            while self.achievement_layout.count():
                child = self.achievement_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # 获取玩家成就
            player = self.game_service.db.get_player(self.current_player_id)
            if not player:
                return

            all_achievements = manager.get_all_achievements()
            unlocked_achievements = [a for a in all_achievements if a.achievement_id in player.achievements]

            # 更新统计
            self.achievement_stats_label.setText(
                f"已解锁: {len(unlocked_achievements)}/{len(all_achievements)} "
                f"({len(unlocked_achievements)/len(all_achievements)*100:.1f}%)"
            )

            # 按分类显示
            for category in AchievementCategory:
                cat_achievements = [a for a in all_achievements if a.category == category]
                if not cat_achievements:
                    continue

                # 分类标题
                cat_label = QLabel(f"【{category.value}】")
                cat_label.setFont(QFont("Arial", 10, QFont.Bold))
                cat_label.setStyleSheet("color: #ffffff; margin-top: 10px;")
                self.achievement_layout.addWidget(cat_label)

                # 该分类的成就
                for ach in cat_achievements:
                    ach_widget = self.create_achievement_widget(ach, ach.achievement_id in player.achievements)
                    self.achievement_layout.addWidget(ach_widget)

            self.achievement_layout.addStretch()

        except Exception as e:
            print(f"刷新成就失败: {e}")

    def create_achievement_widget(self, achievement, is_unlocked):
        """创建成就组件"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # 图标
        icon_label = QLabel("✅" if is_unlocked else "🔒")
        icon_label.setFont(QFont("Arial", 12))
        layout.addWidget(icon_label)

        # 名称和描述
        info_layout = QVBoxLayout()

        name_label = QLabel(achievement.name)
        name_label.setFont(QFont("Arial", 9, QFont.Bold))
        name_label.setStyleSheet("color: #28a745;" if is_unlocked else "color: #6c757d;")
        info_layout.addWidget(name_label)

        if is_unlocked:
            desc_label = QLabel(achievement.reward_description)
        else:
            desc_label = QLabel(achievement.unlock_condition)
        desc_label.setFont(QFont("Arial", 8))
        desc_label.setStyleSheet("color: #adb5bd;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout, 1)

        widget.setStyleSheet(f"""
            QWidget {{
                background: {'#1e3a2b' if is_unlocked else '#343a40'};
                border: 1px solid {'#28a745' if is_unlocked else '#495057'};
                border-radius: 4px;
                padding: 4px;
            }}
        """)

        return widget

    def refresh_inventory(self):
        """刷新背包"""
        if not self.current_player_id:
            return

        try:
            inventory = self.game_service.db.get_player_inventory(self.current_player_id)

            self.inventory_table.setRowCount(len(inventory))

            for i, item in enumerate(inventory):
                # 道具名称
                name_item = QTableWidgetItem(item['item_name'])
                self.inventory_table.setItem(i, 0, name_item)

                # 类型
                type_item = QTableWidgetItem(item['item_type'])
                self.inventory_table.setItem(i, 1, type_item)

                # 数量
                quantity_item = QTableWidgetItem(str(item['quantity']))
                self.inventory_table.setItem(i, 2, quantity_item)

                # 使用按钮
                use_btn = QPushButton("使用")
                use_btn.clicked.connect(
                    lambda checked, name=item['item_name']: self.use_item(name)
                )
                self.inventory_table.setCellWidget(i, 3, use_btn)

        except Exception as e:
            print(f"刷新背包失败: {e}")

    def use_item(self, item_name: str):
        """使用道具"""
        if not self.current_player_id:
            return

        try:
            success, message, _ = self.game_service.use_item(self.current_player_id, item_name)

            msg_box = QMessageBox(self)
            if success:
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("成功")
            else:
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("提示")

            msg_box.setText(message)
            msg_box.exec()

            # 刷新背包
            self.refresh_inventory()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"使用道具失败: {str(e)}")


class CommandPanel(QWidget):
    """新命令面板（成就、进度回退、奖励领取）"""

    command_executed = Signal(str, str)  # 命令文本, 结果消息

    def __init__(self, game_service):
        super().__init__()
        self.game_service = game_service
        self.current_player_id = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("🎮 高级命令")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff; padding: 8px;")
        layout.addWidget(title)

        # 成就命令
        achievement_group = QGroupBox("🏆 成就相关")
        achievement_layout = QVBoxLayout()

        view_achievements_btn = QPushButton("查看成就一览")
        view_achievements_btn.setProperty("class", "info")
        view_achievements_btn.clicked.connect(self.view_achievements)
        achievement_layout.addWidget(view_achievements_btn)

        achievement_group.setLayout(achievement_layout)
        layout.addWidget(achievement_group)

        # 进度管理
        progress_group = QGroupBox("📉 进度管理")
        progress_layout = QVBoxLayout()

        retreat_btn = QPushButton("进度回退")
        retreat_btn.setProperty("class", "warning")
        retreat_btn.clicked.connect(self.progress_retreat)
        retreat_btn.setToolTip("清空所有临时标记，结束当前轮次")
        progress_layout.addWidget(retreat_btn)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # 奖励领取
        reward_group = QGroupBox("🎁 奖励领取")
        reward_layout = QGridLayout()

        reward_types = [
            ("草图", 10),
            ("精致小图", 20),
            ("精草大图", 30),
            ("精致大图", 40),
            ("打卡", 15)
        ]

        for i, (reward_type, base_score) in enumerate(reward_types):
            # 奖励类型按钮
            normal_btn = QPushButton(f"{reward_type}\n(+{base_score})")
            normal_btn.setProperty("class", "success small")
            normal_btn.clicked.connect(
                lambda checked, rt=reward_type: self.claim_reward(rt, False)
            )
            reward_layout.addWidget(normal_btn, i, 0)

            # 翻倍按钮
            double_btn = QPushButton(f"翻倍\n(+{base_score*2})")
            double_btn.setProperty("class", "warning small")
            double_btn.clicked.connect(
                lambda checked, rt=reward_type: self.claim_reward(rt, True)
            )
            reward_layout.addWidget(double_btn, i, 1)

        reward_group.setLayout(reward_layout)
        layout.addWidget(reward_group)

        layout.addStretch()

    def set_player(self, player_id: str):
        """设置当前玩家"""
        self.current_player_id = player_id

    def view_achievements(self):
        """查看成就一览"""
        if not self.current_player_id:
            QMessageBox.warning(self, "警告", "请先选择玩家")
            return

        try:
            from ..services.message_processor import MessageProcessor, UserMessage

            processor = MessageProcessor()
            user_message = UserMessage(
                user_id=self.current_player_id,
                username="",
                content="成就一览"
            )

            import asyncio
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(processor.process_message_async(user_message))

            # 显示结果
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("成就一览")
            msg_box.setText(response.content if response else "获取成就失败")
            msg_box.exec()

            self.command_executed.emit("成就一览", response.content if response else "")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"查看成就失败: {str(e)}")

    def progress_retreat(self):
        """进度回退"""
        if not self.current_player_id:
            QMessageBox.warning(self, "警告", "请先选择玩家")
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认进度回退",
            "确定要清空所有临时标记吗？这将结束当前轮次。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            success, message = self.game_service.force_fail_turn(self.current_player_id)

            msg_box = QMessageBox(self)
            if success:
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("成功")
            else:
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("提示")

            msg_box.setText(message)
            msg_box.exec()

            self.command_executed.emit("进度回退", message)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"进度回退失败: {str(e)}")

    def claim_reward(self, reward_type: str, doubled: bool):
        """领取奖励"""
        if not self.current_player_id:
            QMessageBox.warning(self, "警告", "请先选择玩家")
            return

        try:
            success, message = self.game_service.claim_reward(
                self.current_player_id,
                reward_type,
                times=1,
                doubled=doubled
            )

            msg_box = QMessageBox(self)
            if success:
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("成功")
            else:
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("提示")

            msg_box.setText(message)
            msg_box.exec()

            reward_text = f"领取{reward_type}奖励{'翻倍' if doubled else ''}"
            self.command_executed.emit(reward_text, message)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"领取奖励失败: {str(e)}")
