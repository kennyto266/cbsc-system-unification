@echo off
echo ========================================
echo 富途 OpenD 進程管理工具
echo 解決登錄超時問題
echo ========================================
echo.

echo [1/6] 查找所有富途相關進程...
echo 正在搜索 FutuOpenD.exe...
tasklist | findstr "FutuOpenD" > nul 2>&1
set FUTU_FOUND=%errorlevel%

if %FUTU_FOUND% equ 0 (
    echo ✅ 檢測到富途進程正在運行
    echo.

    [2/6] 顯示進程詳細信息...
    echo 當前運行的富途進程:
    tasklist /fi "imagename eq FutuOpenD.exe" /fo table

    echo.
    [3/6] 查找端口占用情況...
    echo 檢查端口 11111 (標準) 和 4444 (截圖顯示)...
    echo.

    echo 端口 11111 使用情況:
    netstat -ano | findstr ":11111" | findstr "LISTENING"
    echo.

    echo 端口 4444 使用情況:
    netstat -ano | findstr ":4444" | findstr "LISTENING"
    echo.

    [4/6] 強制終止所有富途進程...
    echo 正在終止所有富途進程...
    taskkill /F /IM FutuOpenD.exe > nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ 富途進程已終止
    ) else (
        echo ⚠️ 可能需要管理員權限來終止進程
    )

    echo.
    [5/6] 等待進程完全關閉...
    echo 等待 3 秒確保進程完全關閉...
    timeout /t 3 /nobreak > nul

    [6/6] 驗證進程已關閉...
    echo 驗證富途進程狀態...
    tasklist | findstr "FutuOpenD" > nul 2>&1
    if %errorlevel% equ 0 (
        echo ❌ 仍有富途進程在運行，請手動檢查任務管理器
        echo.
        echo 建議操作:
        echo 1. 打開任務管理器 (Ctrl+Shift+Esc)
        echo 2. 搜索 "FutuOpenD.exe"
        echo 3. 手動終止所有相關進程
        echo 4. 或者重啟電腦
    ) else (
        echo ✅ 所有富途進程已成功關閉
    )

) else (
    echo ❌ 未檢測到富途進程正在運行
    echo 可能的解釋:
    echo 1. 富途尚未啟動
    echo 2. 富途已經被手動關閉
    echo 3. 富途進程使用不同的名稱
)

echo.
echo ========================================
echo 操作完成！
echo ========================================
echo.

echo 現在您可以：
echo 1. 等待 5-10 秒後重新啟動富途客戶端
echo 2. 確保使用正確的賬戶憑證登錄
echo 3. 確認網絡連接穩定
echo 4. 運行 python POC_QUICK_START.py 測試連接

echo.
echo [可選的後續操作]
set /p choice="選擇操作 (1=重啟富途, 2=檢查端口, 3=運行POC測試): "
if "%choice%"=="1" (
    echo.
    echo 正在啟動富途 OpenD...
    start "" "C:\Program Files\Futu\FutuOpenD\FutuOpenD.exe"
    echo 富途客戶端已啟動，請登錄後再測試連接
)

if "%choice%"=="2" (
    echo.
    echo 檢查富途端口使用情況:
    echo 端口 11111 (標準端口):
    netstat -ano | findstr ":11111" | findstr "LISTENING"
    echo.
    echo 端口 4444 (截圖顯示端口):
    netstat -ano | findstr ":4444" | findstr "LISTENING"
)

if "%choice%"=="3" (
    echo.
    echo 準備運行 POC 連接測試...
    python POC_QUICK_START.py
)

echo.
pause