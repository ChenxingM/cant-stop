# Scripts 目录

本目录包含开发和维护工具脚本。

## 工具脚本

### 测试和开发
- **main.py** - 原始CLI/GUI启动器（已被根目录的 `start_bot.py` 和 `start_god_mode.py` 替代）
- **start_gui.py** - 独立GUI启动器（用于测试GUI界面）
- **demo.bat** - 演示模式批处理文件
- **add_test_data.py** - 添加测试数据到数据库

### 机器人启动器（旧版）
- **run_lagrange_bot.py** - Lagrange机器人启动器
- **run_qq_bot.py** - QQ机器人启动器

**注意**：推荐使用根目录的 `start_bot.py` 统一启动机器人。

### 维护工具
- **fix_database.py** - 数据库修复工具

## 使用建议

### 开发测试GUI
如果需要快速测试GUI界面而不是完整的上帝模式：
```bash
python scripts/start_gui.py
```

### 添加测试数据
在开发环境中添加测试玩家和游戏数据：
```bash
python scripts/add_test_data.py
```

### 修复数据库
当数据库出现问题时：
```bash
python scripts/fix_database.py
```

### 使用旧版机器人启动器
如果需要使用特定的旧版启动器：
```bash
python scripts/run_lagrange_bot.py
python scripts/run_qq_bot.py
```

## 迁移说明

从旧版脚本迁移到新版启动器：

**旧版**：
```bash
python run_lagrange_bot.py
python start_god_mode.py
```

**新版**（推荐）：
```bash
python start_bot.py            # 统一的机器人启动器
python start_god_mode.py       # 上帝模式（位置不变）
```

或使用批处理文件：
```bash
start_bot.bat                  # Windows
start_gm.bat                   # Windows
```
