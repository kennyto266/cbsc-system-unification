# 強制清除GitHub相關環境變量
$env:GITHUB_TOKEN = $null
Remove-Item Env:GITHUB_TOKEN -Force -ErrorAction SilentlyContinue

# 檢查認證狀態
Write-Host "Environment cleared. Checking auth status..."
gh auth status