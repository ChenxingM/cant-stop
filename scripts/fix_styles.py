#!/usr/bin/env python3
"""
修复GUI样式 - 将所有彩色背景改为白色，所有彩色文字改为黑色
"""

import re
import sys
import os

def fix_styles_in_file(filepath):
    """修复文件中的样式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换所有background-color为白色或浅灰色
    patterns = [
        # 各种绿色背景 -> 白色
        (r'background-color:\s*#28a745', 'background-color: white'),
        (r'background-color:\s*#1e7e34', 'background-color: #f0f0f0'),
        (r'background-color:\s*#155724', 'background-color: #e0e0e0'),
        (r'background-color:\s*#c8e6c9', 'background-color: white'),

        # 各种蓝色背景 -> 白色
        (r'background-color:\s*#007bff', 'background-color: white'),
        (r'background-color:\s*#0056b3', 'background-color: #f0f0f0'),
        (r'background-color:\s*#004085', 'background-color: #e0e0e0'),
        (r'background-color:\s*#2c5aa0', 'background-color: white'),
        (r'background-color:\s*#e3f2fd', 'background-color: white'),
        (r'background-color:\s*#17a2b8', 'background-color: white'),
        (r'background-color:\s*#138496', 'background-color: #f0f0f0'),
        (r'background-color:\s*#117a8b', 'background-color: #e0e0e0'),

        # 各种黄色/橙色背景 -> 白色
        (r'background-color:\s*#ffc107', 'background-color: white'),
        (r'background-color:\s*#e0a800', 'background-color: #f0f0f0'),
        (r'background-color:\s*#d39e00', 'background-color: #e0e0e0'),
        (r'background-color:\s*#fff3e0', 'background-color: white'),
        (r'background-color:\s*#ffecb3', 'background-color: white'),

        # 各种红色背景 -> 白色
        (r'background-color:\s*#dc3545', 'background-color: white'),
        (r'background-color:\s*#c82333', 'background-color: #f0f0f0'),
        (r'background-color:\s*#bd2130', 'background-color: #e0e0e0'),

        # 各种灰色/其他背景
        (r'background-color:\s*#6c757d', 'background-color: white'),
        (r'background-color:\s*#545b62', 'background-color: #f0f0f0'),
        (r'background-color:\s*#f5f5f5', 'background-color: white'),
        (r'background-color:\s*#f8f9fa', 'background-color: white'),
        (r'background-color:\s*#e9ecef', 'background-color: white'),
        (r'background-color:\s*#f0f8ff', 'background-color: white'),
        (r'background:\s*#f5f5f5', 'background: white'),
        (r'background:\s*#f0f8ff', 'background: white'),
        (r'background:\s*#343a40', 'background: white'),
        (r'background:\s*#495057', 'background: white'),

        # 文字颜色 -> 黑色
        (r'color:\s*#2c5aa0', 'color: black'),
        (r'color:\s*#28a745', 'color: black'),
        (r'color:\s*#1e7e34', 'color: black'),
        (r'color:\s*white(?!-)', 'color: black'),  # 不匹配white-space
        (r'color:\s*#ffffff', 'color: black'),
        (r'color:\s*#adb5bd', 'color: black'),
        (r'color:\s*#6c757d', 'color: black'),
        (r'color:\s*#555', 'color: black'),
        (r'color:\s*#212529', 'color: black'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已处理: {filepath}")

if __name__ == "__main__":
    # 处理god_mode_gui.py
    god_mode_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'interfaces', 'god_mode_gui.py')
    fix_styles_in_file(god_mode_file)

    # 处理gm_panel.py
    gm_panel_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'interfaces', 'gm_panel.py')
    fix_styles_in_file(gm_panel_file)

    print("\n✅ 所有样式修复完成！")
