# CBSC Frontend - 開發服務器啟動腳本
# PowerShell 版本

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CBSC 量化交易系統 - 前端開發服務器" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$frontendDir = "C:\Users\Penguin8n\CODEX--\frontend"

# 檢查目錄
if (!(Test-Path $frontendDir)) {
    Write-Host "錯誤：前端目錄不存在" -ForegroundColor Red
    exit 1
}

# 進入前端目錄
Set-Location $frontendDir

Write-Host "[1/3] 檢查依賴..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "      [OK] 依賴已安裝" -ForegroundColor Green
} else {
    Write-Host "      [INFO] 正在安裝依賴..." -ForegroundColor Yellow
    npm install
}

Write-Host ""
Write-Host "[2/3] 啟動開發服務器..." -ForegroundColor Yellow
Write-Host "      前端地址: http://localhost:3000" -ForegroundColor Cyan
Write-Host "      後端 API: http://localhost:3003" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服務器" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 啟動開發服務器
npm run dev
