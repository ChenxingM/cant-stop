    def _init_map_events(self):
        """初始化地图事件"""
        # 使用陷阱配置管理器生成陷阱位置
        self.regenerate_traps()

        # 添加固定的道具和遇事件
        fixed_events = [
            # 道具示例
            {"column": 7, "position": 4, "type": EventType.ITEM, "name": "传送卷轴"},
            {"column": 9, "position": 6, "type": EventType.ITEM, "name": "幸运符"},
            # 遇事件
            {"column": 13, "position": 5, "type": EventType.ENCOUNTER, "name": "神秘商人"},
            {"column": 16, "position": 3, "type": EventType.ENCOUNTER, "name": "古老遗迹"},
        ]

        for event_data in fixed_events:
            event_key = f"{event_data['column']}_{event_data['position']}"
            event = MapEvent(
                event_id=event_key,
                column=event_data['column'],
                position=event_data['position'],
                event_type=event_data['type'],
                name=event_data['name'],
                description=f"{event_data['name']}事件",
            )

            if event_key not in self.map_events:
                self.map_events[event_key] = []
            self.map_events[event_key].append(event)

    def regenerate_traps(self):
        """重新生成陷阱位置"""
        # 清除现有陷阱事件
        trap_keys = []
        for key, events in self.map_events.items():
            self.map_events[key] = [event for event in events if event.event_type != EventType.TRAP]
            if not self.map_events[key]:
                trap_keys.append(key)

        # 移除空的事件列表
        for key in trap_keys:
            del self.map_events[key]

        # 生成新的陷阱位置
        trap_positions = self.trap_config.generate_trap_positions()

        for position_key, trap_name in trap_positions.items():
            column, position = position_key.split('_')
            column, position = int(column), int(position)

            event = MapEvent(
                event_id=position_key,
                column=column,
                position=position,
                event_type=EventType.TRAP,
                name=trap_name,
                description=f"{trap_name}陷阱",
            )

            if position_key not in self.map_events:
                self.map_events[position_key] = []
            self.map_events[position_key].append(event)