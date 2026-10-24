# Multi-stage Dockerfile for Unified Backtesting Framework
# Stage 1: Base Python environment
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Hong_Kong

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    git \
    curl \
    wget \
    unzip \
    tzdata \
    procps \
    htop \
    iotop \
    net-tools \
    redis-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create non-root user
RUN groupadd -r backtest && useradd -r -g backtest backtest

# Create app directory
WORKDIR /app

# Stage 2: Build dependencies
FROM base as builder

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production runtime
FROM base as production

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY *.py ./

# Create necessary directories
RUN mkdir -p logs data cache results temp && \
    chown -R backtest:backtest /app

# Switch to non-root user
USER backtest

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "main.py"]