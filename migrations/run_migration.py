"""
数据库迁移工具
运行SQL迁移脚本
"""

import sqlite3
import os
from pathlib import Path


def run_migration(db_path: str = "cant_stop.db", migration_file: str = "001_add_encounter_tables.sql"):
    """运行迁移脚本"""
    # 获取迁移文件路径
    migrations_dir = Path(__file__).parent
    migration_path = migrations_dir / migration_file

    if not migration_path.exists():
        print(f"❌ 迁移文件不存在: {migration_path}")
        return False

    # 连接数据库
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 读取并执行迁移脚本
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 分割并执行每个语句
        statements = migration_sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except sqlite3.Error as e:
                    # 如果是"表已存在"错误，可以忽略
                    if "already exists" not in str(e):
                        print(f"⚠️  警告: {e}")
                        print(f"   语句: {statement[:100]}...")

        conn.commit()
        print(f"✅ 迁移成功: {migration_file}")
        print(f"   数据库: {db_path}")

        # 显示新增的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\n📊 当前数据库表:")
        for table in tables:
            print(f"   - {table[0]}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False


if __name__ == "__main__":
    import sys

    # 获取命令行参数
    db_path = sys.argv[1] if len(sys.argv) > 1 else "cant_stop.db"
    migration_file = sys.argv[2] if len(sys.argv) > 2 else "001_add_encounter_tables.sql"

    print("=" * 60)
    print("🔧 数据库迁移工具")
    print("=" * 60)

    success = run_migration(db_path, migration_file)

    if success:
        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 迁移失败，请检查错误信息")
        print("=" * 60)
        sys.exit(1)
