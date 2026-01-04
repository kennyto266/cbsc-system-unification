@echo off
REM CBSC API Server Startup Script for Windows
REM 啟動 CBSC 用戶管理系統 API 服務器

echo ========================================
echo   CBSC API Server Launcher
echo ========================================
echo.
echo Starting server on port 3007...
echo.
echo API Documentation: http://localhost:3007/docs
echo Health Check: http://localhost:3007/health
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

python start_api_server.py --port 3007

pause
