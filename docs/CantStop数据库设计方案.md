# 🗄️ CantStop 数据库设计方案

## 数据库选择建议

### 推荐方案：PostgreSQL
- **优势**：强大的JSON支持、事务安全、高并发性能
- **适用场景**：中大型多人在线游戏
- **扩展性**：支持水平扩展和读写分离

### 备选方案：SQLite + Redis
- **SQLite**：用于持久化存储
- **Redis**：用于缓存和实时数据
- **适用场景**：中小型群组机器人

## 📋 数据库表结构设计

### 1. 玩家基础信息表 (players)
```sql
CREATE TABLE players (
    player_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    faction ENUM('收养人', 'Aeonreth') NOT NULL,
    current_score INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 索引优化
CREATE INDEX idx_players_faction ON players(faction);
CREATE INDEX idx_players_score ON players(current_score DESC);
CREATE INDEX idx_players_last_active ON players(last_active);
```

### 2. 游戏会话表 (game_sessions)
```sql
CREATE TABLE game_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(player_id),
    session_state ENUM('active', 'paused', 'completed', 'failed') DEFAULT 'active',
    current_turn_number INTEGER DEFAULT 1,
    dice_results JSON, -- [1,2,3,4,5,6]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

CREATE INDEX idx_sessions_player ON game_sessions(player_id);
CREATE INDEX idx_sessions_state ON game_sessions(session_state);
```

### 3. 玩家进度表 (player_progress)
```sql
CREATE TABLE player_progress (
    progress_id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(player_id),
    column_number INTEGER CHECK (column_number BETWEEN 3 AND 18),
    permanent_progress INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(player_id, column_number)
);

CREATE INDEX idx_progress_player ON player_progress(player_id);
CREATE INDEX idx_progress_column ON player_progress(column_number);
CREATE INDEX idx_progress_completed ON player_progress(is_completed, completed_at);
```

### 4. 临时标记表 (temporary_markers)
```sql
CREATE TABLE temporary_markers (
    marker_id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES game_sessions(session_id),
    column_number INTEGER CHECK (column_number BETWEEN 3 AND 18),
    current_position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(session_id, column_number)
);

CREATE INDEX idx_markers_session ON temporary_markers(session_id);
```

### 5. 首达记录表 (first_completions)
```sql
CREATE TABLE first_completions (
    completion_id SERIAL PRIMARY KEY,
    column_number INTEGER UNIQUE CHECK (column_number BETWEEN 3 AND 18),
    player_id VARCHAR(50) REFERENCES players(player_id),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reward_given BOOLEAN DEFAULT false
);

CREATE INDEX idx_first_completions_column ON first_completions(column_number);
```

### 6. 道具库存表 (player_inventory)
```sql
CREATE TABLE player_inventory (
    inventory_id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(player_id),
    item_name VARCHAR(100) NOT NULL,
    item_type ENUM('consumable', 'permanent', 'achievement_reward'),
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_count INTEGER DEFAULT 0,
    
    UNIQUE(player_id, item_name)
);

CREATE INDEX idx_inventory_player ON player_inventory(player_id);
CREATE INDEX idx_inventory_type ON player_inventory(item_type);
```

### 7. 成就记录表 (player_achievements)
```sql
CREATE TABLE player_achievements (
    achievement_id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(player_id),
    achievement_name VARCHAR(100) NOT NULL,
    achievement_category ENUM('倒霉类', '挑战类', '收集类', '特殊类'),
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reward_claimed BOOLEAN DEFAULT false,
    
    UNIQUE(player_id, achievement_name)
);

CREATE INDEX idx_achievements_player ON player_achievements(player_id);
CREATE INDEX idx_achievements_category ON player_achievements(achievement_category);
```

### 8. 游戏日志表 (game_logs)
```sql
CREATE TABLE game_logs (
    log_id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(player_id),
    session_id VARCHAR(50) REFERENCES game_sessions(session_id),
    action_type ENUM('dice_roll', 'move_marker', 'end_turn', 'trigger_trap', 'use_item', 'complete_column'),
    action_data JSON, -- 详细的动作数据
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_player ON game_logs(player_id);
CREATE INDEX idx_logs_timestamp ON game_logs(timestamp);
CREATE INDEX idx_logs_action ON game_logs(action_type);
```

### 9. 地图事件表 (map_events)
```sql
CREATE TABLE map_events (
    event_id SERIAL PRIMARY KEY,
    column_number INTEGER CHECK (column_number BETWEEN 3 AND 18),
    position INTEGER CHECK (position >= 1),
    event_type ENUM('trap', 'item', 'encounter', 'reward'),
    event_name VARCHAR(100) NOT NULL,
    event_data JSON, -- 事件配置数据
    faction_specific VARCHAR(20) NULL, -- 特定阵营才能触发
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(column_number, position)
);

CREATE INDEX idx_events_position ON map_events(column_number, position);
CREATE INDEX idx_events_type ON map_events(event_type);
```

### 10. 积分交易记录表 (score_transactions)
```sql
CREATE TABLE score_transactions (
    transaction_id SERIAL PRIMARY KEY,
    player_id VARCHAR(50) REFERENCES players(player_id),
    transaction_type ENUM('earn', 'spend'),
    amount INTEGER NOT NULL,
    source ENUM('artwork', 'map_reward', 'dice_cost', 'item_purchase', 'achievement'),
    description TEXT,
    transaction_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_player ON score_transactions(player_id);
CREATE INDEX idx_transactions_type ON score_transactions(transaction_type);
CREATE INDEX idx_transactions_timestamp ON score_transactions(timestamp);
```

## 🔧 核心查询示例

### 玩家状态查询
```sql
-- 获取玩家完整游戏状态
SELECT 
    p.username,
    p.current_score,
    p.faction,
    COALESCE(active_session.session_id, NULL) as current_session,
    COUNT(prog.column_number) as completed_columns,
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'column', prog.column_number,
            'progress', prog.permanent_progress,
            'completed', prog.is_completed
        )
    ) as progress_data
FROM players p
LEFT JOIN game_sessions active_session ON 
    p.player_id = active_session.player_id AND 
    active_session.session_state = 'active'
LEFT JOIN player_progress prog ON p.player_id = prog.player_id
WHERE p.player_id = $1
GROUP BY p.player_id, active_session.session_id;
```

### 排行榜查询
```sql
-- 获取玩家排行榜
SELECT 
    ROW_NUMBER() OVER (ORDER BY completed_columns DESC, current_score DESC) as rank,
    username,
    faction,
    current_score,
    completed_columns,
    games_won,
    ROUND((games_won::FLOAT / NULLIF(games_played, 0)) * 100, 2) as win_rate
FROM (
    SELECT 
        p.*,
        COUNT(prog.column_number) FILTER (WHERE prog.is_completed = true) as completed_columns
    FROM players p
    LEFT JOIN player_progress prog ON p.player_id = prog.player_id
    WHERE p.is_active = true
    GROUP BY p.player_id
) ranked_players
ORDER BY rank
LIMIT 20;
```

### 临时标记状态查询
```sql
-- 获取当前会话的临时标记
SELECT 
    tm.column_number,
    tm.current_position,
    COALESCE(pp.permanent_progress, 0) as permanent_progress,
    (tm.current_position + COALESCE(pp.permanent_progress, 0)) as total_progress
FROM temporary_markers tm
LEFT JOIN player_progress pp ON 
    tm.column_number = pp.column_number AND 
    pp.player_id = (
        SELECT player_id FROM game_sessions 
        WHERE session_id = tm.session_id
    )
WHERE tm.session_id = $1
ORDER BY tm.column_number;
```

## 🚀 性能优化策略

### 1. 数据库配置优化
```sql
-- PostgreSQL 配置建议
shared_buffers = '256MB'           -- 共享缓冲区
effective_cache_size = '1GB'       -- 有效缓存大小
work_mem = '4MB'                   -- 工作内存
maintenance_work_mem = '64MB'      -- 维护工作内存
checkpoint_completion_target = 0.9  -- 检查点完成目标
wal_buffers = '16MB'               -- WAL缓冲区
```

### 2. 连接池配置
```python
# Python 连接池示例 (psycopg2)
from psycopg2 import pool

db_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=5,      # 最小连接数
    maxconn=20,     # 最大连接数
    host="localhost",
    database="cantstop",
    user="cantstop_user",
    password="secure_password"
)
```

### 3. 缓存策略
```python
# Redis 缓存示例
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_player_state(player_id):
    # 尝试从缓存获取
    cached = redis_client.get(f"player:{player_id}")
    if cached:
        return json.loads(cached)
    
    # 从数据库查询
    player_data = query_player_from_db(player_id)
    
    # 缓存结果（5分钟过期）
    redis_client.setex(
        f"player:{player_id}", 
        300, 
        json.dumps(player_data)
    )
    
    return player_data
```

## 📊 数据备份与恢复

### 自动备份脚本
```bash
#!/bin/bash
# PostgreSQL 自动备份脚本

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cantstop"
DB_NAME="cantstop"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -h localhost -U cantstop_user -d $DB_NAME > $BACKUP_DIR/cantstop_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/cantstop_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: cantstop_$DATE.sql.gz"
```

## 🔒 安全性考虑

### 1. 访问控制
```sql
-- 创建专用用户
CREATE USER cantstop_app WITH PASSWORD 'secure_random_password';

-- 授予必要权限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cantstop_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cantstop_app;

-- 禁止危险操作
REVOKE DROP, CREATE ON SCHEMA public FROM cantstop_app;
```

### 2. SQL注入防护
```python
# 使用参数化查询
def update_player_score(player_id, score_change):
    cursor.execute(
        "UPDATE players SET current_score = current_score + %s WHERE player_id = %s",
        (score_change, player_id)
    )
```

## 📈 监控和维护

### 1. 性能监控查询
```sql
-- 查看慢查询
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. 数据清理策略
```sql
-- 清理过期的游戏会话（30天前）
DELETE FROM temporary_markers 
WHERE session_id IN (
    SELECT session_id FROM game_sessions 
    WHERE updated_at < NOW() - INTERVAL '30 days' 
    AND session_state IN ('completed', 'failed')
);

-- 归档历史日志（保留最近3个月）
CREATE TABLE game_logs_archive AS 
SELECT * FROM game_logs 
WHERE timestamp < NOW() - INTERVAL '3 months';

DELETE FROM game_logs 
WHERE timestamp < NOW() - INTERVAL '3 months';
```

---

## 总结建议

1. **推荐使用PostgreSQL**：对于CantStop这样的多人游戏，PostgreSQL提供了最佳的性能和可靠性平衡

2. **实施缓存策略**：使用Redis缓存频繁访问的数据，如玩家状态、排行榜等

3. **定期维护**：设置自动备份、性能监控和数据清理任务

4. **安全第一**：实施适当的访问控制和输入验证

5. **逐步迁移**：可以先从文件存储开始，随着用户量增长再迁移到数据库

这样的数据库设计能够支持数百甚至数千名并发玩家，同时保证数据的一致性和系统的稳定性。
