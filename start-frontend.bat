@echo off
chcp 65001 > NUL
echo ========================================
echo CBSC 前端服务启动脚本
echo ========================================
echo.

cd /d "%~dp0frontend"

echo 当前目录: %CD%
echo.
echo 正在启动 Vite 开发服务器...
echo.

echo 服务地址: http://localhost:3000
echo 按 Ctrl+C 可以停止服务
echo.
echo ========================================

npm run dev

pause
