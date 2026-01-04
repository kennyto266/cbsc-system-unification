@echo off
chcp 65001 > NUL
echo ========================================
echo CBSC 前端诊断工具
echo ========================================
echo.

echo [1/5] 检查当前目录...
cd /d "%~dp0"
echo 当前目录: %CD%
echo.

echo [2/5] 检查 frontend 目录...
if exist "frontend" (
    echo ✓ frontend 目录存在
    cd frontend
) else (
    echo ✗ frontend 目录不存在！
    pause
    exit /b 1
)
echo.

echo [3/5] 检查 package.json...
if exist "package.json" (
    echo ✓ package.json 存在
) else (
    echo ✗ package.json 不存在！
    pause
    exit /b 1
)
echo.

echo [4/5] 检查 node_modules...
if exist "node_modules\vite" (
    echo ✓ vite 已安装
) else (
    echo ✗ vite 未安装！
    echo.
    echo 正在运行 npm install...
    call npm install
    if errorlevel 1 (
        echo ✗ npm install 失败！
        pause
        exit /b 1
    )
)
echo.

echo [5/5] 检查端口 3000...
netstat -ano | findstr :3000 > NUL
if errorlevel 1 (
    echo ✓ 端口 3000 可用
) else (
    echo ⚠ 端口 3000 已被占用！
    echo.
    echo 占用进程：
    netstat -ano | findstr :3000
    echo.
    set /p kill="是否结束占用进程？(Y/N): "
    if /i "%kill%"=="Y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
            taskkill /PID %%a /F
        )
    )
)
echo.

echo ========================================
echo 所有检查完成！
echo ========================================
echo.
echo 正在启动 Vite 开发服务器...
echo.
echo 服务地址: http://localhost:3000
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

npm run dev

pause
