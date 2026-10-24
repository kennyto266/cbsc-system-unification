@echo off
set HOST=0.0.0.0
set PORT=8000
set LOG_LEVEL=info

cd /d %~dp0
cd ..

echo Starting uvicorn on http://%HOST%:%PORT% ...
start "uvicorn" /min cmd /c python -m uvicorn simple_web_dashboard:app --host %HOST% --port %PORT% --log-level %LOG_LEVEL%

REM simple health ping (optional)
timeout /t 2 >nul
curl -s http://localhost:%PORT%/health >nul 2>nul
echo Server start command issued.


