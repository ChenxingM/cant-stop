@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
echo ============================================
echo Can't Stop 贪骰无厌游戏 - CLI界面
echo ============================================
echo.
python main.py --interface cli
pause