@echo off
REM CBSC Dashboard Frontend 启动脚本 (Windows)

echo 🚀 启动 CBSC Dashboard Frontend 开发服务器...

REM 检查 Node.js 是否安装
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: Node.js 未安装，请先安装 Node.js 20.x 或更高版本
    pause
    exit /b 1
)

REM 检查是否已安装依赖
if not exist "node_modules" (
    echo 📦 安装项目依赖...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查环境变量文件
if not exist ".env.local" (
    echo ⚠️  警告: .env.local 文件不存在，使用默认配置
    copy .env.example .env.local
)

REM 启动开发服务器
echo.
echo 🌟 启动开发服务器...
echo 📍 访问地址: http://localhost:3000
echo 📍 API 地址: http://localhost:3004
echo.
echo 按 Ctrl+C 停止服务器
echo.

npm run dev