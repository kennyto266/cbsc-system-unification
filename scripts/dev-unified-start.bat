@echo off
setlocal enabledelayedexpansion

REM CBSC Unified Development Environment Startup Script (Windows)
REM 统一开发环境启动脚本 (Windows版本)

set PROJECT_ROOT=%~dp0..
set COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.cbsc-unified.yml
set ENV_FILE=%PROJECT_ROOT%\.env
set LOG_FILE=%PROJECT_ROOT%\logs\startup.log

REM 颜色定义（Windows CMD不支持ANSI颜色，使用简单文本）
set INFO=[INFO]
set WARN=[WARN]
set ERROR=[ERROR]
set SUCCESS=[SUCCESS]

REM 创建日志目录
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM 日志函数
:log
echo %date% %time% %SUCCESS% %~1 >> "%LOG_FILE%"
echo %SUCCESS% %~1
goto :eof

:warn
echo %date% %time% %WARN% %~1 >> "%LOG_FILE%"
echo %WARN% %~1
goto :eof

:error
echo %date% %time% %ERROR% %~1 >> "%LOG_FILE%"
echo %ERROR% %~1
goto :eof

:info
echo %date% %time% %INFO% %~1 >> "%LOG_FILE%"
echo %INFO% %~1
goto :eof

REM 检查依赖
:check_dependencies
call :log "检查系统依赖..."

REM 检查Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Docker未安装，请先安装Docker Desktop"
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        call :error "Docker Compose未安装，请先安装Docker Compose"
        exit /b 1
    )
)

REM 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    call :warn "Node.js未安装，前端服务可能无法正常运行"
)

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        call :warn "Python未安装，API服务可能无法正常运行"
    )
)

call :log "依赖检查完成"
goto :eof

REM 创建环境文件
:create_env_file
if not exist "%ENV_FILE%" (
    call :log "创建环境配置文件..."

    REM 生成随机密码
    for /f "tokens=1-6 delims= " %%a in ('wmic os get localdatetime') do (
        if not "%%a"=="" (
            set datetime=%%a
            goto :done_datetime
        )
    )
    :done_datetime
    set random_num=%random%

    (
        echo # CBSC系统环境配置
        echo COMPOSE_PROJECT_NAME=cbsc-unified
        echo.
        echo # 数据库配置
        echo POSTGRES_PASSWORD=cbsc_secure_2024_%random_num%
        echo POSTGRES_USER=cbsc_admin
        echo POSTGRES_DB=cbsc_system
        echo.
        echo # Redis配置
        echo REDIS_PASSWORD=
        echo.
        echo # JWT配置
        echo JWT_SECRET=cbsc_jwt_secret_%datetime:~0,8%_%random_num%
        echo GATEWAY_SECRET_KEY=cbsc_gateway_secret_%datetime:~0,8%_%random_num%
        echo.
        echo # OAuth2配置
        echo GOOGLE_CLIENT_ID=
        echo GOOGLE_CLIENT_SECRET=
        echo GITHUB_CLIENT_ID=
        echo GITHUB_CLIENT_SECRET=
        echo.
        echo # CSRF配置
        echo CSRF_SECRET=cbsc_csrf_secret_%datetime:~0,8%_%random_num%
        echo.
        echo # 监控配置
        echo GRAFANA_PASSWORD=admin123
        echo.
        echo # 日志配置
        echo LOG_LEVEL=INFO
        echo ENVIRONMENT=development
        echo.
        echo # 网络配置
        echo NETWORK_SUBNET=172.20.0.0/16
        echo.
        echo # 端口配置
        echo API_GATEWAY_PORT=8000
        echo USER_MANAGEMENT_PORT=3004
        echo STRATEGY_DASHBOARD_PORT=3003
        echo CONFIG_SERVICE_PORT=3005
        echo FRONTEND_PORT=3000
        echo UNIFIED_DASHBOARD_PORT=3001
        echo NGINX_PORT=80
        echo NGINX_SSL_PORT=443
        echo.
        echo # 监控端口
        echo GRAFANA_PORT=3002
        echo PROMETHEUS_PORT=9090
        echo JAEGER_PORT=16686
        echo KIBANA_PORT=5601
    ) > "%ENV_FILE%"

    call :log "环境配置文件已创建: %ENV_FILE%"
    call :warn "请根据需要修改环境配置文件"
) else (
    call :log "环境配置文件已存在: %ENV_FILE%"
)
goto :eof

REM 清理旧容器
:cleanup_containers
call :log "清理旧容器..."
cd /d "%PROJECT_ROOT%"

docker-compose -f "%COMPOSE_FILE%" down --remove-orphans 2>nul
docker network prune -f 2>nul

call :log "容器清理完成"
goto :eof

REM 创建网络
:create_network
call :log "创建Docker网络..."

docker network inspect cbsc-network >nul 2>&1
if %errorlevel% neq 0 (
    docker network create cbsc-network --subnet=172.20.0.0/16 >nul 2>&1
    if !errorlevel! neq 0 (
        call :warn "网络创建失败，可能已存在"
    )
)

call :log "Docker网络已就绪"
goto :eof

REM 启动基础设施服务
:start_infrastructure
call :log "启动基础设施服务..."
cd /d "%PROJECT_ROOT%"

REM 启动基础服务（Redis, PostgreSQL）
docker-compose -f "%COMPOSE_FILE%" up -d redis postgres

call :log "等待数据库启动..."
timeout /t 10 /nobreak >nul

REM 等待数据库就绪
set /a db_wait=0
:check_db
set /a db_wait+=1
docker exec cbsc-postgres pg_isready -U cbsc_admin -d cbsc_system >nul 2>&1
if %errorlevel% equ 0 (
    call :log "数据库已就绪"
    goto :db_ready
)
if %db_wait% geq 30 (
    call :error "数据库启动超时"
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto :check_db
:db_ready

REM 等待Redis就绪
set /a redis_wait=0
:check_redis
set /a redis_wait+=1
docker exec cbsc-redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    call :log "Redis已就绪"
    goto :redis_ready
)
if %redis_wait% geq 15 (
    call :error "Redis启动超时"
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto :check_redis
:redis_ready

call :log "基础设施服务启动完成"
goto :eof

REM 启动核心服务
:start_core_services
call :log "启动核心服务..."
cd /d "%PROJECT_ROOT%"

REM 启动API网关和核心服务
docker-compose -f "%COMPOSE_FILE%" up -d api-gateway user-management strategy-dashboard config-service

call :log "等待核心服务启动..."
timeout /t 15 /nobreak >nul

call :log "核心服务启动完成"
goto :eof

REM 启动前端服务
:start_frontend_services
call :log "启动前端服务..."
cd /d "%PROJECT_ROOT%"

REM 启动前端服务
docker-compose -f "%COMPOSE_FILE%" up -d frontend-dashboard unified-dashboard nginx

call :log "前端服务启动完成"
goto :eof

REM 启动监控服务
:start_monitoring_services
call :log "启动监控服务..."
cd /d "%PROJECT_ROOT%"

REM 启动监控服务
docker-compose -f "%COMPOSE_FILE%" up -d prometheus grafana jaeger elasticsearch logstash kibana

call :log "监控服务启动完成"
goto :eof

REM 检查服务状态
:check_services
call :log "检查服务状态..."
cd /d "%PROJECT_ROOT%"

echo.
echo === 容器状态 ===
docker-compose -f "%COMPOSE_FILE%" ps

echo.
echo === 服务健康检查 ===

REM 检查API网关
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API网关: http://localhost:8000
) else (
    echo ❌ API网关: 不可访问
)

REM 检查前端Dashboard
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端Dashboard: http://localhost:3000
) else (
    echo ❌ 前端Dashboard: 不可访问
)

REM 检查统一Dashboard
curl -f http://localhost:3001 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 统一Dashboard: http://localhost:3001
) else (
    echo ❌ 统一Dashboard: 不可访问
)

REM 检查Grafana
curl -f http://localhost:3002/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Grafana: http://localhost:3002 ^(admin/admin123^)
) else (
    echo ⚠️  Grafana: 启动中...
)

REM 检查Prometheus
curl -f http://localhost:9090/-/healthy >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Prometheus: http://localhost:9090
) else (
    echo ⚠️  Prometheus: 启动中...
)

REM 检查Kibana
curl -f http://localhost:5601/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Kibana: http://localhost:5601
) else (
    echo ⚠️  Kibana: 启动中...
)

goto :eof

REM 显示访问信息
:show_access_info
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║           🚀 CBSC统一开发环境已启动完成                       ║
echo ║                                                           ║
echo ║  🌐 主要服务访问地址:                                        ║
echo ║  • API网关:        http://localhost:8000                    ║
echo ║  • 前端Dashboard:  http://localhost:3000                    ║
echo ║  • 统一Dashboard:  http://localhost:3001                    ║
echo ║  • Nginx代理:       http://localhost:80                      ║
echo ║                                                             ║
echo ║  📊 监控服务访问地址:                                        ║
echo ║  • Grafana:        http://localhost:3002 ^(admin/admin123^)    ║
echo ║  • Prometheus:     http://localhost:9090                    ║
echo ║  • Jaeger:         http://localhost:16686                   ║
echo ║  • Kibana:         http://localhost:5601                    ║
echo ║                                                             ║
echo ║  📚 API文档:                                                ║
echo ║  • API文档:         http://localhost:8000/docs              ║
echo ║  • ReDoc文档:       http://localhost:8000/redoc             ║
echo ║                                                             ║
echo ║  🔧 管理命令:                                                ║
echo ║  • 查看日志:         docker logs -f [container_name]        ║
echo ║  • 停止环境:         scripts\dev-unified-stop.bat           ║
echo ║  • 重启服务:         docker restart [container_name]         ║
echo ║                                                             ║
echo ║  📝 配置文件: .env                                          ║
echo ║  📋 启动日志: %LOG_FILE%                                    ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════════╝
goto :eof

REM 主函数
:main
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║        🚀 CBSC统一开发环境启动脚本                          ║
echo ║                                                           ║
echo ║  统一API网关 ^| 服务发现 ^| 监控系统 ^| 开发环境              ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM 检查是否在项目根目录
if not exist "%COMPOSE_FILE%" (
    call :error "未找到Docker Compose文件: %COMPOSE_FILE%"
    call :error "请确保在项目根目录运行此脚本"
    exit /b 1
)

REM 执行启动步骤
call :log "开始启动CBSC统一开发环境..."

call :check_dependencies
call :create_env_file
call :cleanup_containers
call :create_network
call :start_infrastructure
call :start_core_services
call :start_frontend_services
call :start_monitoring_services
call :check_services
call :show_access_info

call :log "CBSC统一开发环境启动完成！"

echo.
echo 按任意键退出...
pause >nul
goto :eof

REM 执行主函数
call :main %*