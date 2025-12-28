# CBSC 策略管理系統 Dockerfile - 策略架構 v2 支持
# Multi-stage build for production deployment with strategy refactoring support

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STRATEGY_API_VERSION=2

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY docs/ ./docs/


# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/uploads /app/static \
    && mkdir -p /app/logs/strategies \
    && mkdir -p /app/logs/api \
    && mkdir -p /app/logs/websocket

# Set permissions for logs and data directories
RUN chmod 755 /app/data /app/logs /app/uploads /app/static

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# Expose ports
EXPOSE 3004

# Health check with enhanced checks
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3004/health \
        && curl -f http://localhost:3004/api/v2/strategies/health || exit 1

# Add labels for metadata
LABEL maintainer="CBSC Team" \
      version="2.0.0" \
      description="CBSC Strategy Management System with Refactored Architecture" \
      api.v1.url="http://localhost:3004/api/v1" \
      api.v2.url="http://localhost:3004/api/v2" \
      docs.url="http://localhost:3004/docs"

# Set entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command with worker scaling
CMD ["python", "-m", "uvicorn", "src.api.main:app", \
      "--host", "0.0.0.0", \
      "--port", "3004", \
      "--workers", "4", \
      "--worker-class", "uvicorn.workers.UvicornWorker", \
      "--access-log", \
      "--log-level", "info"]
