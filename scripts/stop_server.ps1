Param(
    [int]$Port = 8000
)

$ErrorActionPreference = "SilentlyContinue"

# 尝试通过端口定位进程并终止
try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen
    foreach ($c in $conns) {
        $pid = $c.OwningProcess
        if ($pid) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
}
catch {}

# 兜底：终止后台 python uvicorn 进程
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -match "uvicorn" -or $_.StartInfo } | ForEach-Object { $_ | Stop-Process -Force -ErrorAction SilentlyContinue }

Write-Host "Stop signal sent for port $Port"


