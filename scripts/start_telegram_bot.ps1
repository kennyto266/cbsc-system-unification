Param(
    [string]$EnvPath = ".env"
)

$ErrorActionPreference = "Stop"

# 进入项目根目录
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path (Resolve-Path ..) | Out-Null

# 载入 .env（如果存在）
if (Test-Path $EnvPath) {
    Write-Host "Loading env from $EnvPath"
    foreach ($line in Get-Content $EnvPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") { continue }
        $k,$v = $line -split "=",2
        if ($k -and $v) { [System.Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim()) }
    }
}

# 安装依赖（如果缺失）
pip install --quiet python-telegram-bot[rate-limiter,http2]==21.6 python-dotenv==1.0.1 >$null 2>$null

Write-Host "Starting Telegram Integration demo..."
Start-Process -FilePath python -ArgumentList "-X","utf8","examples/telegram_integration_demo.py" -WindowStyle Hidden
Write-Host "Launched. Check your Telegram bot for messages."


