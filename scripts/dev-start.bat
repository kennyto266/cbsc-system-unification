@echo off
REM CBSC System Development Environment Startup Script (Windows)
REM Author: CBSC Development Team
REM Description: Start all development services with proper ordering and health checks

setlocal enabledelayedexpansion

REM Configuration
set COMPOSE_FILE=docker-compose.dev.yml
set PROJECT_NAME=cbsc-dev
set LOG_DIR=logs

REM Colors for output (Windows compatible)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM Function to print status
echo %INFO% 检查Docker状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker未运行，请先启动Docker
    pause
    exit /b 1
)
echo %SUCCESS% Docker运行正常

REM Check Docker Compose
echo %INFO% 检查Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker Compose未安装
    pause
    exit /b 1
)
echo %SUCCESS% Docker Compose可用

REM Create necessary directories
echo %INFO% 创建必要的目录...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "data\postgres" mkdir "data\postgres"
if not exist "data\redis" mkdir "data\redis"
if not exist "data\uploads" mkdir "data\uploads"
if not exist "gateway\logs" mkdir "gateway\logs"
if not exist "nginx\logs" mkdir "nginx\logs"
echo %SUCCESS% 目录创建完成

REM Check environment variables
echo %INFO% 检查环境变量...
if not exist ".env" (
    echo %WARNING% .env文件不存在，创建默认配置...
    (
        echo # CBSC Development Environment Variables
        echo # 数据库配置
        echo POSTGRES_PASSWORD=cbsc_dev_password
        echo POSTGRES_DB=cbsc_dev
        echo POSTGRES_USER=cbsc_dev
        echo.
        echo # Redis配置
        echo REDIS_PASSWORD=redis_dev_password
        echo.
        echo # 网关配置
        echo GATEWAY_SECRET_KEY=dev_secret_key_change_in_production
        echo JWT_SECRET=dev_jwt_secret_change_in_production
        echo.
        echo # 应用配置
        echo LOG_LEVEL=DEBUG
        echo ENVIRONMENT=development
        echo.
        echo # CORS配置
        echo CORS_ORIGINS=http://localhost:3000,http://localhost:3001
        echo.
        echo # 监控配置
        echo GRAFANA_PASSWORD=admin123
        echo.
        echo # 端口配置
        echo FRONTEND_PORT=3000
        echo UNIFIED_DASHBOARD_PORT=3001
        echo API_GATEWAY_PORT=8000
    ) > .env
    echo %SUCCESS% .env文件已创建
)
echo %SUCCESS% 环境变量检查完成

REM Stop existing services
echo %INFO% 停止现有服务...
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% down --remove-orphans >nul 2>&1
echo %SUCCESS% 现有服务已停止

REM Start core services
echo.
echo ========================================
echo 启动核心服务 (PostgreSQL, Redis)...
echo ========================================
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% up -d postgres redis

echo %INFO% 等待数据库服务启动...
timeout /t 10 /nobreak >nul

REM Wait for PostgreSQL to be ready
echo %INFO% 等待PostgreSQL就绪...
set /a counter=0
:wait_postgres
set /a counter+=1
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% exec -T postgres pg_isready -U cbsc_dev -d cbsc_dev >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% PostgreSQL已就绪
    goto :postgres_ready
)
if %counter% geq 30 (
    echo %ERROR% PostgreSQL启动超时
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto :wait_postgres
:postgres_ready

REM Wait for Redis to be ready
echo %INFO% 等待Redis就绪...
set /a counter=0
:wait_redis
set /a counter+=1
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% Redis已就绪
    goto :redis_ready
)
if %counter% geq 15 (
    echo %ERROR% Redis启动超时
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto :wait_redis
:redis_ready

echo %SUCCESS% 核心服务启动完成

REM Start application services
echo.
echo ========================================
echo 启动应用服务 (API Gateway, Frontend)...
echo ========================================
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% up -d api-gateway frontend unified-dashboard

echo %INFO% 等待API网关启动...
timeout /t 15 /nobreak >nul

REM Check API Gateway health
echo %INFO% 检查API网关状态...
set /a counter=0
:wait_gateway
set /a counter+=1
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% API网关已就绪
    goto :gateway_ready
)
if %counter% geq 30 (
    echo %WARNING% API网关启动超时，请检查日志
    goto :gateway_ready
)
timeout /t 2 /nobreak >nul
goto :wait_gateway
:gateway_ready

timeout /t 10 /nobreak >nul
echo %SUCCESS% 应用服务启动完成

REM Start optional development tools
echo.
echo ========================================
echo 启动可选开发工具...
echo ========================================
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% --profile tools up -d
timeout /t 5 /nobreak >nul
echo %SUCCESS% 开发工具启动完成

REM Check for backend services flag
if "%1"=="--with-backend" (
    echo.
    echo ========================================
    echo 启动后端服务...
    echo ========================================
    docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% --profile backend up -d
    timeout /t 20 /nobreak >nul
    echo %SUCCESS% 后端服务启动完成
)

REM Display service status
echo.
echo ========================================
echo 服务状态
echo ========================================
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% ps

echo.
echo ========================================
echo 服务访问地址
echo ========================================
echo API Gateway:     http://localhost:8000
echo API 文档:        http://localhost:8000/docs
echo 前端应用:        http://localhost:3000
echo 统一Dashboard:  http://localhost:3001
echo Grafana监控:     http://localhost:8080
echo.

echo PgAdmin:         http://localhost:5050
echo Redis Commander: http://localhost:8081
echo.

echo 数据库连接:
echo   PostgreSQL: localhost:5432
echo   Redis:      localhost:6379
echo.

REM Run health check
echo ========================================
echo 运行健康检查...
echo ========================================

REM Check API Gateway
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% ✅ API Gateway健康
) else (
    echo %ERROR% ❌ API Gateway不健康
)

REM Check Frontend
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% ✅ 前端应用健康
) else (
    echo %WARNING% ⚠️ 前端应用可能还在启动中
)

REM Check Database
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% exec -T postgres pg_isready -U cbsc_dev -d cbsc_dev >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% ✅ PostgreSQL健康
) else (
    echo %ERROR% ❌ PostgreSQL不健康
)

REM Check Redis
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo %SUCCESS% ✅ Redis健康
) else (
    echo %ERROR% ❌ Redis不健康
)

echo.
echo ========================================
echo 🎉 开发环境启动完成！
echo ========================================
echo.
echo 使用 'scripts\dev-start.bat --logs' 查看实时日志
echo 使用 'scripts\dev-start.bat --stop' 停止所有服务
echo.
echo 按任意键继续...
pause >nul
goto :end

:help
echo CBSC开发环境启动脚本
echo.
echo 用法: %0 [选项]
echo.
echo 选项:
echo   --with-backend    同时启动后端服务
echo   --stop           停止所有服务
echo   --restart        重启所有服务
echo   --logs           查看服务日志
echo   --status         显示服务状态
echo   --help           显示帮助信息
echo.
goto :end

:stop
echo ========================================
echo 停止所有服务...
echo ========================================
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% down --remove-orphans
echo %SUCCESS% 所有服务已停止
goto :end

:restart
call :stop
timeout /t 5 /nobreak >nul
call :main
goto :end

:logs
echo ========================================
echo 显示服务日志...
echo ========================================
docker-compose -f %COMPOSE_FILE% -p %PROJECT_NAME% logs -f --tail=100
goto :end

:status
call :show_service_status
call :run_health_check
goto :end

:main
REM Parse command line arguments
if "%1"=="--with-backend" (
    goto :start
) else if "%1"=="--stop" (
    goto :stop
) else if "%1"=="--restart" (
    goto :restart
) else if "%1"=="--logs" (
    goto :logs
) else if "%1"=="--status" (
    goto :status
) else if "%1"=="--help" (
    goto :help
) else if "%1"=="" (
    goto :start
) else (
    echo %ERROR% 未知选项: %1
    goto :help
)

:start
goto :start_process

:end
endlocal