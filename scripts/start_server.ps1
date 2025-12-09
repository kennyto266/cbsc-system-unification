Param(
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000,
    [string]$LogLevel = "info"
)

$ErrorActionPreference = "Stop"

# 进入项目根目录（脚本所在目录的上级）
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path (Resolve-Path ..) | Out-Null

# 确保 fastapi/uvicorn 可用
python -X utf8 -c "import fastapi,uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) { throw "Missing fastapi/uvicorn. Run: pip install fastapi uvicorn" }

# 启动 uvicorn（simple_web_dashboard:app）
Write-Host ("Starting uvicorn on http://{0}:{1} ..." -f $BindHost,$Port)
Start-Process -FilePath python -ArgumentList "-m","uvicorn","simple_web_dashboard:app","--host",$BindHost,"--port",$Port,"--log-level",$LogLevel -WindowStyle Hidden

# 健康检查
Start-Sleep -Seconds 2
try {
    $resp = Invoke-WebRequest -Uri ("http://localhost:{0}/health" -f $Port) -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -eq 200) { Write-Host ("Server is up: http://localhost:{0}" -f $Port) }
    else { Write-Warning ("Health check non-200: {0}" -f $resp.StatusCode) }
}
catch {
    Write-Warning ("Health check failed: {0}" -f $_.Exception.Message)
}


