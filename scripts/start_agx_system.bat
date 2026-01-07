@echo off
REM CBSC AGX Analytics System - Quick Start Script (Windows)

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_ROOT=%~dp0..
set AGX_DIR=%PROJECT_ROOT%\agx
set SERVICE_DIR=%PROJECT_ROOT%\ai-strategy-service
set LOG_DIR=%PROJECT_ROOT%\logs

echo ==================================================
echo CBSC AGX Analytics System - Quick Start
echo ==================================================
echo.

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Step 1: Check if AGX directory exists
echo 1. Checking AGX installation...
if not exist "%AGX_DIR%" (
    echo [ERROR] AGX directory not found: %AGX_DIR%
    echo.
    echo Please install AGX first:
    echo   git clone https://github.com/agnosticeng/agx.git agx
    echo   cd agx ^&^& docker compose up -d
    pause
    exit /b 1
)
echo [OK] AGX directory found

REM Step 2: Start AGX with ClickHouse
echo.
echo 2. Starting AGX and ClickHouse...
cd /d "%AGX_DIR%"
docker compose up -d
echo [OK] AGX started successfully

REM Step 3: Wait for ClickHouse to be ready
echo.
echo 3. Waiting for ClickHouse to be ready...
cd /d "%PROJECT_ROOT%"
set /a COUNT=0
:WAIT_LOOP
if !COUNT! GEQ 30 (
    echo [ERROR] ClickHouse failed to start
    pause
    exit /b 1
)
docker exec agx-clickhouse-1 clickhouse-client --query "SELECT 1" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    set /a COUNT+=1
    goto WAIT_LOOP
)
echo [OK] ClickHouse is ready

REM Step 4: Initialize ClickHouse schema
echo.
echo 4. Initializing ClickHouse schema...
cd /d "%SERVICE_DIR%"
python scripts\init_clickhouse.py
if errorlevel 1 (
    echo [WARNING] Schema initialization failed (may already exist)
) else (
    echo [OK] Schema initialized
)

REM Step 5: Import sample data
echo.
echo 5. Importing sample data...
python scripts\import_sample_data.py
if errorlevel 1 (
    echo [WARNING] Sample data import failed
) else (
    echo [OK] Sample data imported
)

REM Step 6: Start ETL scheduler (using start /B for background)
echo.
echo 6. Starting ETL scheduler...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq etl_scheduler*" 2>nul
timeout /t 2 /nobreak >nul

start "ETL Scheduler" /MIN python scripts\etl_scheduler.py
echo [OK] ETL scheduler started

REM Step 7: Display summary
echo.
echo ==================================================
echo [OK] AGX Analytics System started successfully!
echo ==================================================
echo.
echo 📊 Access Points:
echo   • AGX Web Interface: http://localhost:8080
echo   • ClickHouse Port: 8123
echo.
echo 📁 Log Files:
echo   • ETL Scheduler: %LOG_DIR%\etl_scheduler.log
echo.
echo 🔧 Management Commands:
echo   • View ETL logs: type %LOG_DIR%\etl_scheduler.log
echo   • Stop scheduler: Taskkill /F /IM python.exe
echo   • Stop AGX: cd %AGX_DIR% ^&^& docker compose down
echo.
echo 📖 Next Steps:
echo   1. Open AGX at http://localhost:8080
echo   2. Configure ClickHouse connection:
echo      - Host: localhost
echo      - Port: 8123
echo      - Database: analytics
echo      - User: default
echo      - Password: (empty)
echo   3. Import connection config from: agx\config\clickhouse_connection.json
echo   4. Start exploring your strategy data!
echo.

pause
