#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加北向资金数据表
将北向资金数据表添加到现有的quant_system.db中
"""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self, db_path: str = "data/quant_system.db"):
        self.db_path = db_path
        self.migrations = [
            # 北向资金整体流向表
            {
                "version": "001",
                "name": "create_northbound_flow_table",
                "sql": """
                    CREATE TABLE IF NOT EXISTS northbound_flow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_date DATE NOT NULL,
                        market TEXT NOT NULL CHECK (market IN ('SH', 'SZ')),
                        total_turnover REAL NOT NULL DEFAULT 0,
                        net_inflow REAL DEFAULT 0,
                        turnover_change REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(trade_date, market)
                    )
                """
            },
            # 个股北向资金表
            {
                "version": "002",
                "name": "create_stock_northbound_table",
                "sql": """
                    CREATE TABLE IF NOT EXISTS stock_northbound_flow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_date DATE NOT NULL,
                        stock_code TEXT NOT NULL,
                        stock_name TEXT,
                        market TEXT NOT NULL CHECK (market IN ('SH', 'SZ')),
                        buy_volume REAL DEFAULT 0,
                        sell_volume REAL DEFAULT 0,
                        net_volume REAL DEFAULT 0,
                        turnover REAL DEFAULT 0,
                        holding_ratio REAL DEFAULT 0,
                        holding_shares INTEGER DEFAULT 0,
                        market_cap REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(trade_date, stock_code, market)
                    )
                """
            },
            # 北向资金技术指标表
            {
                "version": "003",
                "name": "create_northbound_indicators_table",
                "sql": """
                    CREATE TABLE IF NOT EXISTS northbound_indicators (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_date DATE NOT NULL,
                        market TEXT NOT NULL,
                        turnover_ma5 REAL,
                        turnover_ma20 REAL,
                        turnover_ma60 REAL,
                        net_inflow_ma5 REAL,
                        net_inflow_ma20 REAL,
                        turnover_zscore REAL,
                        net_inflow_momentum REAL,
                        intensity_index REAL,
                        signal_strength INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(trade_date, market)
                    )
                """
            },
            # 港股通持股记录表
            {
                "version": "004",
                "name": "create_hk_stock_connect_table",
                "sql": """
                    CREATE TABLE IF NOT EXISTS hk_stock_connect_holdings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_date DATE NOT NULL,
                        stock_code TEXT NOT NULL,
                        stock_name TEXT,
                        exchange TEXT CHECK (exchange IN ('HKEX')),
                        southbound_holding_ratio REAL DEFAULT 0,
                        southbound_shares INTEGER DEFAULT 0,
                        southbound_turnover REAL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(trade_date, stock_code)
                    )
                """
            },
            # 数据源配置表
            {
                "version": "005",
                "name": "create_data_sources_table",
                "sql": """
                    CREATE TABLE IF NOT EXISTS data_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        type TEXT NOT NULL,
                        base_url TEXT,
                        api_key TEXT,
                        rate_limit INTEGER DEFAULT 1,
                        is_active BOOLEAN DEFAULT 1,
                        last_success_time TIMESTAMP,
                        last_error_time TIMESTAMP,
                        last_error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            },
            # 数据采集任务表
            {
                "version": "006",
                "name": "create_data_collection_jobs_table",
                "sql": """
                    CREATE TABLE IF NOT EXISTS data_collection_jobs (
                        id TEXT PRIMARY KEY,
                        job_type TEXT NOT NULL,
                        source_name TEXT NOT NULL,
                        target_date DATE,
                        status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        records_collected INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_name) REFERENCES data_sources(name)
                    )
                """
            }
        ]

        self.indexes = [
            # 北向资金表索引
            "CREATE INDEX IF NOT EXISTS idx_northbound_flow_date ON northbound_flow(trade_date)",
            "CREATE INDEX IF NOT EXISTS idx_northbound_flow_market ON northbound_flow(market)",
            "CREATE INDEX IF NOT EXISTS idx_northbound_flow_turnover ON northbound_flow(total_turnover)",

            # 个股北向资金表索引
            "CREATE INDEX IF NOT EXISTS idx_stock_northbound_date ON stock_northbound_flow(trade_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_northbound_code ON stock_northbound_flow(stock_code)",
            "CREATE INDEX IF NOT EXISTS idx_stock_northbound_holding ON stock_northbound_flow(holding_ratio)",

            # 指标表索引
            "CREATE INDEX IF NOT EXISTS idx_northbound_indicators_date ON northbound_indicators(trade_date)",
            "CREATE INDEX IF NOT EXISTS idx_northbound_indicators_signal ON northbound_indicators(signal_strength)",

            # 港股通持股表索引
            "CREATE INDEX IF NOT EXISTS idx_hk_connect_date ON hk_stock_connect_holdings(trade_date)",
            "CREATE INDEX IF NOT EXISTS idx_hk_connect_code ON hk_stock_connect_holdings(stock_code)",
            "CREATE INDEX IF NOT EXISTS idx_hk_connect_ratio ON hk_stock_connect_holdings(southbound_holding_ratio)",

            # 任务表索引
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON data_collection_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_date ON data_collection_jobs(target_date)"
        ]

    def run_migrations(self):
        """运行所有迁移"""
        conn = sqlite3.connect(self.db_path)

        try:
            # 创建迁移记录表
            self._create_migration_table(conn)

            # 检查已执行的迁移
            executed_migrations = self._get_executed_migrations(conn)

            # 执行未执行的迁移
            for migration in self.migrations:
                if migration["version"] not in executed_migrations:
                    logger.info(f"执行迁移: {migration['name']}")

                    cursor = conn.cursor()
                    cursor.execute(migration["sql"])

                    # 记录迁移
                    cursor.execute(
                        "INSERT INTO migrations (version, name, executed_at) VALUES (?, ?, ?)",
                        (migration["version"], migration["name"], datetime.now())
                    )

                    conn.commit()
                    logger.info(f"迁移 {migration['name']} 执行成功")

            # 创建索引
            logger.info("创建索引...")
            for index_sql in self.indexes:
                cursor = conn.cursor()
                cursor.execute(index_sql)

            conn.commit()
            logger.info("所有迁移执行完成")

        except Exception as e:
            conn.rollback()
            logger.error(f"迁移失败: {e}")
            raise
        finally:
            conn.close()

    def _create_migration_table(self, conn):
        """创建迁移记录表"""
        sql = """
            CREATE TABLE IF NOT EXISTS migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        conn.execute(sql)

    def _get_executed_migrations(self, conn) -> set:
        """获取已执行的迁移版本"""
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM migrations")
        return {row[0] for row in cursor.fetchall()}

    def rollback_migration(self, version: str):
        """回滚指定版本的迁移"""
        # 注意：回滚需要手动编写回滚SQL
        logger.warning("回滚功能需要手动实现")

    def get_migration_status(self) -> pd.DataFrame:
        """获取迁移状态"""
        conn = sqlite3.connect(self.db_path)

        # 获取所有迁移记录
        df_migrations = pd.read_sql_query(
            "SELECT * FROM migrations ORDER BY executed_at",
            conn
        )

        conn.close()

        return df_migrations

# 初始化数据源配置
def init_data_sources(db_path: str = "data/quant_system.db"):
    """初始化数据源配置"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    data_sources = [
        {
            "name": "HKEX",
            "type": "official",
            "base_url": "https://www.hkex.com.hk",
            "rate_limit": 1,
            "is_active": 1
        },
        {
            "name": "SSE",
            "type": "official",
            "base_url": "http://query.sse.com.cn",
            "rate_limit": 2,
            "is_active": 1
        },
        {
            "name": "SZSE",
            "type": "official",
            "base_url": "http://www.szse.cn",
            "rate_limit": 2,
            "is_active": 1
        },
        {
            "name": "EastMoney",
            "type": "third_party",
            "base_url": "http://push2.eastmoney.com",
            "rate_limit": 1,
            "is_active": 1
        },
        {
            "name": "Tushare",
            "type": "paid",
            "base_url": "http://api.tushare.pro",
            "rate_limit": 60,
            "is_active": 0
        }
    ]

    for source in data_sources:
        cursor.execute("""
            INSERT OR REPLACE INTO data_sources
            (name, type, base_url, rate_limit, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            source["name"],
            source["type"],
            source["base_url"],
            source["rate_limit"],
            source["is_active"]
        ))

    conn.commit()
    conn.close()
    logger.info("数据源配置初始化完成")

# 主执行函数
def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 确保数据目录存在
    os.makedirs(os.path.dirname("data/"), exist_ok=True)

    # 运行迁移
    migration_manager = MigrationManager()
    migration_manager.run_migrations()

    # 初始化数据源
    init_data_sources()

    # 显示迁移状态
    print("\n迁移状态:")
    status_df = migration_manager.get_migration_status()
    print(status_df.to_string(index=False))

    print("\n✅ 数据库迁移完成！")
    print("\n新增表：")
    print("- northbound_flow: 北向资金整体流向")
    print("- stock_northbound_flow: 个股北向资金流向")
    print("- northbound_indicators: 北向资金技术指标")
    print("- hk_stock_connect_holdings: 港股通持股记录")
    print("- data_sources: 数据源配置")
    print("- data_collection_jobs: 数据采集任务")

if __name__ == "__main__":
    main()