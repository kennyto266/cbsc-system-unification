@echo off
echo ========================================
echo 富途 OpenD 端口問題快速修復
echo ========================================
echo.

echo [1/6] 檢查富途 OpenD 進程...
tasklist | findstr "FutuOpenD" > nul
if %errorlevel% equ 0 (
    echo ✅ 檢測到富途 OpenD 進程正在運行
) else (
    echo ❌ 富途 OpenD 進程未運行
    echo.
    echo 正在啟動富途 OpenD...
    start "" "C:\Program Files\Futu\FutuOpenD\FutuOpenD.exe"
    echo 等待富途啟動...
    timeout /t 10 /nobreak > nul
)

echo.
echo [2/6] 檢查端口占用情況...
netstat -ano | findstr ":11111" > nul
if %errorlevel% equ 0 (
    echo ⚠️ 端口 11111 被占用

    echo 查找占用進程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":11111"') do (
        set PID=%%a
        echo 進程ID: !PID!

        echo 查找進程詳細信息...
        for /f "tokens=1,2" %%b in ('tasklist /fi "PID eq !PID!" /fo table ^| findstr "!PID!"') do (
            set PROCESS_NAME=%%b
            echo 進程名稱: !PROCESS_NAME!
        )

        echo.
        echo 當前狀況:
        echo 1. 如果是富途進程，嘗試重新啟動
        echo 2. 如果是其他進程，考慮使用不同端口
        echo.

        set /p choice="選擇操作 (1=重啟富途, 2=使用其他端口, 3=手動處理): "
        if "!choice!"=="1" goto :restart_futu
        if "!choice!"=="2" goto :use_alternative_port
        if "!choice!"=="3" goto :manual_resolution
        echo 無效選擇，請重新輸入
        goto :end
    )
) else (
    echo ✅ 端口 11111 可用
)

echo.
echo [3/6] 測試富途連接...
cd /d "C:\Users\Penguin8n\CODEX--"

echo 安裝必需的 Python 包...
pip install futu-opensdk > nul 2>&1

echo 運行連接檢測工具...
python -c "import socket; s = socket.socket(); result = s.connect_ex(('127.0.0.1', 11111)); s.close(); print('✅ 富途連接正常' if result == 0 else '❌ 富途連接失敗')"

echo.
echo [4/6] 設置環境變量...
set FUTU_HOST=127.0.0.1
set FUTU_PORT=11111
echo 設置完成: FUTU_HOST=%FUTU_HOST%, FUTU_PORT=%FUTU_PORT%

echo.
echo [5/6] 運行 POC 快速測試...
python futu_connection_fix.py

echo.
echo [6/6] 生成端口配置文件...
echo @echo off > set_futu_port.bat
echo echo 設置富途端口環境變量 >> set_futu_port.bat
echo set FUTU_HOST=127.0.0.1 >> set_futu_port.bat
echo set FUTU_PORT=11111 >> set_futu_port.bat
echo echo 環境變量已設置 >> set_futu_port.bat
echo echo 現在可以運行: python POC_QUICK_START.py >> set_futu_port.bat
echo pause >> set_futu_port.bat

echo ✅ 端口配置文件生成完成: set_futu_port.bat

goto :end

:restart_futu
echo 正在終止當前富途進程...
taskkill /F /IM FutuOpenD.exe > nul 2>&1

echo 等待 2 秒...
timeout /t 2 /nobreak > nul

echo 重新啟動富途...
start "" "C:\Program Files\Futu\FutuOpenD\FutuOpenD.exe"
echo 等待富途啟動...
timeout /t 10 /nobreak > nul

echo 重新測試連接...
python -c "import socket; s = socket.socket(); result = s.connect_ex(('127.0.0.1', 11111)); s.close(); print('✅ 富途連接正常' if result == 0 else '❌ 富途連接失敗')"
goto :end

:use_alternative_port
echo 測試其他可用端口...
python -c "
import socket
ports = [11011, 11211, 11311, 11411]
for port in ports:
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', port))
    s.close()
    if result == 0:
        print(f'✅ 找到可用端口: {port}')
        print(f'執行: set FUTU_PORT={port}')
        break
    else:
        print(f'❌ 端口 {port} 被占用')
"

echo.
echo 設置新端口...
set /p new_port="請輸入要使用的端口 (默認 11011): "
if "%new_port%"=="" set new_port=11011
set FUTU_PORT=%new_port%
echo 環境變量已更新: FUTU_PORT=%FUTU_PORT%
goto :end

:manual_resolution
echo.
echo ========================================
echo 手動解決指南
echo ========================================
echo.
echo 1. 檢查進程:
echo    tasklist ^| findstr "FutuOpenD"
echo.
echo 2. 檢查端口:
echo    netstat -ano ^| findstr ":11111"
echo.
echo 3. 終止進程:
echo    taskkill /F /PID <進程ID>
echo.
echo 4. 防火牆設置:
echo    - 允許 FutuOpenD.exe 通過防火牆
echo    - 添加端口 11111 到例外列表
echo.
echo 5. 重啟富途客戶端後重試
echo.

:end
echo.
echo ========================================
echo 修復完成！
echo ========================================
echo.
echo 下一步操作:
echo 1. 如果富途未運行，請手動啟動富途客戶端
echo 2. 運行: python POC_QUICK_START.py
echo 3. 如果仍有問題，運行: python futu_connection_fix.py
echo.
pause