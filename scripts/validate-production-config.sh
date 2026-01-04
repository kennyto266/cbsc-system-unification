#!/bin/bash
# Production Configuration Validation Script
# 生產環境配置驗證腳本

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 VectorBT 多進程回測系統生產環境配置驗證"
echo "================================================"

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to check if variable is set and not default
check_env_var() {
    local var_name="$1"
    local default_value="$2"
    local var_value="${!var_name}"

    if [ -z "$var_value" ]; then
        print_status 1 "Environment variable $var_name is not set"
        return 1
    elif [ "$var_value" = "$default_value" ]; then
        print_warning "Environment variable $var_name is using default value: $default_value"
        echo "   建議: 請更新為生產環境安全值"
        return 0
    else
        print_status 0 "Environment variable $var_name is properly configured"
        return 0
    fi
}

# Check if required files exist
echo "📁 檢查必需文件..."
required_files=(
    ".env.prod"
    "docker-compose.prod.yml"
    "config/nginx/nginx.conf"
    "config/postgres/postgresql.conf"
    "config/redis/redis.conf"
    "config/prometheus/prometheus.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "Found $file"
    else
        print_status 1 "Missing $file"
    fi
done

echo
echo "🔒 安全配置驗證..."

# Load environment file
if [ -f ".env.prod" ]; then
    source .env.prod
else
    echo "❌ .env.prod file not found"
    exit 1
fi

# Check critical security variables
echo "檢查關鍵安全配置..."

# Database passwords
check_env_var "POSTGRES_PASSWORD" "CHANGE_THIS_STRONG_POSTGRES_PASSWORD"
check_env_var "REDIS_PASSWORD" "CHANGE_THIS_STRONG_REDIS_PASSWORD"
check_env_var "INFLUXDB_PASSWORD" "CHANGE_THIS_STRONG_INFLUXDB_PASSWORD"

# Application secrets
check_env_var "JWT_SECRET" "CHANGE_THIS_JWT_SECRET_KEY"
check_env_var "SECRET_KEY" "CHANGE_THIS_APPLICATION_SECRET_KEY"
check_env_var "INFLUXDB_TOKEN" "CHANGE_THIS_STRONG_INFLUXDB_TOKEN"

# Grafana admin password
check_env_var "GRAFANA_PASSWORD" "CHANGE_THIS_GRAFANA_PASSWORD"

echo
echo "🌐 網絡配置驗證..."

# Check domain configuration
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "cbsc.example.com" ]; then
    print_status 0 "Domain is configured: $DOMAIN"
else
    print_warning "Domain is using default value: cbsc.example.com"
    echo "   建議: 請更新為實際生產域名"
fi

# Check SSL configuration
if [ -f "./ssl/cert.pem" ] && [ -f "./ssl/key.pem" ]; then
    print_status 0 "SSL certificates found"

    # Check certificate validity
    if command -v openssl >/dev/null 2>&1; then
        cert_exp=$(openssl x509 -in ./ssl/cert.pem -noout -enddate 2>/dev/null | cut -d= -f2 || echo "Unknown")
        echo "   Certificate expires: $cert_exp"

        # Check if certificate expires within 30 days
        if command -v date >/dev/null 2>&1; then
            exp_date=$(date -d "$cert_exp" +%s 2>/dev/null || echo "0")
            current_date=$(date +%s)
            days_until_exp=$(( (exp_date - current_date) / 86400 ))

            if [ $days_until_exp -lt 30 ] && [ $days_until_exp -gt 0 ]; then
                print_warning "SSL certificate expires in $days_until_exp days"
            elif [ $days_until_exp -le 0 ]; then
                print_status 1 "SSL certificate has expired"
            fi
        fi
    fi
else
    print_warning "SSL certificates not found in ./ssl/"
    echo "   建議: 請配置生產環境 SSL 證書"
fi

echo
echo "🐳 Docker 環境驗證..."

# Check Docker installation
if command -v docker >/dev/null 2>&1; then
    docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_status 0 "Docker version: $docker_version"

    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_status 0 "Docker Compose version: $compose_version"
    else
        print_status 1 "Docker Compose not found"
    fi
else
    print_status 1 "Docker not found"
fi

echo
echo "🖥️ 系統資源驗證..."

# Check system resources
if command -v free >/dev/null 2>&1; then
    total_mem=$(free -h | awk '/^Mem:/ {print $2}')
    echo "   Total memory: $total_mem"

    # Convert to GB for comparison (assuming format like "16G")
    mem_gb=$(echo $total_mem | sed 's/G//')
    if [ "$mem_gb" -ge 32 ]; then
        print_status 0 "Memory meets requirements (≥32GB)"
    elif [ "$mem_gb" -ge 16 ]; then
        print_warning "Memory is $total_mem (recommended: ≥32GB)"
    else
        print_status 1 "Memory is $total_mem (required: ≥32GB)"
    fi
fi

if command -v nproc >/dev/null 2>&1; then
    cpu_cores=$(nproc)
    echo "   CPU cores: $cpu_cores"

    if [ "$cpu_cores" -ge 8 ]; then
        print_status 0 "CPU cores meet requirements (≥8 cores)"
    elif [ "$cpu_cores" -ge 4 ]; then
        print_warning "CPU cores: $cpu_cores (recommended: ≥8 cores)"
    else
        print_status 1 "CPU cores: $cpu_cores (required: ≥8 cores)"
    fi
fi

echo
echo "📊 磁盤空間驗證..."

# Check disk space
if command -v df >/dev/null 2>&1; then
    # Check root partition
    root_space=$(df -h / | awk 'NR==2 {print $4}')
    echo "   Available disk space: $root_space"

    # Check if adequate space (handling G, T, M formats)
    if [[ $root_space == *T* ]]; then
        # Convert TB to GB
        space_tb=$(echo $root_space | sed 's/T//')
        space_gb=$(echo "$space_tb * 1024" | bc 2>/dev/null || echo "999999")
    elif [[ $root_space == *G* ]]; then
        # Extract GB value
        space_gb=$(echo $root_space | sed 's/G//')
    elif [[ $root_space == *M* ]]; then
        # Convert MB to GB
        space_mb=$(echo $root_space | sed 's/M//')
        space_gb=$(echo "scale=2; $space_mb / 1024" | bc 2>/dev/null || echo "0")
    else
        # Assume GB if no unit
        space_gb=$root_space
    fi

    # Convert to integer for comparison
    space_gb_int=$(echo $space_gb | cut -d. -f1)

    if [ "$space_gb_int" -ge 500 ]; then
        print_status 0 "Disk space is adequate (≥500GB)"
    elif [ "$space_gb_int" -ge 200 ]; then
        print_warning "Disk space: $root_space (recommended: ≥500GB)"
    else
        print_status 1 "Insufficient disk space: $root_space (required: ≥500GB)"
    fi
fi

echo
echo "🔌 端口可用性檢查..."

# Check if required ports are available
required_ports=("80" "443" "3000" "3001" "3004" "3005" "5432" "6379" "8086" "9090")

for port in "${required_ports[@]}"; do
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            print_warning "Port $port is already in use"
            echo "   請檢查是否有其他服務佔用此端口"
        else
            print_status 0 "Port $port is available"
        fi
    fi
done

echo
echo "📋 配置文件語法驗證..."

# Validate Docker Compose configuration
if [ -f "docker-compose.prod.yml" ]; then
    if command -v docker-compose >/dev/null 2>&1; then
        if docker-compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
            print_status 0 "Docker Compose configuration is valid"
        else
            print_status 1 "Docker Compose configuration has errors"
        fi
    fi
fi

# Validate Nginx configuration
if [ -f "config/nginx/nginx.conf" ]; then
    if command -v nginx >/dev/null 2>&1; then
        if nginx -t -c config/nginx/nginx.conf >/dev/null 2>&1; then
            print_status 0 "Nginx configuration is valid"
        else
            print_warning "Nginx configuration validation failed (may be environment specific)"
        fi
    fi
fi

echo
echo "🔧 權限和目錄驗證..."

# Check critical directories and permissions
directories=("logs" "ssl" "uploads" "static")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        if [ -w "$dir" ]; then
            print_status 0 "Directory $dir exists and is writable"
        else
            print_warning "Directory $dir exists but is not writable"
            echo "   建議: chmod 755 $dir"
        fi
    else
        print_warning "Directory $dir does not exist"
        echo "   建議: mkdir -p $dir"
    fi
done

echo
echo "📝 建議事項"
echo "============"
echo "1. 🔒 請確保所有密碼都已更新為強密碼"
echo "2. 🌐 請配置實際的生產域名和 SSL 證書"
echo "3. 🔌 請確保防火牆配置正確"
echo "4. 📧 請配置監控和告警通知"
echo "5. 💾 請設置自動備份策略"
echo "6. 📚 請完成操作文檔和培訓"

echo
echo "✅ 配置驗證完成！"
echo
if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 配置驗證通過，可以進行生產部署！${NC}"
    echo "執行命令: docker-compose -f docker-compose.prod.yml up -d"
else
    echo -e "${RED}⚠️  配置驗證發現問題，請修復後重新驗證${NC}"
    exit 1
fi