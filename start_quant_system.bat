@echo off
echo 🚀 启动量化交易系统...
echo.

REM 切换到项目目录
cd /d "C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊"

REM 检查文件是否存在
if not exist "complete_frontend_system.py" (
    echo ❌ 找不到 complete_frontend_system.py 文件
    echo 正在查找可用的系统文件...
    
    if exist "secure_complete_system.py" (
        echo ✅ 找到 secure_complete_system.py
        echo 启动安全版系统...
        python secure_complete_system.py
    ) else if exist "unified_quant_system.py" (
        echo ✅ 找到 unified_quant_system.py
        echo 启动统一版系统...
        python unified_quant_system.py
    ) else if exist "main.py" (
        echo ✅ 找到 main.py
        echo 启动主系统...
        python main.py
    ) else (
        echo ❌ 未找到任何可用的系统文件
        echo 请检查项目目录: C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊
        pause
        exit /b 1
    )
) else (
    echo ✅ 找到 complete_frontend_system.py
    echo 启动完整前端系统...
    python complete_frontend_system.py
)

echo.
echo 🌐 系统启动后，请访问: http://localhost:8001
echo 按 Ctrl+C 停止系统
pause
