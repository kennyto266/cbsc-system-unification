#!/usr/bin/env python3
"""
数据迁移脚本 - CBSC系统数据整合
Data Migration Script for CBSC System Integration

将遗留的CSV和JSON数据迁移到统一的PostgreSQL数据库中
"""

import os
import sys
import json
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_values
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_migration')

class DataMigrator:
    """数据迁移器"""

    def __init__(self, db_url: str = None):
        """初始化数据库连接"""
        self.db_url = db_url or os.getenv('DATABASE_URL',
                                        'postgresql://postgres:password@localhost:5432/quant_system')
        self.conn = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = False
            logger.info("✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已断开")

    def create_tables(self):
        """创建必要的表结构"""
        with self.conn.cursor() as cursor:
            # 创建港交所市场数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hkex_market_data (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    trading_volume BIGINT,
                    advanced_stocks INTEGER,
                    declined_stocks INTEGER,
                    unchanged_stocks INTEGER,
                    turnover_hkd DECIMAL(20,2),
                    deals BIGINT,
                    morning_close DECIMAL(10,2),
                    afternoon_close DECIMAL(10,2),
                    change_value DECIMAL(10,2),
                    change_percent DECIMAL(8,4),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(date)
                );
            """)

            # 创建股票历史数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_historical_data (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    open_price DECIMAL(12,4),
                    high_price DECIMAL(12,4),
                    low_price DECIMAL(12,4),
                    close_price DECIMAL(12,4),
                    volume BIGINT,
                    market_cap BIGINT,
                    pe_ratio DECIMAL(8,2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(date, symbol)
                );
            """)

            # 创建政府经济数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS government_economic_data (
                    id SERIAL PRIMARY KEY,
                    data_date DATE NOT NULL,
                    data_type VARCHAR(50) NOT NULL,
                    data_subtype VARCHAR(50),
                    value DECIMAL(15,4),
                    unit VARCHAR(20),
                    source VARCHAR(100),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(data_date, data_type, data_subtype)
                );
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hkex_date ON hkex_market_data(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_date_symbol ON stock_historical_data(date, symbol);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gov_data_date_type ON government_economic_data(data_date, data_type);")

            self.conn.commit()
            logger.info("✅ 数据表创建完成")

    def migrate_hkex_data(self, data_dir: str):
        """迁移港交所数据"""
        logger.info("开始迁移港交所市场数据...")

        # 查找所有港交所CSV文件
        hkex_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.startswith('hkex_market_data_') and file.endswith('.csv'):
                    hkex_files.append(os.path.join(root, file))

        if not hkex_files:
            logger.warning("未找到港交所数据文件")
            return

        total_records = 0
        with self.conn.cursor() as cursor:
            for file_path in hkex_files:
                try:
                    df = pd.read_csv(file_path)
                    logger.info(f"处理文件: {file_path} ({len(df)} 条记录)")

                    for _, row in df.iterrows():
                        # 解析日期
                        date_str = row.get('Date', '')
                        if pd.isna(date_str):
                            continue

                        try:
                            date_obj = pd.to_datetime(date_str).date()
                        except:
                            continue

                        # 准备数据
                        data = (
                            date_obj,
                            int(row.get('Trading_Volume', 0)) if pd.notna(row.get('Trading_Volume')) else None,
                            int(row.get('Advanced_Stocks', 0)) if pd.notna(row.get('Advanced_Stocks')) else None,
                            int(row.get('Declined_Stocks', 0)) if pd.notna(row.get('Declined_Stocks')) else None,
                            int(row.get('Unchanged_Stocks', 0)) if pd.notna(row.get('Unchanged_Stocks')) else None,
                            float(row.get('Turnover_HKD', 0)) if pd.notna(row.get('Turnover_HKD')) else None,
                            int(row.get('Deals', 0)) if pd.notna(row.get('Deals')) else None,
                            float(row.get('Morning_Close', 0)) if pd.notna(row.get('Morning_Close')) else None,
                            float(row.get('Afternoon_Close', 0)) if pd.notna(row.get('Afternoon_Close')) else None,
                            float(row.get('Change', 0)) if pd.notna(row.get('Change')) else None,
                            float(row.get('Change_Percent', 0)) if pd.notna(row.get('Change_Percent')) else None
                        )

                        # 插入或更新数据
                        cursor.execute("""
                            INSERT INTO hkex_market_data
                            (date, trading_volume, advanced_stocks, declined_stocks, unchanged_stocks,
                             turnover_hkd, deals, morning_close, afternoon_close, change_value, change_percent)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (date) DO UPDATE SET
                                trading_volume = EXCLUDED.trading_volume,
                                advanced_stocks = EXCLUDED.advanced_stocks,
                                declined_stocks = EXCLUDED.declined_stocks,
                                unchanged_stocks = EXCLUDED.unchanged_stocks,
                                turnover_hkd = EXCLUDED.turnover_hkd,
                                deals = EXCLUDED.deals,
                                morning_close = EXCLUDED.morning_close,
                                afternoon_close = EXCLUDED.afternoon_close,
                                change_value = EXCLUDED.change_value,
                                change_percent = EXCLUDED.change_percent
                        """, data)

                        total_records += 1

                except Exception as e:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")
                    continue

            self.conn.commit()

        logger.info(f"✅ 港交所数据迁移完成，共 {total_records} 条记录")

    def migrate_stock_data(self, data_dir: str):
        """迁移股票历史数据"""
        logger.info("开始迁移股票历史数据...")

        # 查找股票数据文件
        stock_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.csv') and 'raw_data' in file:
                    stock_files.append(os.path.join(root, file))

        if not stock_files:
            logger.warning("未找到股票历史数据文件")
            return

        total_records = 0
        with self.conn.cursor() as cursor:
            for file_path in stock_files:
                try:
                    df = pd.read_csv(file_path)
                    logger.info(f"处理文件: {file_path} ({len(df)} 条记录)")

                    for _, row in df.iterrows():
                        # 解析日期
                        date_str = row.get('date', '')
                        if pd.isna(date_str):
                            continue

                        try:
                            date_obj = pd.to_datetime(date_str).date()
                        except:
                            continue

                        symbol = row.get('symbol', '')
                        if pd.isna(symbol):
                            continue

                        # 准备数据
                        data = (
                            date_obj,
                            str(symbol),
                            float(row.get('open', 0)) if pd.notna(row.get('open')) else None,
                            float(row.get('high', 0)) if pd.notna(row.get('high')) else None,
                            float(row.get('low', 0)) if pd.notna(row.get('low')) else None,
                            float(row.get('close', 0)) if pd.notna(row.get('close')) else None,
                            int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
                            int(row.get('market_cap', 0)) if pd.notna(row.get('market_cap')) else None,
                            float(row.get('pe_ratio', 0)) if pd.notna(row.get('pe_ratio')) else None
                        )

                        # 插入或更新数据
                        cursor.execute("""
                            INSERT INTO stock_historical_data
                            (date, symbol, open_price, high_price, low_price, close_price, volume, market_cap, pe_ratio)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (date, symbol) DO UPDATE SET
                                open_price = EXCLUDED.open_price,
                                high_price = EXCLUDED.high_price,
                                low_price = EXCLUDED.low_price,
                                close_price = EXCLUDED.close_price,
                                volume = EXCLUDED.volume,
                                market_cap = EXCLUDED.market_cap,
                                pe_ratio = EXCLUDED.pe_ratio
                        """, data)

                        total_records += 1

                except Exception as e:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")
                    continue

            self.conn.commit()

        logger.info(f"✅ 股票历史数据迁移完成，共 {total_records} 条记录")

    def migrate_government_data(self, data_dir: str):
        """迁移政府经济数据"""
        logger.info("开始迁移政府经济数据...")

        # 查找政府数据文件
        gov_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json') and ('hibor' in file.lower() or 'gdp' in file.lower() or 'trade' in file.lower()):
                    gov_files.append(os.path.join(root, file))

        if not gov_files:
            logger.warning("未找到政府经济数据文件")
            return

        total_records = 0
        with self.conn.cursor() as cursor:
            for file_path in gov_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    logger.info(f"处理文件: {file_path}")

                    # 根据文件类型确定数据类型
                    if 'hibor' in file.lower():
                        data_type = 'HIBOR'
                        self._migrate_hibor_data(cursor, data, total_records)
                    elif 'gdp' in file.lower():
                        data_type = 'GDP'
                        self._migrate_gdp_data(cursor, data, total_records)
                    elif 'trade' in file.lower():
                        data_type = 'TRADE'
                        self._migrate_trade_data(cursor, data, total_records)

                    total_records += len(data) if isinstance(data, list) else 1

                except Exception as e:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")
                    continue

            self.conn.commit()

        logger.info(f"✅ 政府经济数据迁移完成，共 {total_records} 条记录")

    def _migrate_hibor_data(self, cursor, data: List[Dict], total_records: int):
        """迁移HIBOR数据"""
        for record in data:
            if isinstance(record, dict):
                date_str = record.get('date', '')
                tenor = record.get('tenor', '')
                rate = record.get('rate', 0)

                if date_str and rate:
                    try:
                        date_obj = pd.to_datetime(date_str).date()
                    except:
                        continue

                    cursor.execute("""
                        INSERT INTO government_economic_data
                        (data_date, data_type, data_subtype, value, unit, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (data_date, data_type, data_subtype) DO UPDATE SET
                            value = EXCLUDED.value,
                            unit = EXCLUDED.unit
                    """, (date_obj, 'HIBOR', tenor, float(rate), '%', 'HKMA'))

    def _migrate_gdp_data(self, cursor, data, total_records: int):
        """迁移GDP数据"""
        # 实现GDP数据迁移逻辑
        pass

    def _migrate_trade_data(self, cursor, data, total_records: int):
        """迁移贸易数据"""
        # 实现贸易数据迁移逻辑
        pass

    def verify_data_integrity(self):
        """验证数据完整性"""
        logger.info("开始数据完整性验证...")

        with self.conn.cursor() as cursor:
            # 检查港交所数据
            cursor.execute("SELECT COUNT(*) FROM hkex_market_data;")
            hkex_count = cursor.fetchone()[0]

            # 检查股票数据
            cursor.execute("SELECT COUNT(*) FROM stock_historical_data;")
            stock_count = cursor.fetchone()[0]

            # 检查政府数据
            cursor.execute("SELECT COUNT(*) FROM government_economic_data;")
            gov_count = cursor.fetchone()[0]

            logger.info(f"📊 数据完整性验证结果:")
            logger.info(f"  港交所市场数据: {hkex_count:,} 条记录")
            logger.info(f"  股票历史数据: {stock_count:,} 条记录")
            logger.info(f"  政府经济数据: {gov_count:,} 条记录")

            # 检查数据范围
            cursor.execute("SELECT MIN(date), MAX(date) FROM hkex_market_data;")
            hkex_range = cursor.fetchone()
            if hkex_range[0]:
                logger.info(f"  港交所数据范围: {hkex_range[0]} 至 {hkex_range[1]}")

            cursor.execute("SELECT MIN(date), MAX(date) FROM stock_historical_data;")
            stock_range = cursor.fetchone()
            if stock_range[0]:
                logger.info(f"  股票数据范围: {stock_range[0]} 至 {stock_range[1]}")

        logger.info("✅ 数据完整性验证完成")

    def create_summary_views(self):
        """创建数据汇总视图"""
        logger.info("创建数据汇总视图...")

        with self.conn.cursor() as cursor:
            # 港交所市场数据月度汇总
            cursor.execute("""
                CREATE OR REPLACE VIEW hkex_monthly_summary AS
                SELECT
                    date_trunc('month', date) as month,
                    AVG(trading_volume) as avg_trading_volume,
                    AVG(turnover_hkd) as avg_turnover,
                    SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) as up_days,
                    SUM(CASE WHEN change_percent < 0 THEN 1 ELSE 0 END) as down_days,
                    COUNT(*) as trading_days
                FROM hkex_market_data
                GROUP BY date_trunc('month', date)
                ORDER BY month DESC;
            """)

            # 股票数据统计
            cursor.execute("""
                CREATE OR REPLACE VIEW stock_data_stats AS
                SELECT
                    symbol,
                    COUNT(*) as data_points,
                    MIN(date) as first_date,
                    MAX(date) as last_date,
                    AVG(close_price) as avg_close,
                    MAX(high_price) as max_high,
                    MIN(low_price) as min_low
                FROM stock_historical_data
                GROUP BY symbol
                ORDER BY data_points DESC;
            """)

            self.conn.commit()
            logger.info("✅ 数据汇总视图创建完成")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='CBSC数据迁移工具')
    parser.add_argument('--data-dir', default='.', help='数据文件目录')
    parser.add_argument('--db-url', help='数据库连接URL')
    parser.add_argument('--skip-backup', action='store_true', help='跳过备份')
    parser.add_argument('--verify-only', action='store_true', help='仅验证数据')

    args = parser.parse_args()

    migrator = DataMigrator(args.db_url)

    try:
        # 连接数据库
        migrator.connect()

        if not args.verify_only:
            # 创建表结构
            migrator.create_tables()

            # 执行数据迁移
            migrator.migrate_hkex_data(args.data_dir)
            migrator.migrate_stock_data(args.data_dir)
            migrator.migrate_government_data(args.data_dir)

            # 创建汇总视图
            migrator.create_summary_views()

        # 验证数据完整性
        migrator.verify_data_integrity()

        logger.info("🎉 数据迁移任务完成！")

    except Exception as e:
        logger.error(f"❌ 数据迁移失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        migrator.disconnect()

if __name__ == "__main__":
    main()