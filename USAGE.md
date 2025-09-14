# Can't Stop 游戏使用指南

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行CLI界面

```bash
# Windows用户（推荐）
set PYTHONIOENCODING=utf-8
python main.py --interface cli --demo  # 演示模式
python main.py --interface cli         # 正常游戏

# Linux/Mac用户
export PYTHONIOENCODING=utf-8
python main.py --interface cli --demo  # 演示模式
python main.py --interface cli         # 正常游戏
```

### 运行GUI界面

```bash
# 需要先安装PySide6
pip install PySide6

# Windows用户
set PYTHONIOENCODING=utf-8
python main.py --interface gui

# Linux/Mac用户
export PYTHONIOENCODING=utf-8
python main.py --interface gui
```

## 🎮 游戏玩法

### 1. 注册玩家

在CLI中输入：
```
register <用户名> <阵营>
```

示例：
```
register 张三 收养人
register 李四 Aonreth
```

### 2. 开始游戏

```
start
```

### 3. 游戏流程

#### 掷骰子
```
roll
# 或
掷骰
# 或
.r6d6
```

每次掷骰消耗10积分，得到6个1-6的随机数。

#### 选择数值组合

将6个数字分为两组（每组3个），分别相加得到两个数字：

```
8,13      # 双数值组合
10        # 单数值组合
```

#### 继续或结束

- 继续投掷：`continue` 或 `继续`
- 结束回合：`end` 或 `替换永久棋子`

#### 完成打卡

主动结束回合后需要打卡：
```
checkin
# 或
打卡完毕
```

### 4. 查看状态

```
status          # 查看游戏状态
progress        # 查看当前进度
查看当前进度     # 中文指令
```

### 5. 积分管理

```bash
# 不同类型的作品奖励
add_score 草图           # +20积分
add_score 精致小图       # +80积分
add_score 精草大图       # +100积分
add_score 精致大图       # +150积分
add_score 超常发挥       # +30积分
```

### 6. 查看排行榜

```
leaderboard
# 或
排行榜
```

## 🎯 游戏规则详解

### 基本规则

1. **目标**：在任意3列上登顶即可获胜
2. **地图**：16列（3-18），每列长度不同
3. **标记**：每玩家最多同时使用3个临时标记
4. **积分**：每回合消耗10积分掷骰

### 列长度分布

```
列号:  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18
长度:  3  4  5  6  7  8  9  10 10  9  8  7  6  5  4  3
```

### 特殊规则

- **首轮规则**：必须选择两个数值放置两个标记
- **移动强制**：每回合必须移动所有能移动的标记
- **被动停止**：无法移动任何标记且已有3个标记时，清空所有进度
- **登顶保护**：已完成的列无法再放置标记

### 概率策略

#### 容易达成的列
- **第10、11列**：10格，组合数最多（27种）
- **第7-9、12-14列**：中等长度，平衡选择

#### 高风险高回报
- **第3、18列**：仅3格，但只有1种组合可达成
- **第4、17列**：4格，3种组合

## 🛠️ 高级功能

### 配置文件

编辑 `config/default_config.yaml` 自定义游戏设置：

```yaml
game:
  dice_cost: 10                    # 掷骰消耗
  max_temporary_markers: 3         # 最大临时标记数
  win_condition_columns: 3         # 获胜所需列数

  score_rewards:
    草图: 20
    精致小图: 80
    精草大图: 100
    精致大图: 150
    超常发挥: 30
```

### 数据库管理

游戏数据默认存储在 `cant_stop.db` SQLite文件中。

查看数据：
```bash
sqlite3 cant_stop.db
.tables              # 查看表结构
SELECT * FROM players;  # 查看玩家数据
```

### 开发模式

在配置文件中启用：
```yaml
development:
  debug: true
  test_mode: true
  mock_dice: true      # 使用固定骰子结果测试
```

## 🤖 QQ机器人集成

### 消息处理框架

项目提供了完整的消息处理框架，支持：

- 指令解析和路由
- 用户权限管理
- 频率限制
- 错误处理

### 集成示例

```python
from src.services.message_processor import QQBotAdapter

# 创建适配器
adapter = QQBotAdapter()

# 处理群消息
async def handle_group_message(user_id, username, group_id, message):
    response = await adapter.handle_group_message(user_id, username, group_id, message)
    return response

# 处理私聊消息
async def handle_private_message(user_id, username, message):
    response = await adapter.handle_private_message(user_id, username, message)
    return response
```

支持的指令格式：

```python
# 游戏指令
"选择阵营：收养人"
"轮次开始"
"掷骰" / ".r6d6"
"8,13" / "10"
"替换永久棋子"
"查看当前进度"
"打卡完毕"

# 积分指令
"领取草图奖励1"
"我超级满意这张图1"

# 查询指令
"排行榜"
"帮助"
"道具商店"
```

## 🧪 测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_game_engine.py -v
pytest tests/test_message_processor.py -v
```

### 测试覆盖率

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

## 🔧 故障排除

### 常见问题

1. **数据库锁定**
   ```bash
   # 停止所有相关进程，删除数据库文件重新开始
   rm cant_stop.db
   ```

2. **PySide6安装失败**
   ```bash
   # Windows
   pip install PySide6 --upgrade

   # Linux需要额外依赖
   sudo apt-get install python3-pyqt5-dev-tools
   ```

3. **配置文件错误**
   ```bash
   # 删除自定义配置，使用默认配置
   rm config/config.yaml
   ```

### 日志查看

日志默认保存在 `logs/cant_stop.log`：

```bash
# 实时查看日志
tail -f logs/cant_stop.log

# 查看错误日志
grep ERROR logs/cant_stop.log
```

## 📈 性能优化

### 数据库优化

1. **定期清理**：游戏会自动清理7天前的已完成会话
2. **索引优化**：数据库已配置适当的索引
3. **连接池**：使用连接池管理数据库连接

### 内存管理

1. **会话清理**：及时清理无效会话
2. **缓存策略**：合理使用缓存减少数据库查询
3. **日志轮转**：自动轮转日志文件防止过大

## 🔒 安全考虑

### 数据安全

- 使用参数化查询防止SQL注入
- 输入验证和清理
- 访问权限控制

### 频率限制

配置文件中设置：
```yaml
security:
  rate_limiting:
    enabled: true
    max_requests_per_minute: 30
```

### 数据备份

自动备份功能：
```yaml
security:
  backup:
    enabled: true
    interval_hours: 6
    max_backups: 10
```

## 🎨 自定义扩展

### 添加新的游戏事件

在 `src/core/game_engine.py` 中的 `_init_map_events` 方法中添加：

```python
events.append({
    "column": 7,
    "position": 4,
    "type": EventType.TRAP,
    "name": "新陷阱"
})
```

### 添加新的积分奖励

在配置文件中添加：
```yaml
game:
  score_rewards:
    新作品类型: 50
```

### 自定义消息处理

在 `src/services/message_processor.py` 中添加新的处理器：

```python
def _handle_new_command(self, message: UserMessage) -> BotResponse:
    # 处理新指令
    return BotResponse(content="处理结果", message_type=MessageType.COMMAND)

# 注册处理器
self.command_handlers["新指令"] = self._handle_new_command
```

---

## 📞 获取帮助

如果遇到问题或需要帮助：

1. 查看 [游戏规则说明书](docs/游戏规则说明书.md)
2. 参考 [机器人指令手册](docs/机器人指令完整手册.md)
3. 查看测试用例了解使用方法
4. 检查日志文件获取错误信息

祝您游戏愉快！🎲