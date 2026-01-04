@echo off
echo ========================================
echo CBSC 系統快速部署腳本
echo ========================================
echo.

REM 檢查 Docker Desktop 是否運行
echo [1/5] 檢查 Docker Desktop 狀態...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Desktop 未運行，請先啟動 Docker Desktop
    echo 正在嘗試啟動 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo 等待 Docker Desktop 啟動...
    timeout /t 30 /nobreak
    docker version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Docker Desktop 啟動失敗，請手動啟動後重新運行此腳本
        pause
        exit /b 1
    )
)
echo ✅ Docker Desktop 運行中

REM 進入項目目錄
echo [2/5] 進入項目目錄...
cd /d "C:\Users\Penguin8n\CODEX--"
if %errorlevel% neq 0 (
    echo ❌ 無法進入項目目錄
    pause
    exit /b 1
)
echo ✅ 已進入項目目錄

REM 創建必要目錄
echo [3/5] 創建必要目錄...
if not exist "ssl" mkdir ssl
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "static" mkdir static
if not exist "config\influxdb" mkdir config\influxdb
echo ✅ 目錄創建完成

REM 檢查環境配置
echo [4/5] 檢查環境配置...
if not exist ".env" (
    echo ⚠️ .env 文件不存在，複製生產配置...
    copy .env.prod .env
    echo 請編輯 .env 文件更新安全密碼後重新運行
    notepad .env
    pause
    exit /b 1
)
echo ✅ 環境配置已就緒

REM 開始部署
echo [5/5] 開始部署 CBSC 系統...
echo.

REM 部署數據庫服務
echo 部署數據庫服務...
docker-compose -f docker-compose.prod.yml up -d postgres redis influxdb
echo 等待數據庫服務啟動...
timeout /t 60 /nobreak

REM 部署應用服務
echo 部署應用服務...
docker-compose -f docker-compose.prod.yml up -d backend frontend
echo 等待應用服務啟動...
timeout /t 45 /nobreak

REM 部署監控服務
echo 部署監控服務...
docker-compose -f docker-compose.prod.yml up -d prometheus grafana nginx
echo 等待監控服務啟動...
timeout /t 30 /nobreak

REM 檢查服務狀態
echo.
echo ========================================
echo 檢查服務狀態...
echo ========================================
docker-compose -f docker-compose.prod.yml ps

echo.
echo ========================================
echo 🎉 部署完成！
echo ========================================
echo.
echo 訪問地址：
echo ✅ 主應用: http://localhost:3000
echo ✅ API 文檔: http://localhost:3004/docs
echo ✅ Grafana: http://localhost:3001 (admin/您的密碼)
echo ✅ Prometheus: http://localhost:9090
echo.

echo 健康檢查...
curl -f http://localhost:3004/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 後端服務正常
) else (
    echo ⚠️ 後端服務可能仍在啟動中
)

curl -f http://localhost:3000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端服務正常
) else (
    echo ⚠️ 前端服務可能仍在啟動中
)

curl -f http://localhost:3001/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Grafana 服務正常
) else (
    echo ⚠️ Grafana 服務可能仍在啟動中
)

echo.
echo 如需查看日誌：
echo docker-compose -f docker-compose.prod.yml logs -f [服務名]
echo.
echo 如需停止服務：
echo docker-compose -f docker-compose.prod.yml down
echo.
pause