# Authentication Service Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY docker/auth/entrypoint.sh .
COPY docker/auth/keys/ ./keys/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set permissions
RUN chown -R appuser:appuser /app && \
    chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3006

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3006/health || exit 1

# Run the application
CMD ["./entrypoint.sh"]