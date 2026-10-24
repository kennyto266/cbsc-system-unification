$ErrorActionPreference = "SilentlyContinue"

# 终止前台/后台 python 进程中运行的 telegram_bot_service
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*python*" } | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    } catch {}
}

Write-Host "Stop signal sent for Telegram bot service"


