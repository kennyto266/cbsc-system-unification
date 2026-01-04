@echo off
echo ========================================
echo 富途 OpenD 端口衝突修復腳本
echo ========================================
echo.

echo [1/4] 查找占用端口 11111 的進程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":11111"') do (
    set PID=%%a
    goto :found_pid
)
echo ✅ 端口 11111 未被占用，直接使用即可
goto :end

:found_pid
echo 發現端口 11111 被進程 %PID% 占用

echo [2/4] 查找進程詳細信息...
for /f "tokens=1,2" %%a in ('tasklist /fi "PID eq %PID%" /fo table ^| findstr "%PID%"') do (
    set PROCESS_NAME=%%b
    goto :found_process
)

:found_process
echo 進程名稱: %PROCESS_NAME%
echo.

echo [3/4] 嘗試解決衝突...
if "%PROCESS_NAME%" == "FutuOpenD.exe" (
    echo 檢測到富途 OpenD 進程，嘗試重新啟動...

    echo 終束富途進程...
    taskkill /F /IM FutuOpenD.exe

    echo 等待 3 秒...
    timeout /t 3 /nobreak >nul

    echo 重新啟動富途 OpenD...
    start "" "C:\Program Files\Futu\FutuOpenD\FutuOpenD.exe"

    echo 等待富途啟動...
    timeout /t 10 /nobreak >nul

    goto :test_connection
)

if "%PROCESS_NAME%" == "python.exe" (
    echo 檢測到 Python 進程，可能是富途腳本...

    echo 終束 Python 進程...
    taskkill /F /PID %PID%

    echo 等待 2 秒...
    timeout /t 2 /nobreak >nul

    goto :test_connection
)

echo 未知進程，強制終止...
taskkill /F /PID %PID%

:test_connection
echo [4/4] 測試端口連接...
timeout /t 2 /nobreak >nul

echo 測試富途連接...
cd /d "C:\Users\Penguin8n\CODEX--"
python -c "import socket; s = socket.socket(); result = s.connect_ex(('127.0.0.1', 11111)); s.close(); print('✅ 端口可用' if result == 0 else '❌ 端口仍被占用')"

echo.
echo ========================================
echo 修復完成！
echo ========================================
echo.
echo 現在您可以：
echo 1. 重新運行富途客戶端
echo 2. 執行 python POC_QUICK_START.py
echo.

:end
pause