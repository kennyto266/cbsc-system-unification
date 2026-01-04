@echo off
REM CBSC Frontend - 開發服務器啟動腳本
REM 批處理版本 (推薦使用)

echo ================================================================
echo   CBSC 量化交易系統 - 前端開發服務器
echo ================================================================
echo.

cd /d "%~dp0frontend"

echo [1/3] 檢查依賴...
if exist node_modules (
     echo     [OK] 依賴已安裝
) else (
     echo     [INFO] 正在安裝依賴...
     call npm install
)

echo.
echo [2/3] 啟動開發服務器...
echo     前端地址: http://localhost:3000
echo     後端 API: http://localhost:3003
echo.
echo 按 Ctrl+C 停止服務器
echo.
echo ================================================================
echo.

REM 使用 npx vite 直接啟動 (Windows 兼容)
npx vite --port 3000

pause
