@echo off
REM 啟動 CBSC 前端和後端服務 (Windows)

echo === CBSC 系統啟動腳本 ===
echo.

REM 檢查 Python 版本
echo 檢查 Python 版本...
python --version

REM 檢查 Node.js 版本
echo.
echo 檢查 Node.js 版本...
node --version

REM 啟動後端 WebSocket 服務
echo.
echo === 啟動後端 WebSocket 服務 (端口 3004) ===
cd backend

REM 創建並激活虛擬環境（如果不存在）
if not exist venv (
    echo 創建 Python 虛擬環境...
    python -m venv venv
)

REM 激活虛擬環境
call venv\Scripts\activate.bat

REM 安裝依賴
echo 安裝後端依賴...
pip install -r requirements.txt

REM 啟動後端服務器（在新窗口中）
echo 啟動 WebSocket 服務器...
start "WebSocket Server" cmd /k "python main.py"

REM 返回根目錄
cd ..

REM 等待後端啟動
timeout /t 3 /nobreak >nul

REM 啟動前端服務
echo.
echo === 啟動前端服務 (端口 3001) ===
cd square-ui-frontend

REM 安裝前端依賴（如果需要）
if not exist node_modules (
    echo 安裝前端依賴...
    call npm install
)

REM 啟動前端服務器（在新窗口中）
echo 啟動前端開發服務器...
start "Frontend Server" cmd /k "npm run dev"

REM 返回根目錄
cd ..

echo.
echo === 服務狀態 ===
echo 後端 WebSocket: ws://localhost:3004/ws
echo 後端 API: http://localhost:3004/health
echo 前端 Dashboard: http://localhost:3001/dashboard
echo.
echo 兩個服務已在獨立窗口中啟動
echo 關閉窗口即可停止對應服務
echo.

pause