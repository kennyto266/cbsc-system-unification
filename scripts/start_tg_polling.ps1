Param(
    [string]$EnvPath = "config/bot.env"
)

$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path (Resolve-Path ..) | Out-Null

if (Test-Path $EnvPath) {
    Write-Host "Loading env from $EnvPath"
    foreach ($line in Get-Content $EnvPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") { continue }
        $k,$v = $line -split "=",2
        if ($k -and $v) { [System.Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim()) }
    }
}

Write-Host "Starting telegram bot polling..."
Start-Process -FilePath python -ArgumentList "-X","utf8","examples/telegram_bot_polling.py" -WindowStyle Hidden
Write-Host "Launched. Send /cursor_help in Telegram to verify."


