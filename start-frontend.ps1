# CBSC 前端服务启动脚本 (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CBSC 前端服务启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到项目目录
$projectDir = "C:\Users\Penguin8n\CODEX--\frontend"
Set-Location $projectDir

Write-Host "当前目录: $PWD" -ForegroundColor Green
Write-Host ""
Write-Host "正在启动 Vite 开发服务器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "服务地址: http://localhost:3000" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 可以停止服务" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动开发服务器
npm run dev
