#!/usr/bin/env python3
"""
修复数据库缺失列的脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.database.database import get_db_manager
from sqlalchemy import text

def add_missing_columns():
    """添加缺失的数据库列"""
    try:
        db = get_db_manager()

        with db.get_session() as session:
            try:
                # 尝试添加 total_dice_rolls 列
                session.execute(text("ALTER TABLE players ADD COLUMN total_dice_rolls INTEGER DEFAULT 0"))
                print("添加 total_dice_rolls 列成功")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("total_dice_rolls 列已存在")
                else:
                    print(f"添加 total_dice_rolls 列失败: {e}")

            try:
                # 尝试添加 total_turns 列
                session.execute(text("ALTER TABLE players ADD COLUMN total_turns INTEGER DEFAULT 0"))
                print("添加 total_turns 列成功")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("total_turns 列已存在")
                else:
                    print(f"添加 total_turns 列失败: {e}")

            session.commit()
            print("数据库列修复完成！")

    except Exception as e:
        print(f"数据库修复失败: {e}")
        return False

    return True

if __name__ == "__main__":
    print("开始修复数据库...")
    success = add_missing_columns()
    if success:
        print("修复完成，现在可以正常使用GM面板了")
    else:
        print("修复失败，请检查错误信息")