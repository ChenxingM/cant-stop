@echo off
chcp 65001 >nul 2>&1

set PYTHONIOENCODING=utf-8
echo ============================================
echo Can't Stop 贪骰无厌游戏 - GUI界面
echo ============================================
echo.
echo 正在启动GUI界面...
python main.py --interface gui
pause