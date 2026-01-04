@echo off
REM CBSC Real Backend Startup Script
REM 啟動真實後端系統

echo ========================================
echo CBSC Quantitative Trading System
echo Real Backend Deployment
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [1/5] Stopping existing containers...
docker-compose -f docker-compose.simple.yml down
docker-compose -f docker-compose.real.yml down 2>nul

echo [2/5] Building real backend image...
docker-compose -f docker-compose.real.yml build backend

echo [3/5] Starting real services...
docker-compose -f docker-compose.real.yml up -d postgres redis influxdb

echo [4/5] Waiting for databases to be ready...
timeout /t 15 /nobreak >nul

echo [5/5] Starting backend and frontend...
docker-compose -f docker-compose.real.yml up -d

echo.
echo ========================================
echo CBSC Real Backend Started Successfully!
echo ========================================
echo.
echo Services:
echo   - Backend API:       http://localhost:8001
echo   - API Documentation: http://localhost:8001/docs
echo   - Frontend:          http://localhost:3006
echo   - Grafana:           http://localhost:8889 (admin/cbsc_grafana_admin_2024)
echo   - Prometheus:        http://localhost:9091
echo   - PostgreSQL:        localhost:5433
echo   - Redis:             localhost:6380
echo   - InfluxDB:          http://localhost:8087
echo.
echo To view logs:
echo   docker-compose -f docker-compose.real.yml logs -f backend
echo.
echo To stop services:
echo   docker-compose -f docker-compose.real.yml down
echo.

pause
