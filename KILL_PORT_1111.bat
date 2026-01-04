@echo off
echo ========================================
echo 關閉端口 1111 解決方案
echo ========================================
echo.

echo [1/3] 查找占用端口 1111 的進程...
netstat -ano | findstr ":1111" > nul 2>&1
if %errorlevel% equ 0 (
    echo 發現以下進程占用端口 1111:
    netstat -ano | findstr ":1111"
    echo.

    [2/3] 查找進程詳細信息...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":1111"') do (
        set PID=%%a
        echo 進程ID: !PID!

        [3/3] 查找進程詳細信息...
        for /f "tokens=1,2" %%b in ('tasklist /fi "PID eq !PID!" /fo table ^| findstr "!PID!"') do (
            set PROCESS_NAME=%%b
            echo 進程名稱: !PROCESS_NAME!
        )

        echo.
        set /p choice="選擇操作 (1=終止進程, 2=跳過): "
        if "!choice!"=="1" (
            echo 正在終止進程 !PID!...
            taskkill /F /PID !PID! > nul 2>&1
            if !errorlevel! equ 0 (
                echo ✅ 進程 !PID! 已終止
            ) else (
                echo ❌ 終止進程失敗，可能需要管理員權限
            )
        )
        goto :end_loop
    )
) else (
    echo ✅ 端口 1111 當前未被占用
    goto :end_loop
)

:end_loop
echo.
echo ========================================
echo 操作完成
echo ========================================
echo.

echo [可選操作]
echo 1. 檢查端口是否已釋放
echo 2. 重新檢查系統狀態
echo 3. 結束修復工具

set /p next_action="選擇操作 (1/2/3): "
if "%next_action%"=="1" (
    echo.
    echo 重新檢查端口 1111...
    netstat -ano | findstr ":1111"
    echo.
    if %errorlevel% equ 0 (
        echo ❌ 端口 1111 仍被占用
    ) else (
        echo ✅ 端口 1111 已釋放
    )
)

if "%next_action%"=="2" (
    echo.
    echo 系統狀態檢查...
    echo 當前運行的富途相關進程:
    tasklist | findstr /i "futu"
    echo.
    echo 富途端口使用情況:
    netstat -ano | findstr ":1111\|:11111\|:4444"
)

if "%next_action%"=="3" (
    echo.
    echo 啟動富途連接問題修復工具...
    python FUTU_LOGIN_FIX.py
)

echo.
pause