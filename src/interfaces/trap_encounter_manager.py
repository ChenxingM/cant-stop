"""
陷阱和遭遇管理面板
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QSpinBox, QComboBox, QTextEdit,
    QMessageBox, QGridLayout, QCheckBox, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from typing import Optional, List, Dict
import json
import os


def load_available_traps() -> List[str]:
    """从配置文件加载可用的陷阱列表"""
    try:
        trap_plugins_path = "config/trap_plugins.json"
        if os.path.exists(trap_plugins_path):
            with open(trap_plugins_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                traps = list(data.get("plugins", {}).keys())
                return sorted(traps) if traps else ["小小火球术", "不要回头"]
    except Exception as e:
        print(f"加载陷阱列表失败: {e}")

    # 默认列表（如果加载失败）
    return ["小小火球术", "不要回头", "婚戒…？", "奇变偶不变"]


def load_available_encounters() -> List[str]:
    """从配置文件加载可用的遭遇列表"""
    try:
        encounters_path = "config/encounters.json"
        if os.path.exists(encounters_path):
            with open(encounters_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                encounters = list(data.get("encounters", {}).keys())
                return sorted(encounters) if encounters else ["喵", "梦"]
    except Exception as e:
        print(f"加载遭遇列表失败: {e}")

    # 默认列表（如果加载失败）
    return ["喵", "梦", "小花", "不明物质"]


class TrapEncounterManagerPanel(QWidget):
    """陷阱和遭遇管理面板"""

    config_updated = Signal()  # 配置更新信号

    def __init__(self, game_service):
        super().__init__()
        self.game_service = game_service
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("🕳️ 陷阱与遭遇管理")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #ffffff; padding: 8px;")
        layout.addWidget(title)

        # 操作按钮区
        buttons_layout = QHBoxLayout()

        # 随机生成陷阱
        random_traps_btn = QPushButton("🎲 随机放置陷阱")
        random_traps_btn.setProperty("class", "warning")
        random_traps_btn.clicked.connect(self.random_generate_traps)
        random_traps_btn.setToolTip("清空现有陷阱配置并随机生成新的陷阱位置")
        buttons_layout.addWidget(random_traps_btn)

        # 随机生成遭遇
        random_encounters_btn = QPushButton("🎯 随机放置遭遇")
        random_encounters_btn.setProperty("class", "info")
        random_encounters_btn.clicked.connect(self.random_generate_encounters)
        random_encounters_btn.setToolTip("随机生成遭遇事件位置")
        buttons_layout.addWidget(random_encounters_btn)

        # 清空配置
        clear_btn = QPushButton("🗑️ 清空配置")
        clear_btn.setProperty("class", "danger")
        clear_btn.clicked.connect(self.clear_all_config)
        clear_btn.setToolTip("清空所有陷阱和遭遇配置")
        buttons_layout.addWidget(clear_btn)

        layout.addLayout(buttons_layout)

        # 陷阱配置表格
        traps_group = QGroupBox("🕳️ 当前陷阱配置")
        traps_layout = QVBoxLayout()

        self.traps_table = QTableWidget(0, 5)
        self.traps_table.setHorizontalHeaderLabels([
            "陷阱名称", "列位置", "行位置", "已设置数量", "操作"
        ])
        self.traps_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.traps_table.setStyleSheet("""
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
        traps_layout.addWidget(self.traps_table)

        # 添加陷阱按钮
        add_trap_btn = QPushButton("➕ 添加陷阱")
        add_trap_btn.setProperty("class", "success")
        add_trap_btn.clicked.connect(self.add_trap)
        traps_layout.addWidget(add_trap_btn)

        traps_group.setLayout(traps_layout)
        layout.addWidget(traps_group)

        # 遭遇配置表格
        encounters_group = QGroupBox("🎯 当前遭遇配置")
        encounters_layout = QVBoxLayout()

        self.encounters_table = QTableWidget(0, 5)
        self.encounters_table.setHorizontalHeaderLabels([
            "遭遇名称", "列位置", "行位置", "已设置数量", "操作"
        ])
        self.encounters_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.encounters_table.setStyleSheet("""
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
        encounters_layout.addWidget(self.encounters_table)

        # 添加遭遇按钮
        add_encounter_btn = QPushButton("➕ 添加遭遇")
        add_encounter_btn.setProperty("class", "success")
        add_encounter_btn.clicked.connect(self.add_encounter)
        encounters_layout.addWidget(add_encounter_btn)

        encounters_group.setLayout(encounters_layout)
        layout.addWidget(encounters_group)

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新配置")
        refresh_btn.clicked.connect(self.refresh_config)
        layout.addWidget(refresh_btn)

        # 初始刷新
        self.refresh_config()

    def refresh_config(self):
        """刷新配置显示"""
        self.refresh_traps()
        self.refresh_encounters()

    def refresh_traps(self):
        """刷新陷阱配置"""
        try:
            # 获取陷阱配置
            trap_config = self.game_service.engine.trap_config
            generated_traps = trap_config.generated_traps

            # 按陷阱名称分组
            traps_by_name = {}
            for pos_key, trap_name in generated_traps.items():
                if trap_name not in traps_by_name:
                    traps_by_name[trap_name] = []
                traps_by_name[trap_name].append(pos_key)

            # 更新表格
            self.traps_table.setRowCount(len(traps_by_name))

            for i, (trap_name, positions) in enumerate(sorted(traps_by_name.items())):
                # 陷阱名称
                name_item = QTableWidgetItem(trap_name)
                self.traps_table.setItem(i, 0, name_item)

                # 提取列和行
                columns = set()
                rows = set()
                for pos_key in positions:
                    col, row = pos_key.split('_')
                    columns.add(col)
                    rows.add(row)

                # 列位置
                cols_str = ", ".join(sorted(columns))
                cols_item = QTableWidgetItem(cols_str)
                self.traps_table.setItem(i, 1, cols_item)

                # 行位置
                rows_str = ", ".join(sorted(rows))
                rows_item = QTableWidgetItem(rows_str)
                self.traps_table.setItem(i, 2, rows_item)

                # 数量
                count_item = QTableWidgetItem(str(len(positions)))
                self.traps_table.setItem(i, 3, count_item)

                # 操作按钮
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 4, 4, 4)

                edit_btn = QPushButton("编辑")
                edit_btn.setProperty("class", "info small")
                edit_btn.clicked.connect(
                    lambda checked, name=trap_name: self.edit_trap(name)
                )
                action_layout.addWidget(edit_btn)

                delete_btn = QPushButton("删除")
                delete_btn.setProperty("class", "danger small")
                delete_btn.clicked.connect(
                    lambda checked, name=trap_name: self.delete_trap(name)
                )
                action_layout.addWidget(delete_btn)

                self.traps_table.setCellWidget(i, 4, action_widget)

        except Exception as e:
            print(f"刷新陷阱配置失败: {e}")

    def refresh_encounters(self):
        """刷新遭遇配置"""
        try:
            # 获取遭遇配置
            encounter_config = getattr(self.game_service.engine, 'encounter_config', None)
            if not encounter_config:
                self.encounters_table.setRowCount(0)
                return

            generated_encounters = getattr(encounter_config, 'generated_encounters', {})

            # 按遭遇名称分组
            encounters_by_name = {}
            for pos_key, encounter_name in generated_encounters.items():
                if encounter_name not in encounters_by_name:
                    encounters_by_name[encounter_name] = []
                encounters_by_name[encounter_name].append(pos_key)

            # 更新表格
            self.encounters_table.setRowCount(len(encounters_by_name))

            for i, (encounter_name, positions) in enumerate(sorted(encounters_by_name.items())):
                # 遭遇名称
                name_item = QTableWidgetItem(encounter_name)
                self.encounters_table.setItem(i, 0, name_item)

                # 提取列和行
                columns = set()
                rows = set()
                for pos_key in positions:
                    col, row = pos_key.split('_')
                    columns.add(col)
                    rows.add(row)

                # 列位置
                cols_str = ", ".join(sorted(columns))
                cols_item = QTableWidgetItem(cols_str)
                self.encounters_table.setItem(i, 1, cols_item)

                # 行位置
                rows_str = ", ".join(sorted(rows))
                rows_item = QTableWidgetItem(rows_str)
                self.encounters_table.setItem(i, 2, rows_item)

                # 数量
                count_item = QTableWidgetItem(str(len(positions)))
                self.encounters_table.setItem(i, 3, count_item)

                # 操作按钮
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 4, 4, 4)

                edit_btn = QPushButton("编辑")
                edit_btn.setProperty("class", "info small")
                edit_btn.clicked.connect(
                    lambda checked, name=encounter_name: self.edit_encounter(name)
                )
                action_layout.addWidget(edit_btn)

                delete_btn = QPushButton("删除")
                delete_btn.setProperty("class", "danger small")
                delete_btn.clicked.connect(
                    lambda checked, name=encounter_name: self.delete_encounter(name)
                )
                action_layout.addWidget(delete_btn)

                self.encounters_table.setCellWidget(i, 4, action_widget)

        except Exception as e:
            print(f"刷新遭遇配置失败: {e}")

    def random_generate_traps(self):
        """随机生成陷阱"""
        reply = QMessageBox.question(
            self,
            "确认随机生成",
            "这将清空现有陷阱配置并随机生成新的陷阱位置，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 清空现有陷阱
            self.game_service.engine.trap_config.generated_traps.clear()

            # 重新生成
            success, message = self.game_service.regenerate_traps()

            if success:
                QMessageBox.information(self, "成功", message)
                self.refresh_traps()
                self.config_updated.emit()
            else:
                QMessageBox.warning(self, "失败", message)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"随机生成陷阱失败: {str(e)}")

    def random_generate_encounters(self):
        """随机生成遭遇"""
        reply = QMessageBox.question(
            self,
            "确认随机生成",
            "这将清空现有遭遇配置并随机生成新的遭遇位置，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 检查是否有遭遇系统
            encounter_config = getattr(self.game_service.engine, 'encounter_config', None)
            if not encounter_config:
                QMessageBox.warning(self, "警告", "遭遇系统未初始化")
                return

            # 清空现有遭遇
            encounter_config.generated_encounters = {}

            # 重新生成
            encounter_config.generate_encounter_positions()
            encounter_config.save_config()

            QMessageBox.information(self, "成功", "遭遇位置已随机生成！")
            self.refresh_encounters()
            self.config_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"随机生成遭遇失败: {str(e)}")

    def clear_all_config(self):
        """清空所有配置"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "这将清空所有陷阱和遭遇配置，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 清空陷阱
            self.game_service.engine.trap_config.generated_traps.clear()
            self.game_service.engine.trap_config.save_config()

            # 清空遭遇
            encounter_config = getattr(self.game_service.engine, 'encounter_config', None)
            if encounter_config:
                encounter_config.generated_encounters = {}
                encounter_config.save_config()

            QMessageBox.information(self, "成功", "所有配置已清空！")
            self.refresh_config()
            self.config_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空配置失败: {str(e)}")

    def add_trap(self):
        """添加陷阱"""
        dialog = TrapEditorDialog(self, self.game_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_traps()
            self.config_updated.emit()

    def edit_trap(self, trap_name: str):
        """编辑陷阱"""
        dialog = TrapEditorDialog(self, self.game_service, trap_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_traps()
            self.config_updated.emit()

    def delete_trap(self, trap_name: str):
        """删除陷阱"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除陷阱 '{trap_name}' 的所有位置配置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            trap_config = self.game_service.engine.trap_config

            # 删除所有该陷阱的位置
            keys_to_delete = [
                key for key, name in trap_config.generated_traps.items()
                if name == trap_name
            ]

            for key in keys_to_delete:
                del trap_config.generated_traps[key]

            trap_config.save_config()

            QMessageBox.information(self, "成功", f"已删除陷阱 '{trap_name}' 的所有配置")
            self.refresh_traps()
            self.config_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除陷阱失败: {str(e)}")

    def add_encounter(self):
        """添加遭遇"""
        dialog = EncounterEditorDialog(self, self.game_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_encounters()
            self.config_updated.emit()

    def edit_encounter(self, encounter_name: str):
        """编辑遭遇"""
        dialog = EncounterEditorDialog(self, self.game_service, encounter_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_encounters()
            self.config_updated.emit()

    def delete_encounter(self, encounter_name: str):
        """删除遭遇"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除遭遇 '{encounter_name}' 的所有位置配置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            encounter_config = getattr(self.game_service.engine, 'encounter_config', None)
            if not encounter_config:
                return

            # 删除所有该遭遇的位置
            keys_to_delete = [
                key for key, name in encounter_config.generated_encounters.items()
                if name == encounter_name
            ]

            for key in keys_to_delete:
                del encounter_config.generated_encounters[key]

            encounter_config.save_config()

            QMessageBox.information(self, "成功", f"已删除遭遇 '{encounter_name}' 的所有配置")
            self.refresh_encounters()
            self.config_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除遭遇失败: {str(e)}")


class TrapEditorDialog(QDialog):
    """陷阱编辑器对话框"""

    def __init__(self, parent, game_service, trap_name=None):
        super().__init__(parent)
        self.game_service = game_service
        self.trap_name = trap_name
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("陷阱编辑器" if not self.trap_name else f"编辑陷阱: {self.trap_name}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # 陷阱名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("陷阱名称:"))
        self.name_combo = QComboBox()
        # 动态加载陷阱列表
        self.name_combo.addItems(load_available_traps())
        if self.trap_name:
            index = self.name_combo.findText(self.trap_name)
            if index >= 0:
                self.name_combo.setCurrentIndex(index)
                self.name_combo.setEnabled(False)  # 编辑时不允许修改名称
        name_layout.addWidget(self.name_combo)
        layout.addLayout(name_layout)

        # 列号
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("列号 (3-18):"))
        self.column_spin = QSpinBox()
        self.column_spin.setRange(3, 18)
        self.column_spin.setValue(7)
        col_layout.addWidget(self.column_spin)
        layout.addLayout(col_layout)

        # 行号
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("行号 (1-10):"))
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 10)
        self.row_spin.setValue(3)
        row_layout.addWidget(self.row_spin)
        layout.addLayout(row_layout)

        # 批量添加选项
        batch_group = QGroupBox("批量添加")
        batch_layout = QVBoxLayout()

        self.batch_checkbox = QCheckBox("启用批量添加")
        batch_layout.addWidget(self.batch_checkbox)

        # 列范围
        col_range_layout = QHBoxLayout()
        col_range_layout.addWidget(QLabel("列范围:"))
        self.col_start_spin = QSpinBox()
        self.col_start_spin.setRange(3, 18)
        self.col_start_spin.setValue(3)
        col_range_layout.addWidget(self.col_start_spin)
        col_range_layout.addWidget(QLabel("-"))
        self.col_end_spin = QSpinBox()
        self.col_end_spin.setRange(3, 18)
        self.col_end_spin.setValue(18)
        col_range_layout.addWidget(self.col_end_spin)
        batch_layout.addLayout(col_range_layout)

        # 行范围
        row_range_layout = QHBoxLayout()
        row_range_layout.addWidget(QLabel("行范围:"))
        self.row_start_spin = QSpinBox()
        self.row_start_spin.setRange(1, 10)
        self.row_start_spin.setValue(1)
        row_range_layout.addWidget(self.row_start_spin)
        row_range_layout.addWidget(QLabel("-"))
        self.row_end_spin = QSpinBox()
        self.row_end_spin.setRange(1, 10)
        self.row_end_spin.setValue(5)
        row_range_layout.addWidget(self.row_end_spin)
        batch_layout.addLayout(row_range_layout)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        # 按钮
        button_layout = QHBoxLayout()

        save_btn = QPushButton("保存")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save_trap)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def save_trap(self):
        """保存陷阱"""
        try:
            trap_name = self.name_combo.currentText()
            trap_config = self.game_service.engine.trap_config

            if self.batch_checkbox.isChecked():
                # 批量添加
                col_start = self.col_start_spin.value()
                col_end = self.col_end_spin.value()
                row_start = self.row_start_spin.value()
                row_end = self.row_end_spin.value()

                for col in range(col_start, col_end + 1):
                    for row in range(row_start, row_end + 1):
                        pos_key = f"{col}_{row}"
                        trap_config.generated_traps[pos_key] = trap_name
            else:
                # 单个添加
                column = self.column_spin.value()
                row = self.row_spin.value()
                pos_key = f"{column}_{row}"
                trap_config.generated_traps[pos_key] = trap_name

            # 保存配置
            trap_config.save_config()
            self.game_service.engine.update_map_events_from_config()

            QMessageBox.information(self, "成功", f"陷阱 '{trap_name}' 已保存")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存陷阱失败: {str(e)}")


class EncounterEditorDialog(QDialog):
    """遭遇编辑器对话框"""

    def __init__(self, parent, game_service, encounter_name=None):
        super().__init__(parent)
        self.game_service = game_service
        self.encounter_name = encounter_name
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("遭遇编辑器" if not self.encounter_name else f"编辑遭遇: {self.encounter_name}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # 遭遇名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("遭遇名称:"))
        self.name_input = QLineEdit()
        if self.encounter_name:
            self.name_input.setText(self.encounter_name)
            self.name_input.setReadOnly(True)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 列号
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("列号 (3-18):"))
        self.column_spin = QSpinBox()
        self.column_spin.setRange(3, 18)
        self.column_spin.setValue(7)
        col_layout.addWidget(self.column_spin)
        layout.addLayout(col_layout)

        # 行号
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("行号 (1-10):"))
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 10)
        self.row_spin.setValue(3)
        row_layout.addWidget(self.row_spin)
        layout.addLayout(row_layout)

        # 按钮
        button_layout = QHBoxLayout()

        save_btn = QPushButton("保存")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save_encounter)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def save_encounter(self):
        """保存遭遇"""
        try:
            encounter_name = self.name_input.text().strip()
            if not encounter_name:
                QMessageBox.warning(self, "警告", "请输入遭遇名称")
                return

            encounter_config = getattr(self.game_service.engine, 'encounter_config', None)
            if not encounter_config:
                QMessageBox.warning(self, "警告", "遭遇系统未初始化")
                return

            column = self.column_spin.value()
            row = self.row_spin.value()
            pos_key = f"{column}_{row}"

            encounter_config.generated_encounters[pos_key] = encounter_name
            encounter_config.save_config()

            QMessageBox.information(self, "成功", f"遭遇 '{encounter_name}' 已保存")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存遭遇失败: {str(e)}")
