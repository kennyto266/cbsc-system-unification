#!/bin/bash

# 啟動 CBSC 前端和後端服務

echo "=== CBSC 系統啟動腳本 ==="
echo ""

# 檢查 Python 版本
echo "檢查 Python 版本..."
python3 --version

# 檢查 Node.js 版本
echo ""
echo "檢查 Node.js 版本..."
node --version

# 啟動後端 WebSocket 服務
echo ""
echo "=== 啟動後端 WebSocket 服務 (端口 3004) ==="
cd backend

# 安裝後端依賴（如果需要）
if [ ! -d "venv" ]; then
    echo "創建 Python 虛擬環境..."
    python3 -m venv venv
fi

# 激活虛擬環境
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# 安裝依賴
pip install -r requirements.txt

# 啟動後端（在後台運行）
echo "啟動 WebSocket 服務器..."
python main.py &
BACKEND_PID=$!
echo "後端 PID: $BACKEND_PID"

# 返回根目錄
cd ..

# 等待後端啟動
sleep 3

# 檢查後端是否成功啟動
echo ""
echo "檢查後端服務狀態..."
if curl -s http://localhost:3004/health > /dev/null; then
    echo "✅ 後端 WebSocket 服務已成功啟動"
else
    echo "❌ 後端服務啟動失敗"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 啟動前端服務
echo ""
echo "=== 啟動前端服務 (端口 3001) ==="
cd square-ui-frontend

# 安裝前端依賴（如果需要）
if [ ! -d "node_modules" ]; then
    echo "安裝前端依賴..."
    npm install
fi

# 啟動前端
echo "啟動前端開發服務器..."
npm run dev &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

# 等待前端啟動
sleep 5

echo ""
echo "=== 服務狀態 ==="
echo "後端 WebSocket: http://localhost:3004/ws"
echo "前端 Dashboard: http://localhost:3001/dashboard"
echo ""
echo "按 Ctrl+C 停止所有服務"

# 創建清理函數
cleanup() {
    echo ""
    echo "正在停止服務..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "所有服務已停止"
    exit 0
}

# 捕獲中斷信號
trap cleanup SIGINT SIGTERM

# 保持腳本運行
wait