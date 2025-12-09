FROM nvidia/cuda:12.0-runtime-ubuntu22.04

# 設置環境變量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$PATH:$CUDA_HOME/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDA_HOME/lib64

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    # Python 編譯依賴
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    gcc \
    g++ \
    # 數學庫依賴
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    # 系統工具
    curl \
    wget \
    git \
    vim \
    htop \
    # 網絡工具
    netcat-openbsd \
    # 監控工具
    procps \
    # 清理
    && rm -rf /var/lib/apt/lists/*

# 升級 pip
RUN python3.11 -m pip install --upgrade pip

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .
COPY requirements-gpu.txt .

# 安裝 Python 依賴
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# 安裝 GPU 相關依賴（如果可用）
RUN python3.11 -m pip install --no-cache-dir -r requirements-gpu.txt || \
    echo "GPU requirements installation failed, using CPU fallback"

# 複製應用代碼
COPY . .

# 創建必要的目錄
RUN mkdir -p /app/logs /app/data /app/temp

# 設置權限
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令
CMD ["python3.11", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]