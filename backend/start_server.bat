@echo off
REM CBSC WebSocket 服務器啟動腳本 (Windows)

echo Starting CBSC WebSocket Server...
echo Port: 3004
echo WebSocket URL: ws://localhost:3004/ws

REM 檢查 Python 版本
python --version

REM 安裝依賴
echo Installing dependencies...
pip install -r requirements.txt

REM 啟動服務器
echo Starting WebSocket server...
python main.py

pause