# 🤖 CantStop QQ机器人部署指南

本指南将帮助您部署CantStop游戏QQ机器人，使用Lagrange.OneBot作为QQ协议实现。

## 📋 环境要求

### 系统要求
- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8+
- **内存**: 至少512MB可用内存
- **网络**: 稳定的网络连接

### 依赖安装
```bash
# 安装Python依赖
pip install aiohttp asyncio logging pathlib

# 或使用requirements.txt（如果有）
pip install -r requirements.txt
```

---

## 🛠️ 第一步：设置Lagrange.OneBot

### 1. 下载Lagrange.OneBot

访问 [Lagrange.OneBot Releases](https://github.com/LagrangeDev/Lagrange.Core/releases) 下载最新版本：

- **Windows**: `Lagrange.OneBot-win-x64.zip`
- **Linux**: `Lagrange.OneBot-linux-x64.tar.gz`
- **macOS**: `Lagrange.OneBot-osx-x64.tar.gz`

### 2. 配置Lagrange.OneBot

解压后，创建配置文件 `appsettings.json`：

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning",
      "Microsoft.Hosting.Lifetime": "Information"
    }
  },
  "SignServerUrl": "",
  "Account": {
    "Uin": 0,
    "Password": "",
    "Protocol": "Linux",
    "AutoReconnect": true,
    "GetOptimumServer": true
  },
  "Message": {
    "IgnoreSelf": true
  },
  "QrCode": {
    "ConsoleCompatibilityMode": false
  },
  "Implementations": [
    {
      "Type": "ReverseWebSocket",
      "Host": "127.0.0.1",
      "Port": 8080,
      "Suffix": "/onebot",
      "ReconnectInterval": 5000,
      "HeartBeatInterval": 5000,
      "AccessToken": "YOUR_SECRET_TOKEN_HERE"
    },
    {
      "Type": "Http",
      "Host": "127.0.0.1",
      "Port": 3001,
      "AccessToken": "YOUR_SECRET_TOKEN_HERE"
    }
  ]
}
```

**重要说明**:
- `AccessToken`: 访问令牌，用于保护您的机器人安全
- 建议使用复杂的随机字符串作为token（例如：`6}#3xKUJ-?VREQbz`）
- 如果不需要验证，可以留空（不推荐用于生产环境）
- **请妥善保管您的token，不要泄露给他人**

```bash
# 生成随机token的方法（可选）
# Linux/macOS
openssl rand -base64 16

# Python
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 3. 启动Lagrange.OneBot

```bash
# Windows
./Lagrange.OneBot.exe

# Linux/macOS
./Lagrange.OneBot
```

首次启动需要扫码登录QQ账号。

---

## 🎮 第二步：配置CantStop机器人

### 1. 配置机器人

编辑 `config/bot_config.json`（推荐使用统一配置格式）：

```json
{
  "platform": "lagrange",
  "websocket": {
    "url": "ws://127.0.0.2:8081/onebot/v11/ws",
    "access_token": "YOUR_SECRET_TOKEN_HERE",
    "reconnect": true,
    "timeout": 30
  },
  "bot": {
    "allowed_groups": [541674420, 329182491],
    "admin_users": [1234567890],
    "auto_register": true,
    "default_faction": "收养人"
  }
}
```

**或使用旧版配置** `config/qq_bot_config.json`：

```json
{
  "onebot": {
    "url": "http://127.0.0.1:3001",
    "timeout": 30
  },
  "bot": {
    "listen_host": "127.0.0.1",
    "listen_port": 8080,
    "allowed_groups": ["123456789", "987654321"],
    "admin_users": ["1234567890"],
    "auto_register": true
  },
  "message": {
    "use_emoji": true,
    "max_length": 1000,
    "compact_mode": false,
    "mention_user": false,
    "welcome_new_users": true
  },
  "logging": {
    "level": "INFO",
    "file": "logs/qq_bot.log"
  }
}
```

### 2. 配置说明

#### WebSocket配置（统一配置格式）
- `url`: WebSocket连接地址
- `access_token`: 访问令牌，**必须与Lagrange.OneBot配置中的AccessToken一致**
- `reconnect`: 是否自动重连
- `timeout`: 连接超时时间（秒）

**重要**: `access_token` 必须与 Lagrange.OneBot 的 `appsettings.json` 中配置的 `AccessToken` 完全一致，否则连接会被拒绝。

#### OneBot配置（旧版格式）
- `url`: Lagrange.OneBot的HTTP API地址
- `timeout`: API请求超时时间

#### 机器人配置
- `listen_host/port`: 机器人监听地址（接收OneBot回调）
- `allowed_groups`: 允许的QQ群号列表（空数组表示所有群）
- `admin_users`: 管理员QQ号列表
- `auto_register`: 是否自动注册新用户
- `default_faction`: 默认阵营（收养人/Aonreth）

#### 消息配置
- `use_emoji`: 是否使用emoji
- `max_length`: 消息最大长度
- `compact_mode`: 紧凑模式（简化输出）
- `mention_user`: 是否@用户
- `welcome_new_users`: 是否欢迎新用户

---

## 🚀 第三步：启动机器人

### 方法1: 使用统一启动器（推荐）

```bash
# 进入项目目录
cd cant-stop-bot

# 使用默认配置启动
python start_bot.py

# 指定配置文件
python start_bot.py --config config/bot_config.json

# 创建示例配置文件
python start_bot.py --create-example

# 使用Windows批处理脚本
start_bot.bat
```

### 方法2: 使用旧版启动器

```bash
# 启动机器人
python -m src.bots.bot_launcher

# 或指定配置文件
python -m src.bots.bot_launcher -c config/qq_bot_config.json

# 查看状态
python -m src.bots.bot_launcher --status

# 创建默认配置
python -m src.bots.bot_launcher --create-config
```

### 方法2: 直接运行

```python
# run_qq_bot.py
import asyncio
from src.bots.qq_bot import QQBot

async def main():
    bot = QQBot(
        onebot_url="http://127.0.0.1:3001",
        listen_host="127.0.0.1",
        listen_port=8080
    )

    # 设置允许的群（可选）
    bot.set_allowed_groups(["123456789"])

    # 设置管理员（可选）
    bot.set_admin_users(["1234567890"])

    await bot.start()

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔧 配置优化

### 群组管理

```json
{
  "bot": {
    "allowed_groups": [
      "123456789",  // 测试群
      "987654321"   // 正式群
    ],
    "admin_users": [
      "1234567890"  // 你的QQ号
    ]
  }
}
```

### 消息样式优化

```json
{
  "message": {
    "use_emoji": true,        // 手机用户建议true
    "max_length": 800,        // 避免消息过长
    "compact_mode": false,    // 群聊人多时可设为true
    "mention_user": false,    // 避免频繁@用户
    "welcome_new_users": true // 自动欢迎新成员
  }
}
```

### 性能优化

```json
{
  "game": {
    "rate_limit": {
      "enabled": true,
      "max_commands_per_minute": 10  // 限制指令频率
    }
  },
  "logging": {
    "level": "INFO",     // 生产环境建议INFO
    "file": "logs/qq_bot.log",
    "max_size": "10MB",  // 日志文件大小限制
    "backup_count": 5    // 保留日志文件数量
  }
}
```

---

## 🎮 使用指南

### 用户指令

```
# 基础游戏
help - 显示帮助
轮次开始 - 开始新轮次
.r6d6 - 掷骰子
8,13 - 移动棋子
替换永久棋子 - 结束轮次
查看当前进度 - 查看状态

# 奖励系统
领取草图奖励1 - 领取奖励
我超级满意这张图1 - 超常发挥奖励

# 商店系统
道具商店 - 查看商店
购买丑喵玩偶 - 购买道具
```

### 管理员指令

```
reset_all - 重置所有数据（需确认）
trap_config - 查看陷阱配置
set_trap 小小火球术 3,4,5 - 设置陷阱
regenerate_traps - 重新生成陷阱
```

---

## 🐛 故障排除

### 常见问题

#### 0. WebSocket连接失败/401错误
```bash
# 检查access_token是否一致
# 1. 查看Lagrange.OneBot的配置
cat appsettings.json | grep AccessToken

# 2. 查看机器人配置
cat config/bot_config.json | grep access_token

# 3. 确保两个token完全一致（包括大小写）
# 4. 如果不需要验证，可以将两边的token都设为空字符串或null
```

**常见错误**:
- ❌ 连接被拒绝: token不匹配
- ❌ 401 Unauthorized: token验证失败
- ✅ 连接成功: token一致或都为空

#### 1. 机器人无响应
```bash
# 检查OneBot状态
curl http://127.0.0.1:3001/get_status

# 检查机器人日志
tail -f logs/qq_bot.log

# 检查端口占用
netstat -an | grep 8080
```

#### 2. 消息发送失败
```bash
# 检查OneBot配置
cat appsettings.json

# 测试API连接
curl -X POST http://127.0.0.1:3001/send_group_msg \
  -H "Content-Type: application/json" \
  -d '{"group_id": 123456789, "message": "test"}'
```

#### 3. 数据库错误
```bash
# 检查数据库文件权限
ls -la data/

# 重新初始化数据库
python -c "from src.database.database import get_db_manager; get_db_manager().init_db()"
```

### 网络配置

#### 端口映射
如果部署在服务器上：
```bash
# 确保防火墙开放端口
ufw allow 8080

# 或使用iptables
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

#### 反向代理（可选）
使用nginx代理：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /cantstop-bot {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 监控和维护

### 日志监控

```bash
# 实时查看日志
tail -f logs/qq_bot.log

# 查看错误日志
grep "ERROR" logs/qq_bot.log

# 统计消息数量
grep "收到消息" logs/qq_bot.log | wc -l
```

### 性能监控

```python
# 添加到机器人代码中
import psutil
import time

def log_system_stats():
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()

    print(f"CPU使用率: {cpu_percent}%")
    print(f"内存使用率: {memory_info.percent}%")
    print(f"活跃用户数: {len(bot.user_info)}")
```

### 自动重启脚本

```bash
#!/bin/bash
# restart_bot.sh

while true; do
    echo "启动机器人..."
    python -m src.bots.bot_launcher

    echo "机器人意外退出，5秒后重启..."
    sleep 5
done
```

---

## 🚀 生产环境部署

### 使用systemd（Linux）

创建服务文件 `/etc/systemd/system/cantstop-bot.service`：

```ini
[Unit]
Description=CantStop QQ Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/cant-stop-bot
ExecStart=/usr/bin/python3 -m src.bots.bot_launcher
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable cantstop-bot
sudo systemctl start cantstop-bot
sudo systemctl status cantstop-bot
```

### 使用Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "-m", "src.bots.bot_launcher"]
```

构建和运行：
```bash
docker build -t cantstop-bot .
docker run -d -p 8080:8080 -v ./config:/app/config cantstop-bot
```

---

## 📞 技术支持

### 获取帮助
1. 查看日志文件了解详细错误信息
2. 检查Lagrange.OneBot的GitHub Issues
3. 验证配置文件格式正确性

### 常用调试命令
```bash
# 测试机器人状态
python -m src.bots.bot_launcher --status

# 创建新配置
python -m src.bots.bot_launcher --create-config

# 验证OneBot连接
curl http://127.0.0.1:3001/get_status
```

现在您的CantStop QQ机器人已经可以正常运行了！🎉

用户可以在QQ群中使用游戏指令，享受完整的CantStop游戏体验。