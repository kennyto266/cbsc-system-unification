"""
Migration: Create HKEX market data tables
Date: 2025-12-29

Usage:
    python src/db/migrations/001_create_hkex_tables.py          # Create tables
    python src/db/migrations/001_create_hkex_tables.py down    # Rollback

Requirements:
    - PostgreSQL must be running
    - Set DATABASE_URL environment variable or use default
"""
from sqlalchemy import create_engine, text
import os
import sys

# Try Docker Compose database URL first, then fallback to localhost
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy'
)

def check_database_connection():
    """Test database connection before proceeding"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running (docker-compose up -d postgres)")
        print("2. DATABASE_URL environment variable is set correctly")
        print(f"\nCurrent DATABASE_URL: {DATABASE_URL}")
        return False

def upgrade():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Create raw data table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hkex_raw_data (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                trading_volume INTEGER,
                advanced_stocks INTEGER,
                declined_stocks INTEGER,
                unchanged_stocks INTEGER,
                turnover_hkd BIGINT,
                deals INTEGER,
                morning_close DECIMAL(10,2),
                afternoon_close DECIMAL(10,2),
                change_value DECIMAL(10,2),
                change_percent DECIMAL(10,4),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))

        # Create indicators table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_indicators (
                date DATE PRIMARY KEY REFERENCES hkex_raw_data(date) ON DELETE CASCADE,
                advance_decline_ratio DECIMAL(10,4),
                volume_change_percent DECIMAL(10,4),
                sentiment_score DECIMAL(10,2),
                breadth_momentum DECIMAL(10,4),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))

        # Create trigger function
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION calculate_indicators()
            RETURNS TRIGGER AS $$
            DECLARE
                prev_volume BIGINT;
                volume_pct DECIMAL(10,4);
                total_stocks INTEGER;
            BEGIN
                -- Get previous day's volume for change calculation
                SELECT turnover_hkd INTO prev_volume
                FROM hkex_raw_data
                WHERE date < NEW.date
                ORDER BY date DESC
                LIMIT 1;

                -- Calculate volume change percent
                IF prev_volume IS NOT NULL AND prev_volume > 0 THEN
                    volume_pct = ((NEW.turnover_hkd - prev_volume)::DECIMAL / prev_volume) * 100;
                ELSE
                    volume_pct = 0;
                END IF;

                -- Calculate total stocks
                total_stocks = NEW.advanced_stocks + NEW.declined_stocks + NEW.unchanged_stocks;

                -- Insert or update indicators
                INSERT INTO market_indicators (
                    date,
                    advance_decline_ratio,
                    volume_change_percent,
                    sentiment_score,
                    breadth_momentum
                )
                VALUES (
                    NEW.date,
                    CASE WHEN NEW.declined_stocks > 0
                         THEN NEW.advanced_stocks::DECIMAL / (NEW.declined_stocks + 1)
                         ELSE NEW.advanced_stocks::DECIMAL END,
                    volume_pct,
                    (
                        CASE WHEN NEW.declined_stocks > 0
                             THEN NEW.advanced_stocks::DECIMAL / (NEW.declined_stocks + 1)
                             ELSE NEW.advanced_stocks::DECIMAL END * 0.4 +
                        volume_pct * 0.3 +
                        CASE WHEN total_stocks > 0
                             THEN (NEW.advanced_stocks::DECIMAL / total_stocks) * 0.3
                             ELSE 0 END
                    ) * 100,
                    0  -- Phase 2 implementation
                )
                ON CONFLICT (date) DO UPDATE SET
                    advance_decline_ratio = EXCLUDED.advance_decline_ratio,
                    volume_change_percent = EXCLUDED.volume_change_percent,
                    sentiment_score = EXCLUDED.sentiment_score,
                    updated_at = NOW();

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        # Create trigger
        conn.execute(text("""
            DROP TRIGGER IF EXISTS trigger_calculate_indicators ON hkex_raw_data;
            CREATE TRIGGER trigger_calculate_indicators
            AFTER INSERT ON hkex_raw_data
            FOR EACH ROW
            EXECUTE FUNCTION calculate_indicators();
        """))

        conn.commit()
        print("Migration completed: hkex tables created")

def downgrade():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_calculate_indicators ON hkex_raw_data;"))
        conn.execute(text("DROP FUNCTION IF EXISTS calculate_indicators();"))
        conn.execute(text("DROP TABLE IF EXISTS market_indicators;"))
        conn.execute(text("DROP TABLE IF EXISTS hkex_raw_data;"))
        conn.commit()
        print("Rollback completed: hkex tables dropped")

if __name__ == "__main__":
    # Check database connection first
    if not check_database_connection():
        sys.exit(1)

    # Run migration or rollback
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()
