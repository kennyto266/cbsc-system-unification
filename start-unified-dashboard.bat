@echo off
setlocal enabledelayedexpansion

:: CBSC Unified Dashboard 启动脚本 (Windows版本)
:: 自动启动前端Dashboard、后端API和监控系统

echo 🚀 启动 CBSC Unified Dashboard 系统...

:: 检查Python环境
echo [STEP] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python未安装或不在PATH中
    pause
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip未安装
    pause
    exit /b 1
)

echo [INFO] Python环境检查通过

:: 检查Node.js环境
echo [STEP] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js未安装或不在PATH中
    pause
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm未安装
    pause
    exit /b 1
)

echo [INFO] Node.js环境检查通过

:: 创建日志目录
if not exist "logs" mkdir logs

:: 启动后端API服务
echo [STEP] 启动后端API服务 (端口 3004)...
cd src/api
if exist "main.py" (
    start /B python -m uvicorn main:app --reload --port 3004 --host 0.0.0.0
    echo [INFO] 后端API服务启动成功
) else (
    echo [ERROR] 未找到 main.py 文件
    pause
    exit /b 1
)
cd ..\..

:: 等待API服务启动
timeout /t 3 /nobreak >nul

:: 安装前端依赖
echo [STEP] 检查前端依赖...
cd unified-dashboard
if not exist "node_modules" (
    echo [INFO] 安装前端依赖...
    npm install
    if errorlevel 1 (
        echo [ERROR] 前端依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [INFO] 前端依赖已存在，跳过安装
)

:: 启动前端Dashboard
echo [STEP] 启动前端Dashboard (端口 3000)...
start /B npm run dev
echo [INFO] 前端Dashboard启动成功

:: 等待前端服务启动
timeout /t 5 /nobreak >nul

:: 尝试启动监控系统（可选）
echo [STEP] 启动监控系统 (端口 3005)...
if exist "run_strategy_management_dashboard.py" (
    start /B python run_strategy_management_dashboard.py --port 3005
    echo [INFO] 监控系统启动成功
) else (
    echo [WARN] 未找到监控服务，将跳过
)

cd ..

:: 等待监控系统启动
timeout /t 3 /nobreak >nul

:: 检查服务状态
echo [STEP] 检查服务状态...

:: 检查后端API
curl -s http://localhost:3004/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 后端API服务异常
) else (
    echo [INFO] ✅ 后端API服务正常 (http://localhost:3004)
)

:: 检查前端服务
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 前端Dashboard异常
) else (
    echo [INFO] ✅ 前端Dashboard正常 (http://localhost:3000)
)

:: 检查监控系统
curl -s http://localhost:3005 >nul 2>&1
if errorlevel 1 (
    echo [WARN] ⚠️  监控系统未启动或异常
) else (
    echo [INFO] ✅ 监控系统正常 (http://localhost:3005)
)

:: 显示访问信息
echo.
echo 🎉 CBSC Unified Dashboard 系统启动完成！
echo.
echo 📊 主要访问地址：
echo    - 统一Dashboard: http://localhost:3000
echo    - 后端API文档: http://localhost:3004/docs
echo    - API健康检查: http://localhost:3004/health
echo    - 监控系统: http://localhost:3005
echo.
echo 🔐 默认登录信息：
echo    - 用户名: admin
echo    - 密码: admin123
echo.
echo ⚡ 快速命令：
echo    - 查看日志: type logs\*.log
echo    - 停止服务: Ctrl+C 或关闭此窗口
echo.
echo 💡 提示：
echo    - 使用 Ctrl+C 停止所有服务
echo    - 如遇到问题请检查 logs\ 目录下的日志文件
echo.

:: 保持脚本运行
echo [INFO] 系统运行中，按 Ctrl+C 停止所有服务...
pause