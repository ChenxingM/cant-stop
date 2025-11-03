@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
echo ============================================
echo Can't Stop 贪骰无厌游戏 - 演示模式
echo ============================================
echo.
python main.py --interface cli --demo
pause