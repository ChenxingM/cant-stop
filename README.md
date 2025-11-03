# Can't Stop 贪骰无厌游戏机器人

一个功能完整的Can't Stop骰子游戏机器人，支持多人在线游戏，设计用于QQ群集成和独立测试。

## ✨ 项目特性

### 🎮 完整游戏体验
- 🎲 **完整的Can't Stop游戏逻辑** - 严格按照原版规则实现
- 👥 **多人在线支持** - 支持并发多玩家游戏
- 🏆 **成就和陷阱系统** - 丰富的游戏互动元素
- 🛒 **道具商店系统** - 可购买和使用各种游戏道具
- ⚔️ **阵营系统** - 收养人/Aonreth双阵营玩法

### 💻 多样化界面
- 🖥️ **CLI命令行界面** - 轻量级测试和游戏
- 🎨 **PySide6图形界面** - 直观的可视化游戏体验
- 📱 **QQ消息处理框架** - 完整的群聊机器人支持

### 🏗️ 技术优势
- 💾 **数据持久化** - SQLAlchemy ORM，支持SQLite/PostgreSQL
- 🔧 **模块化架构** - 易于维护和扩展的代码结构
- 📊 **完整日志系统** - 详细的游戏事件记录和错误处理
- ⚙️ **灵活配置** - YAML配置文件，支持运行时调整

## 🚀 快速开始

### 环境要求
- Python 3.11.9+
- 支持的操作系统：Windows/Linux/macOS

### 1. 安装依赖
```bash
git clone <repository-url>
cd cant-stop-bot
pip install -r requirements.txt
```

### 2. 启动程序

本项目提供两个主要入口：

#### 🤖 启动QQ机器人
```bash
# Windows用户（推荐）
start_bot.bat

# 或使用Python命令
python start_bot.py

# 使用指定配置文件
python start_bot.py --config config/lagrange_bot_config.json

# 创建示例配置文件
python start_bot.py --create-example
```

#### 🎮 启动上帝模式GUI（游戏管理界面）
```bash
# Windows用户（推荐）
start_gm.bat

# 或使用Python命令
python start_god_mode.py
```

上帝模式GUI提供：
- 👥 玩家管理 - 添加/查看所有玩家
- 🎮 游戏控制 - 掷骰、结束轮次、修改积分
- 🗺️ 游戏地图 - 实时显示所有玩家位置
- 📊 GM视角 - 游戏统计和详细信息

### 3. 基本游戏流程（QQ群内）

```
选择阵营：收养人      # 注册并选择阵营
轮次开始              # 开始游戏
领取草图奖励1         # 获取积分
掷骰                  # 掷骰子
8,13                  # 选择数值组合
替换永久棋子          # 结束回合
打卡完毕              # 完成打卡
```

## 🎯 游戏玩法

### 核心规则
- **目标**：在任意3列上登顶即可获胜
- **地图**：16列（3-18列），每列长度3-10格不等
- **资源**：每回合消耗10积分掷骰，通过作品打卡获得积分
- **策略**：平衡风险与收益，选择合适的推进路线

### 游戏流程
1. **掷骰阶段**：消耗10积分，获得6个骰子结果
2. **组合选择**：将6个数字分为两组，各自相加得到目标列号
3. **标记移动**：在对应列上放置或移动临时标记
4. **决策阶段**：选择继续掷骰或结束回合保存进度
5. **打卡机制**：结束回合后需要打卡才能开始下轮

### 特色系统
- **陷阱系统**：地图上的特殊位置会触发各种效果
- **道具系统**：可购买和使用的特殊物品
- **成就系统**：隐藏成就解锁额外奖励
- **积分经济**：通过创作获得积分，用于游戏消费

## 📁 项目结构

```
cant-stop-bot/
├── src/
│   ├── core/              # 🎯 核心游戏引擎
│   │   ├── game_engine.py      # 游戏逻辑引擎
│   ├── database/          # 💾 数据持久化
│   │   ├── models.py           # 数据库模型定义
│   │   └── database.py         # 数据库操作管理
│   ├── interfaces/        # 💻 用户界面
│   │   ├── cli.py              # 命令行界面
│   │   └── gui.py              # 图形用户界面
│   ├── services/          # 🔧 业务逻辑服务
│   │   ├── game_service.py     # 游戏服务层
│   │   └── message_processor.py # QQ消息处理
│   ├── models/            # 📋 数据模型
│   │   └── game_models.py      # 游戏数据结构
│   └── utils/             # 🛠️ 工具函数
│       ├── config.py           # 配置管理
│       ├── logger.py           # 日志系统
│       └── exceptions.py       # 异常处理
├── tests/                 # 🧪 单元测试
├── config/                # ⚙️ 配置文件
├── docs/                  # 📚 游戏文档
└── logs/                  # 📄 日志文件
```

## 🏗️ 技术架构

### 核心技术栈
- **Python 3.11.9** - 主要开发语言
- **SQLAlchemy** - ORM数据库操作
- **PySide6** - 跨平台GUI框架
- **asyncio** - 异步并发处理
- **PyYAML** - 配置文件管理
- **pytest** - 单元测试框架

### 架构特点
- **分层架构** - 清晰的业务逻辑分离
- **事件驱动** - 基于事件的游戏状态管理
- **插件化设计** - 易于扩展的消息处理框架
- **配置驱动** - 通过配置文件控制游戏行为

## 🎮 功能演示

### CLI界面演示
```bash
$ python main.py --interface cli
==================================================
🎲 欢迎来到Can't Stop贪骰无厌游戏！🎲
==================================================

[未登录] > register 张三 收养人
✅ 玩家 张三 注册成功，阵营：收养人

[张三] > start
✅ 新游戏开始！输入 '掷骰' 开始第一回合

[张三] > add_score 草图
✅ 您的积分 +20（草图）
当前积分：20

[张三] > roll
🎲 张三的骰点：2 3 4 5 5 6
积分：10 (-10)
可选组合：[(7, 14), (8, 13), (9, 12), (10, 11)]
请选择数值组合（格式：8,13 或单个数字）

[张三] > 8,13
✅ 已移动标记到列: [8, 13]
当前位置：第8列-位置1、第13列-位置1；剩余可放置标记：1
当前永久棋子位置：无
已登顶棋子数：0/3
```

### GUI界面特性
- 🎨 直观的游戏棋盘显示
- 📊 实时进度条和状态更新
- 🖱️ 点击操作，用户友好
- 🎯 可视化的游戏状态反馈

## 🤖 QQ机器人集成

### 支持的消息格式
```python
# 游戏控制指令
"选择阵营：收养人"           # 选择游戏阵营
"轮次开始"                  # 开始新轮次
"掷骰" / ".r6d6"           # 掷骰子
"8,13" / "10"              # 移动标记
"替换永久棋子"              # 结束回合
"查看当前进度"              # 查看状态
"打卡完毕"                  # 完成打卡

# 积分奖励指令
"领取草图奖励1"             # +20积分
"领取精致大图奖励1"         # +150积分
"我超级满意这张图1"         # +30积分

# 查询指令
"排行榜"                    # 查看玩家排行
"帮助"                      # 指令帮助
"道具商店"                  # 查看商店
```

### 集成示例
```python
from src.services.message_processor import QQBotAdapter

adapter = QQBotAdapter()

async def on_group_message(user_id, username, group_id, message):
    response = await adapter.handle_group_message(user_id, username, group_id, message)
    await send_group_message(group_id, response)
```

## 📊 数据管理

### 数据库支持
- **SQLite** - 默认，适合小规模使用
- **PostgreSQL** - 推荐生产环境使用
- **自动迁移** - 使用Alembic管理数据库版本

### 数据模型
- 玩家信息和进度数据
- 游戏会话和临时状态
- 成就解锁和道具库存
- 积分交易历史记录
- 完整的审计日志

## 🧪 测试与质量保证

### 测试覆盖
```bash
# 运行所有测试
pytest tests/ -v

# 查看测试覆盖率
pytest tests/ --cov=src --cov-report=html

# 运行特定测试
pytest tests/test_game_engine.py -v
```

### 代码质量
- 类型提示支持
- 完整的异常处理
- 详细的日志记录
- 模块化设计原则

## ⚙️ 配置与定制

### 配置文件示例
```yaml
# config/default_config.yaml
game:
  dice_cost: 10                 # 每次掷骰消耗积分
  max_temporary_markers: 3      # 最大临时标记数
  win_condition_columns: 3      # 获胜所需完成列数

  score_rewards:
    草图: 20
    精致小图: 80
    精致大图: 150

database:
  url: "sqlite:///cant_stop.db"
  echo: false

logging:
  level: "INFO"
  file: "logs/cant_stop.log"
```

### 自定义扩展
- 新增游戏事件和陷阱
- 自定义积分奖励规则
- 扩展消息处理指令
- 添加新的用户界面

## 📚 文档资源

- [详细使用指南](docs/USAGE.md) - 完整的使用说明
- [游戏规则说明](docs/游戏规则说明书.md) - 官方游戏规则
- [指令参考手册](docs/机器人指令完整手册.md) - 所有可用指令
- [陷阱与成就系统](docs/陷阱与成就系统详解.md) - 特色系统说明
- [数据库设计方案](docs/CantStop数据库设计方案.md) - 技术架构文档
- [上帝模式说明](docs/README_GOD_MODE.md) - GM界面使用指南
- [Claude Code 指南](CLAUDE.md) - AI辅助开发指南

## 🔧 开发状态

### 已完成功能 ✅
- [x] 核心游戏引擎和规则实现
- [x] 完整的数据持久化系统
- [x] CLI和GUI测试界面
- [x] QQ消息处理框架
- [x] 配置管理和日志系统
- [x] 异常处理和错误恢复
- [x] 单元测试和文档

### 后续计划 🚧
- [ ] 更多陷阱和道具实现
- [ ] 实时对战功能
- [ ] Web管理界面
- [ ] 性能优化和监控
- [ ] 多语言支持

## 🤝 贡献指南

欢迎各种形式的贡献！

1. **Bug报告** - 发现问题请创建Issue
2. **功能建议** - 欢迎提出新想法
3. **代码贡献** - Fork项目并提交PR
4. **文档改进** - 完善使用文档和注释

### 开发环境设置
```bash
git clone <repository-url>
cd cant-stop-bot
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋 获取帮助

- 📖 查看 [使用指南](USAGE.md) 获取详细说明
- 🐛 遇到问题请创建 [GitHub Issue](../../issues)
- 💬 讨论和交流欢迎在 [Discussions](../../discussions) 中进行
- 📧 技术支持：[联系方式]

---

**🎲 开始您的Can't Stop贪骰无厌之旅吧！**

记住游戏的核心理念：**贪心有风险，投掷需谨慎！** 在追求胜利的同时，享受策略决策带来的乐趣。