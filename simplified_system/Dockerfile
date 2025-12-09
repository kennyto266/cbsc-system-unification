# 量化交易系统生产级 Docker 镜像
# 基于Ubuntu 20.04 LTS，优化性能和安全性
FROM ubuntu:20.04

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Hong_Kong

# 创建应用用户
RUN groupadd -r quantuser && useradd -r -g quantuser quantuser

# 基础系统更新和核心工具安装
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    htop \
    supervisor \
    nginx \
    redis-tools \
    postgresql-client \
    python3.9 \
    python3.9-dev \
    python3.9-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 设置Python环境
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# 创建应用目录
WORKDIR /app

# 复制requirements文件并安装Python依赖
COPY requirements.txt requirements.txt
COPY requirements_production.txt requirements_production.txt

# 安装核心依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_production.txt

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/
COPY deployment/ ./deployment/
COPY scripts/ ./scripts/

# 创建必要的目录
RUN mkdir -p /app/logs /app/data /app/cache /app/models /app/reports \
    && chown -R quantuser:quantuser /app

# 复制配置文件
COPY deployment/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deployment/nginx/nginx.conf /etc/nginx/sites-available/default

# 安装Supervisor
RUN pip install supervisor

# 暴露端口
EXPOSE 8000 8001 3000 9090 3001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 切换到非root用户
USER quantuser

# 启动命令
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]