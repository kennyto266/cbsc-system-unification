# CBSC Strategy API Database Configuration
# Generated on: 2025-12-13T16:56:41.943622

# =============================================================================
# PostgreSQL Database Configuration (Primary)
# =============================================================================
# Connection settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cbsc_production
POSTGRES_USER=cbsc_admin
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env or environment}

# Full connection URL (password injected from POSTGRES_PASSWORD env var)
DATABASE_URL=postgresql://cbsc_admin:${POSTGRES_PASSWORD}@localhost:5432/cbsc_production

# =============================================================================
# Connection Pool Configuration
# =============================================================================
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# =============================================================================
# SQLite Configuration (Fallback for Development)
# =============================================================================
# SQLite database path for development/testing
SQLITE_DB_PATH=./data/cbsc_dev.db
USE_SQLITE_FALLBACK=false

# =============================================================================
# Database Schema Settings
# =============================================================================
# Auto-migration settings
AUTO_MIGRATE=true
SCHEMA_VERSION=1.0

# =============================================================================
# Database Backups
# =============================================================================
BACKUP_ENABLED=false
BACKUP_SCHEDULE=0 2 * * *
BACKUP_PATH=./backups
BACKUP_RETENTION_DAYS=30
