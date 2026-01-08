@echo off
REM CBSC AGX Analytics System - Quick Start Script (Windows)
REM
REM This script initializes and starts the AGX analytics system on Windows

setlocal enabledelayedexpansion

REM Configuration
set "PROJECT_ROOT=%~dp0.."
set "AGX_DIR=%PROJECT_ROOT%\agx"
set "SERVICE_DIR=%PROJECT_ROOT%\ai-strategy-service"
set "LOG_DIR=%PROJECT_ROOT%\logs"

echo ==================================================
echo CBSC AGX Analytics System - Quick Start
echo ==================================================
echo.

REM Prerequisites check
echo [Prerequisites] Checking required tools...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python found

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker found

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Step 1: Check if AGX directory exists
echo.
echo 1. Checking AGX installation...
if not exist "%AGX_DIR%" (
    echo [ERROR] AGX directory not found: %AGX_DIR%
    echo.
    echo Please install AGX first:
    echo   git clone https://github.com/agnosticeng/agx.git agx
    echo   cd agx
    echo   docker compose up -d
    pause
    exit /b 1
)
echo [OK] AGX directory found

REM Step 2: Check Docker status
echo.
echo 2. Checking Docker status...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)
echo [OK] Docker is running

REM Step 3: Start AGX with ClickHouse
echo.
echo 3. Starting AGX and ClickHouse...
cd /d "%AGX_DIR%"
docker compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start AGX containers
    pause
    exit /b 1
)
echo [OK] AGX containers started

REM Step 4: Wait for ClickHouse to be ready
echo.
echo 4. Waiting for ClickHouse to be ready...
cd /d "%PROJECT_ROOT%"
set /a COUNT=0
:WAIT_LOOP
if !COUNT! GEQ 60 (
    echo [ERROR] ClickHouse failed to start within 60 seconds
    echo Check Docker logs: docker logs agx-clickhouse-1
    pause
    exit /b 1
)
docker exec agx-clickhouse-1 clickhouse-client --query "SELECT 1" >nul 2>&1
if errorlevel 1 (
    if !COUNT! EQU 0 (
        echo Waiting for ClickHouse...
    )
    timeout /t 1 /nobreak >nul
    set /a COUNT+=1
    goto WAIT_LOOP
)
echo [OK] ClickHouse is ready

REM Step 5: Install Python dependencies
echo.
echo 5. Checking Python dependencies...
cd /d "%SERVICE_DIR%"
pip show clickhouse-driver >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies...
    pip install clickhouse-driver psycopg2-binary apscheduler -q
    if errorlevel 1 (
        echo [WARNING] Failed to install dependencies
        echo Attempting to continue anyway...
    ) else (
        echo [OK] Dependencies installed
    )
) else (
    echo [OK] Dependencies already installed
)

REM Step 6: Initialize ClickHouse schema
echo.
echo 6. Initializing ClickHouse schema...
python scripts\init_clickhouse.py
if errorlevel 1 (
    echo [WARNING] Schema initialization failed (may already exist)
) else (
    echo [OK] Schema initialized
)

REM Step 7: Import sample data
echo.
echo 7. Importing sample data...
python scripts\import_sample_data.py
if errorlevel 1 (
    echo [WARNING] Sample data import failed
    echo You can import later: python scripts\import_sample_data.py
) else (
    echo [OK] Sample data imported
)

REM Step 8: Start ETL scheduler
echo.
echo 8. Starting ETL scheduler...
REM Stop any existing Python ETL scheduler
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH 2^>nul ^| findstr /I "etl_scheduler"') do (
    taskkill /F /PID %%i >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Start ETL scheduler in background with output redirection
start "ETL Scheduler" /MIN cmd /c "python scripts\etl_scheduler.py > %LOG_DIR%\etl_scheduler.log 2>&1"
timeout /t 2 /nobreak >nul

REM Verify scheduler is running
tasklist /FI "WINDOWTITLE eq ETL Scheduler*" 2>nul | find /I "cmd.exe" >nul
if errorlevel 1 (
    echo [WARNING] ETL scheduler may not have started properly
    echo Check: %LOG_DIR%\etl_scheduler.log
) else (
    echo [OK] ETL scheduler started
)

REM Step 9: Display summary
echo.
echo ==================================================
echo [OK] AGX Analytics System started successfully!
echo ==================================================
echo.
echo Access Points:
echo   - AGX Web Interface: http://localhost:8080
echo   - ClickHouse Port: 8123
echo.
echo Log Files:
echo   - ETL Scheduler: %LOG_DIR%\etl_scheduler.log
echo.
echo Management Commands:
echo   - View ETL logs: type %LOG_DIR%\etl_scheduler.log
echo   - View Docker logs: docker logs agx-clickhouse-1
echo   - Stop scheduler: Taskkill /F /FI "WINDOWTITLE eq ETL Scheduler*"
echo   - Stop AGX: cd %AGX_DIR% ^& docker compose down
echo.
echo Next Steps:
echo   1. Open AGX at http://localhost:8080
echo   2. Configure ClickHouse connection:
echo      Host: localhost
echo      Port: 8123
echo      Database: analytics
echo      User: default
echo      Password: (empty)
echo   3. Import connection config from: agx\config\clickhouse_connection.json
echo   4. Start exploring your strategy data!
echo.

REM Optional: Open browser automatically
set /p OPEN_BROWSER="Open AGX in browser? (Y/n): "
if /i "%OPEN_BROWSER%"=="Y" set OPEN_BROWSER=y
if /i "%OPEN_BROWSER%"=="y" (
    start http://localhost:8080
)

echo.
echo Press any key to exit this window...
pause >nul
