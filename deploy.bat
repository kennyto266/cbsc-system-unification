@echo off
REM CBSC Strategy API Docker部署脚本 (Windows版本)

setlocal enabledelayedexpansion

echo ==========================================
echo CBSC Strategy API Docker Deployment
echo ==========================================

REM 设置颜色代码
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "NC=[0m"

REM 检查Docker是否安装
:check_docker
echo %GREEN%[INFO]%NC% Checking Docker environment...
docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker is not installed, please install Docker first
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker Compose is not installed, please install Docker Compose first
    pause
    exit /b 1
)

echo %GREEN%[INFO]%NC% Docker environment check passed
goto :eof

REM 创建必要的目录
:create_directories
echo %GREEN%[INFO]%NC% Creating necessary directories...

if not exist logs\nginx mkdir logs\nginx
if not exist data mkdir data
if not exist database mkdir database
if not exist redis mkdir redis
if not exist nginx\ssl mkdir nginx\ssl

REM 创建Redis配置文件
if not exist redis\redis.conf (
    echo %GREEN%[INFO]%NC% Creating Redis configuration file...
    (
        echo # Redis Configuration File
        echo bind 0.0.0.0
        echo port 6379
        echo timeout 0
        echo keepalive 300
        echo databases 16
        echo.
        echo # Persistence configuration
        echo save 900 1
        echo save 300 10
        echo save 60 10000
        echo.
        echo # Log configuration
        echo loglevel notice
        echo logfile /var/log/redis/redis.log
        echo.
        echo # Security configuration
        echo # requirepass your-redis-password
        echo.
        echo # Memory configuration
        echo maxmemory 256mb
        echo maxmemory-policy allkeys-lru
    ) > redis\redis.conf
)

REM 创建Nginx配置文件
if not exist nginx\nginx.conf (
    echo %GREEN%[INFO]%NC% Creating Nginx configuration file...
    (
        echo events {
        echo     worker_connections 1024;
        echo }
        echo.
        echo http {
        echo     upstream cbsc_api {
        echo         server cbsc-strategy-api:3004;
        echo     }
        echo.
        echo     server {
        echo         listen 80;
        echo         server_name localhost;
        echo.
        echo         location / {
        echo             proxy_pass http://cbsc_api;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo.
        echo         location /health {
        echo             proxy_pass http://cbsc_api/health;
        echo         }
        echo     }
        echo }
    ) > nginx\nginx.conf
)

REM 创建数据库初始化脚本
if not exist database\init.sql (
    echo %GREEN%[INFO]%NC% Creating database initialization script...
    (
        echo -- CBSC Strategy API Database Initialization Script
        echo.
        echo -- Create extensions
        echo CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        echo CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        echo.
        echo -- Create users table
        echo CREATE TABLE IF NOT EXISTS users ^(
        echo     id SERIAL PRIMARY KEY,
        echo     username VARCHAR^(50^) UNIQUE NOT NULL,
        echo     email VARCHAR^(255^) UNIQUE NOT NULL,
        echo     password_hash VARCHAR^(255^) NOT NULL,
        echo     is_active BOOLEAN DEFAULT TRUE,
        echo     is_admin BOOLEAN DEFAULT FALSE,
        echo     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW^(^),
        echo     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW^(^)
        echo ^);
        echo.
        echo -- Create strategies table
        echo CREATE TABLE IF NOT EXISTS strategies ^(
        echo     id UUID PRIMARY KEY DEFAULT gen_random_uuid^(^),
        echo     user_id INTEGER REFERENCES users^(id^) ON DELETE CASCADE,
        echo     name VARCHAR^(255^) NOT NULL,
        echo     description TEXT,
        echo     strategy_type VARCHAR^(50^) NOT NULL,
        echo     status VARCHAR^(20^) DEFAULT 'inactive',
        echo     risk_level VARCHAR^(20^) DEFAULT 'medium',
        echo     parameters JSONB DEFAULT '{}',
        echo     is_active BOOLEAN DEFAULT FALSE,
        echo     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW^(^),
        echo     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW^(^),
        echo     created_by INTEGER REFERENCES users^(id^)
        echo ^);
        echo.
        echo -- Create indexes
        echo CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies^(user_id^);
        echo CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies^(status^);
        echo CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies^(strategy_type^);
        echo CREATE INDEX IF NOT EXISTS idx_users_email ON users^(email^);
        echo CREATE INDEX IF NOT EXISTS idx_users_username ON users^(username^);
        echo.
        echo -- Insert sample data
        echo INSERT INTO users ^(username, email, password_hash, is_admin^)
        echo VALUES ^('admin', 'admin@cbsc.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G', true^)
        echo ON CONFLICT ^(username^) DO NOTHING;
    ) > database\init.sql
)
goto :eof

REM 构建和启动服务
:deploy_services
echo %GREEN%[INFO]%NC% Building Docker images...
docker build -t cbsc-api:latest .
docker-compose -f docker-compose.cbsc-api.yml build

echo %GREEN%[INFO]%NC% Starting services...
docker-compose -f docker-compose.cbsc-api.yml up -d

echo %GREEN%[INFO]%NC% Waiting for services to start...
timeout /t 30 /nobreak
goto :eof

REM 检查服务状态
:check_services
echo %GREEN%[INFO]%NC% Checking service status...

REM 检查API服务
curl -f http://localhost:3004/health >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% CBSC Strategy API service failed to start
    docker-compose -f docker-compose.cbsc-api.yml logs cbsc-strategy-api
) else (
    echo %GREEN%[INFO]%NC% ✓ CBSC Strategy API service is running normally
)

REM 检查数据库连接
docker exec cbsc-postgres pg_isready -U cbsc_admin -d cbsc_production >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% PostgreSQL database connection failed
) else (
    echo %GREEN%[INFO]%NC% ✓ PostgreSQL database connection is normal
)

REM 检查Redis连接
docker exec cbsc-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Redis cache service connection failed
) else (
    echo %GREEN%[INFO]%NC% ✓ Redis cache service is normal
)
goto :eof

REM 显示服务信息
:show_info
echo %GREEN%[INFO]%NC% Service deployment completed!
echo.
echo Service access addresses:
echo   - CBSC Strategy API: http://localhost:3004
echo   - API Documentation: http://localhost:3004/docs
echo   - Database: localhost:5432
echo   - Redis: localhost:6379
echo.
echo Common commands:
echo   - View logs: docker-compose -f docker-compose.cbsc-api.yml logs -f
echo   - Stop services: docker-compose -f docker-compose.cbsc-api.yml down
echo   - Restart services: docker-compose -f docker-compose.cbsc-api.yml restart
echo.
goto :eof

REM 主函数
:main
set "command=%1"
if "%command%"=="" set "command=deploy"

if "%command%"=="deploy" (
    call :check_docker
    call :create_directories
    call :deploy_services
    call :check_services
    call :show_info
) else if "%command%"=="stop" (
    echo %GREEN%[INFO]%NC% Stopping all services...
    docker-compose -f docker-compose.cbsc-api.yml down
) else if "%command%"=="restart" (
    echo %GREEN%[INFO]%NC% Restarting all services...
    docker-compose -f docker-compose.cbsc-api.yml restart
) else if "%command%"=="logs" (
    docker-compose -f docker-compose.cbsc-api.yml logs -f
) else if "%command%"=="status" (
    docker-compose -f docker-compose.cbsc-api.yml ps
) else (
    echo Usage: %0 [deploy^|stop^|restart^|logs^|status]
    echo   deploy  - Deploy services ^(default^)
    echo   stop    - Stop services
    echo   restart - Restart services
    echo   logs    - View logs
    echo   status  - View status
    pause
    exit /b 1
)

pause